"""
Nova Apply - Discovery Module
Portal adapters for job search across multiple platforms.
"""

from discovery.base import (
    BasePortalAdapter,
    JobListing,
    SearchParams,
    JobType,
    ExperienceLevel,
    PortalRegistry,
)

# Import adapters to register them
try:
    from discovery.linkedin import LinkedInAdapter
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"LinkedIn adapter not available: {e}")

__all__ = [
    "BasePortalAdapter",
    "JobListing", 
    "SearchParams",
    "JobType",
    "ExperienceLevel",
    "PortalRegistry",
    "LinkedInAdapter",
]
