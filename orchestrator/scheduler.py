"""
Nova Apply - Orchestrator
Main scheduler and workflow orchestrator.
"""

import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from utils.rate_limiter import RateLimiter, RateLimitConfig
from utils.logger import ApplicationLogger
from utils.profile_manager import ProfileManager
from utils.llm_client import LLMClient
from matcher.semantic_matcher import SemanticMatcher
from tracker.application_tracker import ApplicationTracker
from tracker.reporter import Reporter


class NovaApplyOrchestrator:
    """Main orchestrator for the job application pipeline."""
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize logger first (needed for other components)
        self.logger = ApplicationLogger()
        
        # Initialize components
        self.rate_limiter = self._init_rate_limiter()
        self.profile_manager = ProfileManager(
            self.config.get('paths', {}).get('profiles_dir', './profiles')
        )
        self.tracker = ApplicationTracker(
            self.config.get('paths', {}).get('memory_dir', './memory') + '/applications.db'
        )
        # Load LLM client if API keys available
        self.llm_client = self._init_llm_client()
        self.matcher = SemanticMatcher(llm_client=self.llm_client)
        self.reporter = Reporter(self.tracker)
        
        # Portal adapters (loaded on demand)
        self._adapters = {}
        
        self.logger.info("🚀 Nova Apply Orchestrator initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _init_rate_limiter(self) -> RateLimiter:
        """Initialize rate limiter from config."""
        rl_config = self.config.get('rate_limits', {})
        config = RateLimitConfig(
            api_call_delay=rl_config.get('api_call_delay_seconds', 5),
            portal_action_delay=rl_config.get('portal_action_delay_seconds', 10),
            max_searches_per_batch=rl_config.get('max_searches_per_batch', 5),
            search_batch_break=rl_config.get('search_batch_break_seconds', 120),
            max_apps_per_profile_per_day=rl_config.get('max_applications_per_profile_per_day', 30)
        )
        return RateLimiter(config)

    def _init_llm_client(self) -> Optional[LLMClient]:
        """Initialize LLM client if API keys available."""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            llm_config = self.config.get('llm', {})
            client = LLMClient(llm_config)
            
            # Check if any clients initialized
            if client._clients:
                self.logger.info(f"LLM client ready: {list(client._clients.keys())}")
                return client
            else:
                self.logger.warning("No LLM API keys configured, using fallback matching")
                return None
        except Exception as e:
            self.logger.warning(f"Failed to init LLM client: {e}")
            return None
    
    def get_enabled_portals(self) -> List[str]:
        """Get list of enabled portals."""
        portals = self.config.get('portals', {})
        return [name for name, config in portals.items() if config.get('enabled', False)]
    
    def run_for_profile(self, profile_id: str, max_applications: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the full pipeline for a single profile.
        
        Returns stats about the run.
        """
        logger = ApplicationLogger(profile_id)
        logger.info(f"Starting run for profile: {profile_id}")
        
        # Load profile
        profile = self.profile_manager.load_profile(profile_id)
        if not profile:
            logger.error(f"Profile not found: {profile_id}")
            return {"error": "Profile not found", "applications_sent": 0}
        
        # Check daily limit
        if not self.rate_limiter.can_apply_today(profile_id):
            remaining = self.rate_limiter.get_remaining_applications(profile_id)
            logger.info(f"Daily limit reached. Remaining: {remaining}")
            return {"status": "limit_reached", "applications_sent": 0}
        
        # Determine how many to apply
        if max_applications is None:
            max_applications = profile.application_settings.daily_limit
        
        remaining = self.rate_limiter.get_remaining_applications(profile_id)
        target = min(max_applications, remaining)
        
        logger.info(f"Target applications: {target}")
        
        # TODO: Implement full pipeline
        # 1. Search jobs on enabled portals
        # 2. Match jobs to profile
        # 3. Apply to high/medium matches
        # 4. Track applications
        
        # Placeholder return
        return {
            "profile_id": profile_id,
            "target_applications": target,
            "applications_sent": 0,
            "matches_found": 0,
            "errors": []
        }
    
    def run_daily(self) -> Dict[str, Any]:
        """Run the full daily pipeline for all active profiles."""
        self.logger.info("🚀 Starting daily run")
        
        # Load active profiles
        profiles_config = Path("config/profiles.json")
        if profiles_config.exists():
            with open(profiles_config, 'r') as f:
                data = json.load(f)
                active_profiles = data.get('active_profiles', [])
        else:
            active_profiles = self.profile_manager.list_profiles()
        
        results = {
            "start_time": datetime.now().isoformat(),
            "profiles_processed": 0,
            "total_applications": 0,
            "errors": []
        }
        
        for profile_id in active_profiles:
            try:
                result = self.run_for_profile(profile_id)
                results["profiles_processed"] += 1
                results["total_applications"] += result.get("applications_sent", 0)
            except Exception as e:
                error_msg = f"Error processing {profile_id}: {str(e)}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
            
            # Rate limit between profiles
            self.rate_limiter.human_like_delay(5, 15)
        
        results["end_time"] = datetime.now().isoformat()
        
        self.logger.info(f"Daily run complete. Total applications: {results['total_applications']}")
        
        return results
    
    def send_daily_report(self) -> bool:
        """Generate and send daily report."""
        report = self.reporter.generate_daily_report()
        return self.reporter.send_whatsapp_report(report)
    
    def check_confirmations(self) -> List[Dict[str, Any]]:
        """Check Gmail for application confirmations."""
        # TODO: Implement Gmail monitoring
        self.logger.info("Checking for confirmation emails...")
        return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "config_loaded": True,
            "enabled_portals": self.get_enabled_portals(),
            "profiles": self.profile_manager.list_profiles(),
            "rate_limiter_ready": True,
            "tracker_ready": True
        }


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nova Apply - Automated Job Application System")
    parser.add_argument("command", choices=["daily", "profile", "status", "report"],
                       help="Command to run")
    parser.add_argument("--profile", "-p", help="Profile ID for single profile run")
    parser.add_argument("--max", "-m", type=int, help="Max applications to send")
    
    args = parser.parse_args()
    
    orchestrator = NovaApplyOrchestrator()
    
    if args.command == "daily":
        results = orchestrator.run_daily()
        print(json.dumps(results, indent=2))
    
    elif args.command == "profile":
        if not args.profile:
            print("Error: --profile required for profile command")
            return
        results = orchestrator.run_for_profile(args.profile, args.max)
        print(json.dumps(results, indent=2))
    
    elif args.command == "status":
        status = orchestrator.get_status()
        print(json.dumps(status, indent=2))
    
    elif args.command == "report":
        orchestrator.send_daily_report()


if __name__ == "__main__":
    main()
