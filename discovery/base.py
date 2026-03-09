"""
Nova Apply - Base Portal Adapter
Abstract base class for all job portal adapters.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class JobType(Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    REMOTE = "remote"


class ExperienceLevel(Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    EXECUTIVE = "executive"


@dataclass
class JobListing:
    """Standardized job listing across all portals."""
    job_id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    posted_date: Optional[datetime] = None
    salary_range: Optional[str] = None
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    remote_allowed: bool = False
    easy_apply: bool = False
    application_url: Optional[str] = None
    requirements: List[str] = None
    source_portal: str = ""
    raw_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = []
        if self.raw_data is None:
            self.raw_data = {}


@dataclass
class SearchParams:
    """Parameters for job search."""
    keywords: List[str]
    location: str = "United States"
    date_filter: str = "past_24_hours"  # past_24_hours, past_week, past_month
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    remote_only: bool = False
    radius_miles: int = 50
    page: int = 1


class BasePortalAdapter(ABC):
    """Abstract base class for job portal adapters."""
    
    PORTAL_NAME: str = "base"
    BASE_URL: str = ""
    REQUIRES_LOGIN: bool = False
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', False)
        self.session = None
        self.authenticated = False
    
    @abstractmethod
    def search_jobs(self, params: SearchParams) -> List[JobListing]:
        """Search for jobs on this portal."""
        pass
    
    @abstractmethod
    def get_job_details(self, job_id: str) -> Optional[JobListing]:
        """Get full details for a specific job."""
        pass
    
    @abstractmethod
    def apply_to_job(self, job: JobListing, profile_data: Dict[str, Any]) -> bool:
        """Apply to a job. Returns True if successful."""
        pass
    
    def login(self, credentials: Dict[str, str]) -> bool:
        """Login to the portal if required."""
        if not self.REQUIRES_LOGIN:
            return True
        # Override in subclasses that require login
        return False
    
    def is_ready(self) -> bool:
        """Check if portal is ready for use."""
        return self.enabled and (not self.REQUIRES_LOGIN or self.authenticated)
    
    def normalize_job_data(self, raw_job: Dict[str, Any]) -> JobListing:
        """Normalize portal-specific job data to standard format."""
        # Override in subclasses
        raise NotImplementedError
    
    def get_rate_limit_delay(self) -> float:
        """Get recommended delay between requests for this portal."""
        return 10.0  # Default 10 seconds
    
    def get_search_url(self, params: SearchParams) -> str:
        """Build search URL for this portal."""
        # Override in subclasses
        return self.BASE_URL
    
    def __str__(self) -> str:
        return f"{self.PORTAL_NAME}Adapter(enabled={self.enabled})"
    
    def __repr__(self) -> str:
        return self.__str__()


class PortalRegistry:
    """Registry for portal adapters."""
    
    _adapters: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, adapter_class: type):
        """Register a portal adapter."""
        cls._adapters[name] = adapter_class
    
    @classmethod
    def get_adapter(cls, name: str, config: Dict[str, Any]) -> Optional[BasePortalAdapter]:
        """Get an instance of a registered adapter."""
        adapter_class = cls._adapters.get(name)
        if adapter_class:
            return adapter_class(config)
        return None
    
    @classmethod
    def list_adapters(cls) -> List[str]:
        """List all registered adapter names."""
        return list(cls._adapters.keys())
