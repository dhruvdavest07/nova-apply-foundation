"""
Nova Apply - Semantic Matcher
LLM-powered job-to-candidate matching using Kimi API.
"""

import json
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class MatchLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class MatchResult:
    """Result of job-candidate matching."""
    score: float  # 0.0 to 1.0
    level: MatchLevel
    reasoning: str
    skill_matches: list
    skill_gaps: list
    experience_relevance: float
    confidence: float
    should_apply: bool


class SemanticMatcher:
    """LLM-based semantic matching of jobs to candidates."""
    
    MATCHING_PROMPT = """You are an expert career advisor evaluating job fit.

CANDIDATE PROFILE:
Name: {candidate_name}
Target Roles: {target_roles}
Skills: {skills}
Experience Summary: {experience_summary}
Preferred Location: {preferred_location}

JOB POSTING:
Title: {job_title}
Company: {company}
Location: {job_location}
Description: {job_description}
Requirements: {requirements}

Evaluate this match carefully:

1. SKILL ALIGNMENT: Which required skills does the candidate have? Which are missing?
2. EXPERIENCE FIT: Does their experience level match the role requirements?
3. ROLE RELEVANCE: Is this job aligned with their target career path?
4. LOCATION/COMPENSATION: Any obvious deal-breakers?

Respond ONLY with a JSON object in this exact format:
{{
    "score": 0.0-1.0,
    "level": "high" | "medium" | "low",
    "reasoning": "Brief explanation of the match quality",
    "skill_matches": ["skill1", "skill2"],
    "skill_gaps": ["missing1"],
    "experience_relevance": 0.0-1.0,
    "confidence": 0.0-1.0,
    "should_apply": true/false
}}

Scoring guidelines:
- HIGH (0.8-1.0): Strong skill match, relevant experience, aligned with career goals
- MEDIUM (0.6-0.79): Good fit with some gaps, worth applying
- LOW (0.0-0.59): Significant mismatches, not worth the application
"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.min_match_score = 0.6
        self.high_threshold = 0.8
        self.medium_threshold = 0.6
    
    def match(self, job: Dict[str, Any], profile: Dict[str, Any]) -> MatchResult:
        """
        Match a job to a candidate profile.
        
        Returns MatchResult with score and recommendation.
        """
        # Build the prompt
        prompt = self._build_prompt(job, profile)
        
        # Get LLM response
        if self.llm_client:
            response = self._call_llm(prompt)
        else:
            # Fallback to simple keyword matching if no LLM
            response = self._fallback_match(job, profile)
        
        # Parse and validate result
        return self._parse_result(response)
    
    def _build_prompt(self, job: Dict[str, Any], profile: Dict[str, Any]) -> str:
        """Build the matching prompt."""
        candidate = profile.get('candidate', {})
        resume = profile.get('resume', {})
        prefs = profile.get('preferences', {})
        
        skills = resume.get('skills', {})
        all_skills = (
            skills.get('technical', []) + 
            skills.get('soft', []) + 
            skills.get('tools', [])
        )
        
        experience = resume.get('experience', [])
        exp_summary = ""
        if experience:
            latest = experience[0]
            exp_summary = f"{latest.get('title', '')} at {latest.get('company', '')}"
        
        return self.MATCHING_PROMPT.format(
            candidate_name=f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip(),
            target_roles=", ".join(prefs.get('target_roles', [])),
            skills=", ".join(all_skills),
            experience_summary=exp_summary,
            preferred_location=candidate.get('location', {}).get('preferred_locations', ['Anywhere']),
            job_title=job.get('title', ''),
            company=job.get('company', ''),
            job_location=job.get('location', ''),
            job_description=job.get('description', '')[:2000],  # Limit length
            requirements=", ".join(job.get('requirements', []))
        )
    
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Call the LLM with the matching prompt."""
        # This will integrate with your Kimi API
        # For now, return a placeholder
        return {
            "score": 0.75,
            "level": "medium",
            "reasoning": "Placeholder - implement LLM call",
            "skill_matches": [],
            "skill_gaps": [],
            "experience_relevance": 0.7,
            "confidence": 0.8,
            "should_apply": True
        }
    
    def _fallback_match(self, job: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Simple keyword-based fallback matching."""
        # Extract skills and keywords
        resume = profile.get('resume', {})
        skills = resume.get('skills', {})
        candidate_skills = set(
            s.lower() for s in (
                skills.get('technical', []) + 
                skills.get('tools', [])
            )
        )
        
        job_desc = job.get('description', '').lower()
        job_title = job.get('title', '').lower()
        
        # Count skill matches
        matches = []
        for skill in candidate_skills:
            if skill in job_desc or skill in job_title:
                matches.append(skill)
        
        # Simple score calculation
        if candidate_skills:
            score = len(matches) / len(candidate_skills)
        else:
            score = 0.0
        
        # Determine level
        if score >= 0.7:
            level = "high"
        elif score >= 0.4:
            level = "medium"
        else:
            level = "low"
        
        return {
            "score": min(score * 1.5, 1.0),  # Scale up a bit
            "level": level,
            "reasoning": f"Keyword matching: {len(matches)} skills found in job",
            "skill_matches": matches,
            "skill_gaps": list(candidate_skills - set(matches)),
            "experience_relevance": 0.5,
            "confidence": 0.5,
            "should_apply": score >= 0.4
        }
    
    def _parse_result(self, response: Dict[str, Any]) -> MatchResult:
        """Parse LLM response into MatchResult."""
        score = float(response.get('score', 0))
        level_str = response.get('level', 'low')
        
        # Validate level
        try:
            level = MatchLevel(level_str)
        except ValueError:
            level = MatchLevel.LOW
        
        return MatchResult(
            score=score,
            level=level,
            reasoning=response.get('reasoning', ''),
            skill_matches=response.get('skill_matches', []),
            skill_gaps=response.get('skill_gaps', []),
            experience_relevance=float(response.get('experience_relevance', 0)),
            confidence=float(response.get('confidence', 0)),
            should_apply=response.get('should_apply', False) and score >= self.min_match_score
        )
    
    def batch_match(self, jobs: list, profile: Dict[str, Any]) -> list:
        """Match multiple jobs to a profile."""
        results = []
        for job in jobs:
            result = self.match(job, profile)
            results.append((job, result))
        return results
