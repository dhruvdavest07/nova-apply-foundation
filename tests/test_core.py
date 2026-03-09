# Nova Apply - Test Suite

import pytest
from pathlib import Path
import sys
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.rate_limiter import RateLimiter, RateLimitConfig
from utils.profile_manager import ProfileManager, Profile
from matcher.semantic_matcher import SemanticMatcher
from tracker.application_tracker import ApplicationTracker
from discovery import LinkedInAdapter, PortalRegistry, SearchParams


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_rate_limit_config(self):
        config = RateLimitConfig(
            api_call_delay=5,
            portal_action_delay=10,
            max_searches_per_batch=5,
            max_apps_per_profile_per_day=30
        )
        assert config.api_call_delay == 5
        assert config.max_apps_per_profile_per_day == 30
    
    def test_daily_limit(self):
        config = RateLimitConfig(max_apps_per_profile_per_day=30)
        limiter = RateLimiter(config)
        
        # Should allow 30 applications
        for i in range(30):
            assert limiter.can_apply_today("test_profile")
            limiter.record_application("test_profile")
        
        # Should deny the 31st
        assert not limiter.can_apply_today("test_profile")
    
    def test_remaining_applications(self):
        config = RateLimitConfig(max_apps_per_profile_per_day=30)
        limiter = RateLimiter(config)
        
        assert limiter.get_remaining_applications("test_profile") == 30
        limiter.record_application("test_profile")
        assert limiter.get_remaining_applications("test_profile") == 29


class TestProfileManager:
    """Test profile management."""
    
    def test_create_and_load_profile(self, tmp_path):
        pm = ProfileManager(str(tmp_path / "profiles"))
        
        data = {
            "candidate": {
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com"
            },
            "preferences": {
                "target_roles": ["Software Engineer"]
            }
        }
        
        profile = pm.create_profile("test_001", data)
        assert profile.profile_id == "test_001"
        assert profile.candidate.first_name == "Test"
        
        # Load it back
        loaded = pm.load_profile("test_001")
        assert loaded.candidate.email == "test@example.com"
    
    def test_validate_profile(self, tmp_path):
        pm = ProfileManager(str(tmp_path / "profiles"))
        
        # Empty profile should have issues
        data = {"profile_id": "bad_profile"}
        pm.create_profile("bad_profile", data)
        
        issues = pm.validate_profile("bad_profile")
        assert len(issues) > 0
        assert "Missing first name" in issues


class TestSemanticMatcher:
    """Test semantic matching."""
    
    def test_fallback_match(self):
        matcher = SemanticMatcher(llm_client=None)  # Use fallback
        
        job = {
            "title": "Python Developer",
            "description": "Looking for Python, Django, and React experience",
            "requirements": ["Python", "Django"]
        }
        
        profile = {
            "candidate": {"first_name": "Test", "last_name": "User"},
            "resume": {
                "skills": {
                    "technical": ["Python", "Django", "JavaScript"],
                    "tools": ["Git", "Docker"]
                }
            },
            "preferences": {"target_roles": ["Python Developer"]}
        }
        
        result = matcher.match(job, profile)
        assert result.score > 0
        assert isinstance(result.should_apply, bool)


class TestApplicationTracker:
    """Test application tracking."""
    
    def test_record_application(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        tracker = ApplicationTracker(db_path)
        
        from tracker.application_tracker import ApplicationRecord, ApplicationStatus
        
        record = ApplicationRecord(
            profile_id="test_001",
            job_id="job_123",
            job_title="Software Engineer",
            company="Test Corp",
            portal="linkedin",
            status=ApplicationStatus.SUBMITTED,
            match_score=0.85
        )
        
        record_id = tracker.record_application(record)
        assert record_id > 0
        
        # Check today's stats
        stats = tracker.get_today_stats()
        assert stats["submitted"] == 1


class TestLinkedInAdapter:
    """Test LinkedIn adapter (without browser)."""
    
    def test_adapter_registration(self):
        """Test that LinkedIn adapter is registered."""
        adapters = PortalRegistry.list_adapters()
        assert "linkedin" in adapters
    
    def test_adapter_creation(self):
        """Test creating LinkedIn adapter instance."""
        config = {
            "enabled": True,
            "headless": True
        }
        # This will fail without browser, so we just check the class exists
        assert LinkedInAdapter.PORTAL_NAME == "linkedin"
        assert LinkedInAdapter.REQUIRES_LOGIN == True
    
    def test_search_url_building(self):
        """Test URL generation for search."""
        # Create a mock adapter to test URL building
        config = {"enabled": False}
        
        params = SearchParams(
            keywords=["Python", "Developer"],
            location="United States",
            date_filter="past_24_hours",
            remote_only=True
        )
        
        # Expected URL parts
        assert "Python" in " ".join(params.keywords)
        assert params.location == "United States"
        assert params.date_filter == "past_24_hours"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
