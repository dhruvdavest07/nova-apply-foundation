"""
Nova Apply - Profile Manager
Handles loading, validating, and managing candidate profiles.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Location:
    city: str = ""
    state: str = ""
    country: str = "United States"
    willing_to_relocate: bool = True
    preferred_locations: List[str] = None
    
    def __post_init__(self):
        if self.preferred_locations is None:
            self.preferred_locations = ["Remote", "Anywhere USA"]


@dataclass
class Candidate:
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    location: Location = None
    linkedin_url: str = ""
    portfolio_url: str = ""
    github_url: str = ""
    
    def __post_init__(self):
        if self.location is None:
            self.location = Location()
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class Skills:
    technical: List[str] = None
    soft: List[str] = None
    tools: List[str] = None
    languages: List[str] = None
    
    def __post_init__(self):
        if self.technical is None:
            self.technical = []
        if self.soft is None:
            self.soft = []
        if self.tools is None:
            self.tools = []
        if self.languages is None:
            self.languages = []
    
    def all_skills(self) -> List[str]:
        return self.technical + self.soft + self.tools + self.languages


@dataclass
class Experience:
    title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    current: bool = False
    description: str = ""
    achievements: List[str] = None
    
    def __post_init__(self):
        if self.achievements is None:
            self.achievements = []


@dataclass
class Education:
    degree: str = ""
    field: str = ""
    institution: str = ""
    graduation_year: int = 0


@dataclass
class Resume:
    file_path: str = ""
    summary: str = ""
    skills: Skills = None
    experience: List[Experience] = None
    education: List[Education] = None
    certifications: List[str] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = Skills()
        if self.experience is None:
            self.experience = []
        if self.education is None:
            self.education = []
        if self.certifications is None:
            self.certifications = []


@dataclass
class SalaryRange:
    min: int = 0
    max: int = 0
    currency: str = "USD"


@dataclass
class Preferences:
    target_roles: List[str] = None
    target_industries: List[str] = None
    avoid_industries: List[str] = None
    job_types: List[str] = None
    remote_preference: str = "remote-first"
    salary_range: SalaryRange = None
    visa_status: str = "No visa sponsorship required - willing to relocate anywhere USA"
    notice_period_days: int = 30
    available_start: str = "immediately"
    
    def __post_init__(self):
        if self.target_roles is None:
            self.target_roles = []
        if self.target_industries is None:
            self.target_industries = []
        if self.avoid_industries is None:
            self.avoid_industries = []
        if self.job_types is None:
            self.job_types = ["full-time", "contract"]
        if self.salary_range is None:
            self.salary_range = SalaryRange()


@dataclass
class ApplicationSettings:
    daily_limit: int = 30
    cover_letter_style: str = "professional-concise"
    auto_apply_enabled: bool = True
    manual_review_threshold: float = 0.7


@dataclass
class Profile:
    profile_id: str = ""
    candidate: Candidate = None
    resume: Resume = None
    preferences: Preferences = None
    application_settings: ApplicationSettings = None
    created_at: str = ""
    updated_at: str = ""
    notes: str = ""
    
    def __post_init__(self):
        if self.candidate is None:
            self.candidate = Candidate()
        if self.resume is None:
            self.resume = Resume()
        if self.preferences is None:
            self.preferences = Preferences()
        if self.application_settings is None:
            self.application_settings = ApplicationSettings()
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        # Manual conversion for nested dataclasses
        candidate_data = data.get('candidate', {})
        candidate_data['location'] = Location(**candidate_data.get('location', {}))
        candidate = Candidate(**candidate_data)
        
        resume_data = data.get('resume', {})
        resume_data['skills'] = Skills(**resume_data.get('skills', {}))
        resume_data['experience'] = [Experience(**e) for e in resume_data.get('experience', [])]
        resume_data['education'] = [Education(**e) for e in resume_data.get('education', [])]
        resume = Resume(**resume_data)
        
        prefs_data = data.get('preferences', {})
        prefs_data['salary_range'] = SalaryRange(**prefs_data.get('salary_range', {}))
        preferences = Preferences(**prefs_data)
        
        app_settings = ApplicationSettings(**data.get('application_settings', {}))
        
        return cls(
            profile_id=data.get('profile_id', ''),
            candidate=candidate,
            resume=resume,
            preferences=preferences,
            application_settings=app_settings,
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            notes=data.get('notes', '')
        )


class ProfileManager:
    """Manages candidate profiles."""
    
    def __init__(self, profiles_dir: str = "./profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
        self._profiles: Dict[str, Profile] = {}
    
    def load_profile(self, profile_id: str) -> Optional[Profile]:
        """Load a profile from JSON file."""
        if profile_id in self._profiles:
            return self._profiles[profile_id]
        
        profile_path = self.profiles_dir / f"{profile_id}.json"
        if not profile_path.exists():
            return None
        
        with open(profile_path, 'r') as f:
            data = json.load(f)
        
        profile = Profile.from_dict(data)
        self._profiles[profile_id] = profile
        return profile
    
    def save_profile(self, profile: Profile) -> None:
        """Save a profile to JSON file."""
        profile.updated_at = datetime.now().isoformat()
        profile_path = self.profiles_dir / f"{profile.profile_id}.json"
        
        with open(profile_path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
        
        self._profiles[profile.profile_id] = profile
    
    def list_profiles(self) -> List[str]:
        """List all profile IDs."""
        profiles = []
        for f in self.profiles_dir.glob("*.json"):
            if f.stem != "template_profile":
                profiles.append(f.stem)
        return sorted(profiles)
    
    def create_profile(self, profile_id: str, data: Dict[str, Any]) -> Profile:
        """Create a new profile."""
        data['profile_id'] = profile_id
        profile = Profile.from_dict(data)
        self.save_profile(profile)
        return profile
    
    def get_profile_summary(self, profile_id: str) -> Dict[str, Any]:
        """Get a summary of a profile."""
        profile = self.load_profile(profile_id)
        if not profile:
            return {}
        
        return {
            "profile_id": profile.profile_id,
            "name": profile.candidate.full_name,
            "email": profile.candidate.email,
            "target_roles": profile.preferences.target_roles,
            "skills_count": len(profile.resume.skills.all_skills()),
            "experience_years": len(profile.resume.experience),
            "daily_limit": profile.application_settings.daily_limit,
            "auto_apply": profile.application_settings.auto_apply_enabled
        }
    
    def validate_profile(self, profile_id: str) -> List[str]:
        """Validate a profile and return list of issues."""
        profile = self.load_profile(profile_id)
        if not profile:
            return ["Profile not found"]
        
        issues = []
        
        if not profile.candidate.first_name:
            issues.append("Missing first name")
        if not profile.candidate.last_name:
            issues.append("Missing last name")
        if not profile.candidate.email:
            issues.append("Missing email")
        if not profile.preferences.target_roles:
            issues.append("No target roles specified")
        if not profile.resume.skills.all_skills():
            issues.append("No skills listed")
        
        return issues
