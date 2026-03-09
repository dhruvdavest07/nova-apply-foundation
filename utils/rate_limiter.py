"""
Nova Apply - Rate Limiter
Enforces rate limits to avoid bans and respect API quotas.
"""

import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class RateLimitConfig:
    api_call_delay: int = 5
    portal_action_delay: int = 10
    max_searches_per_batch: int = 5
    search_batch_break: int = 120
    max_apps_per_profile_per_day: int = 30


class RateLimiter:
    """Central rate limiter for all Nova Apply operations."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.last_api_call: Optional[datetime] = None
        self.last_portal_action: Optional[datetime] = None
        self.search_count_this_batch: int = 0
        self.batch_start_time: Optional[datetime] = None
        self.profile_daily_counts: Dict[str, int] = {}
        self.profile_last_reset: Dict[str, datetime] = {}
    
    def wait_for_api_call(self) -> None:
        """Wait appropriate time before making an API call."""
        if self.last_api_call:
            elapsed = (datetime.now() - self.last_api_call).total_seconds()
            if elapsed < self.config.api_call_delay:
                sleep_time = self.config.api_call_delay - elapsed
                # Add small randomization (±10%) for human-like behavior
                sleep_time *= random.uniform(0.9, 1.1)
                time.sleep(max(0, sleep_time))
        self.last_api_call = datetime.now()
    
    def wait_for_portal_action(self) -> None:
        """Wait appropriate time before a portal interaction."""
        if self.last_portal_action:
            elapsed = (datetime.now() - self.last_portal_action).total_seconds()
            if elapsed < self.config.portal_action_delay:
                sleep_time = self.config.portal_action_delay - elapsed
                sleep_time *= random.uniform(0.9, 1.1)
                time.sleep(max(0, sleep_time))
        self.last_portal_action = datetime.now()
    
    def check_search_batch(self) -> None:
        """Check if we need a break between search batches."""
        if self.batch_start_time is None:
            self.batch_start_time = datetime.now()
            self.search_count_this_batch = 0
            return
        
        self.search_count_this_batch += 1
        
        if self.search_count_this_batch >= self.config.max_searches_per_batch:
            # Take a break
            print(f"[RateLimiter] Batch limit reached. Breaking for {self.config.search_batch_break}s...")
            time.sleep(self.config.search_batch_break)
            self.search_count_this_batch = 0
            self.batch_start_time = datetime.now()
    
    def can_apply_today(self, profile_id: str) -> bool:
        """Check if profile has remaining applications for today."""
        today = datetime.now().date()
        
        # Reset counter if it's a new day
        if profile_id in self.profile_last_reset:
            if self.profile_last_reset[profile_id].date() < today:
                self.profile_daily_counts[profile_id] = 0
                self.profile_last_reset[profile_id] = datetime.now()
        else:
            self.profile_daily_counts[profile_id] = 0
            self.profile_last_reset[profile_id] = datetime.now()
        
        current_count = self.profile_daily_counts.get(profile_id, 0)
        return current_count < self.config.max_apps_per_profile_per_day
    
    def record_application(self, profile_id: str) -> None:
        """Record a successful application for rate tracking."""
        if profile_id not in self.profile_daily_counts:
            self.profile_daily_counts[profile_id] = 0
        self.profile_daily_counts[profile_id] += 1
    
    def get_remaining_applications(self, profile_id: str) -> int:
        """Get remaining applications for profile today."""
        if not self.can_apply_today(profile_id):
            return 0
        current = self.profile_daily_counts.get(profile_id, 0)
        return self.config.max_apps_per_profile_per_day - current
    
    def human_like_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
        """Random delay to simulate human behavior."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def typing_delay(self, text_length: int) -> None:
        """Simulate typing time based on text length."""
        # Average typing speed: ~200-300 chars/min = ~3-5 chars/sec
        chars_per_second = random.uniform(3, 6)
        delay = text_length / chars_per_second
        # Add some variance
        delay *= random.uniform(0.8, 1.2)
        time.sleep(delay)


def load_rate_limiter_from_config(config_path: str = "config/settings.json") -> RateLimiter:
    """Load rate limiter from settings file."""
    with open(config_path, 'r') as f:
        settings = json.load(f)
    
    rl_config = settings.get('rate_limits', {})
    config = RateLimitConfig(
        api_call_delay=rl_config.get('api_call_delay_seconds', 5),
        portal_action_delay=rl_config.get('portal_action_delay_seconds', 10),
        max_searches_per_batch=rl_config.get('max_searches_per_batch', 5),
        search_batch_break=rl_config.get('search_batch_break_seconds', 120),
        max_apps_per_profile_per_day=rl_config.get('max_applications_per_profile_per_day', 30)
    )
    
    return RateLimiter(config)
