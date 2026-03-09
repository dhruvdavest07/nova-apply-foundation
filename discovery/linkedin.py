"""
Nova Apply - LinkedIn Portal Adapter
Job search and application automation for LinkedIn.
"""

import time
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from discovery.base import (
    BasePortalAdapter, JobListing, SearchParams, JobType, 
    ExperienceLevel, PortalRegistry
)
from utils.rate_limiter import RateLimiter
from utils.logger import ApplicationLogger


class LinkedInAdapter(BasePortalAdapter):
    """LinkedIn job portal adapter with stealth automation."""
    
    PORTAL_NAME = "linkedin"
    BASE_URL = "https://www.linkedin.com"
    REQUIRES_LOGIN = True
    
    # LinkedIn-specific selectors (can change, need maintenance)
    SELECTORS = {
        # Auth
        "login_email": "input#username",
        "login_password": "input#password",
        "login_button": "button[type='submit']",
        
        # Search results
        "job_cards": "div.job-card-container",
        "job_title": "a.job-card-list__title",
        "job_company": "a.job-card-container__company-name",
        "job_location": "span.job-card-container__metadata-item",
        "job_link": "a.job-card-list__title",
        
        # Job details
        "job_description": "div.jobs-description",
        "show_more": "button.jobs-description__footer-button",
        "apply_button": "button.jobs-apply-button",
        
        # Easy Apply flow
        "easy_apply_button": "button[aria-label*='Easy Apply']",
        "next_button": "button[aria-label='Continue to next step']",
        "review_button": "button[aria-label='Review your application']",
        "submit_button": "button[aria-label='Submit application']",
        "done_button": "button[aria-label='Dismiss']",
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = ApplicationLogger("linkedin")
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._init_browser()
    
    def _init_browser(self):
        """Initialize stealth browser."""
        try:
            self.playwright = sync_playwright().start()
            
            # Stealth browser context
            self.browser = self.playwright.chromium.launch(
                headless=self.config.get('headless', True),
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            
            # Context with realistic viewport and locale
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                color_scheme='light',
            )
            
            # Add stealth scripts
            self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                window.chrome = { runtime: {} };
            """)
            
            self.page = self.context.new_page()
            self.logger.info("Browser initialized in stealth mode")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            raise
    
    def login(self, credentials: Dict[str, str]) -> bool:
        """Login to LinkedIn with email/password."""
        try:
            email = credentials.get('email') or credentials.get('LINKEDIN_EMAIL')
            password = credentials.get('password') or credentials.get('LINKEDIN_PASSWORD')
            
            if not email or not password:
                # Try cookie-based auth
                return self._login_with_cookies(credentials)
            
            self.logger.info("Logging in to LinkedIn...")
            self.page.goto(f"{self.BASE_URL}/login")
            
            # Wait for login form
            self.page.wait_for_selector(self.SELECTORS["login_email"], timeout=10000)
            
            # Fill credentials with human-like delays
            self._human_type(self.SELECTORS["login_email"], email)
            time.sleep(0.5)
            self._human_type(self.SELECTORS["login_password"], password)
            time.sleep(0.3)
            
            # Click login
            self.page.click(self.SELECTORS["login_button"])
            
            # Wait for navigation (feed or checkpoint)
            self.page.wait_for_load_state('networkidle', timeout=15000)
            
            # Check if logged in
            if 'feed' in self.page.url or 'checkpoint' not in self.page.url:
                self.authenticated = True
                self.logger.info("Successfully logged in")
                
                # Save cookies for future sessions
                self._save_cookies()
                return True
            else:
                self.logger.error("Login failed - checkpoint or captcha")
                return False
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False
    
    def _login_with_cookies(self, credentials: Dict[str, str]) -> bool:
        """Try cookie-based authentication."""
        try:
            cookie_path = credentials.get('cookie_path', 'config/linkedin_cookies.json')
            
            with open(cookie_path, 'r') as f:
                cookies = json.load(f)
            
            self.context.add_cookies(cookies)
            self.page.goto(f"{self.BASE_URL}/feed")
            
            # Check if authenticated
            if 'login' not in self.page.url:
                self.authenticated = True
                self.logger.info("Logged in with cookies")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Cookie login failed: {e}")
            return False
    
    def _save_cookies(self):
        """Save cookies for future sessions."""
        try:
            cookies = self.context.cookies()
            with open('config/linkedin_cookies.json', 'w') as f:
                json.dump(cookies, f)
        except Exception as e:
            self.logger.warning(f"Failed to save cookies: {e}")
    
    def _human_type(self, selector: str, text: str):
        """Type text with human-like delays."""
        for char in text:
            self.page.type(selector, char, delay=50)
            time.sleep(0.01)
    
    def search_jobs(self, params: SearchParams) -> List[JobListing]:
        """Search for jobs on LinkedIn."""
        if not self.is_ready():
            self.logger.error("Adapter not ready - not logged in")
            return []
        
        jobs = []
        
        try:
            # Build search URL
            search_url = self._build_search_url(params)
            self.logger.info(f"Searching: {search_url}")
            
            self.page.goto(search_url)
            self.page.wait_for_load_state('networkidle')
            
            # Wait for job cards
            self.page.wait_for_selector(self.SELECTORS["job_cards"], timeout=10000)
            
            # Extract job listings
            job_cards = self.page.query_selector_all(self.SELECTORS["job_cards"])
            self.logger.info(f"Found {len(job_cards)} job cards")
            
            for card in job_cards[:25]:  # Limit to first 25
                try:
                    job = self._extract_job_from_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    self.logger.warning(f"Failed to extract job: {e}")
                    continue
                
                # Rate limiting between extractions
                time.sleep(0.5)
            
            self.logger.info(f"Successfully extracted {len(jobs)} jobs")
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
        
        return jobs
    
    def _build_search_url(self, params: SearchParams) -> str:
        """Build LinkedIn job search URL."""
        base = f"{self.BASE_URL}/jobs/search"
        
        query_parts = []
        
        # Keywords
        if params.keywords:
            query_parts.append(f"keywords={quote(' '.join(params.keywords))}")
        
        # Location
        if params.location:
            query_parts.append(f"location={quote(params.location)}")
        
        # Date filter
        if params.date_filter == "past_24_hours":
            query_parts.append("f_TPR=r86400")
        elif params.date_filter == "past_week":
            query_parts.append("f_TPR=r604800")
        elif params.date_filter == "past_month":
            query_parts.append("f_TPR=r2592000")
        
        # Remote filter
        if params.remote_only:
            query_parts.append("f_WT=2")  # Remote work type
        
        # Job type
        if params.job_type:
            type_map = {
                JobType.FULL_TIME: "F",
                JobType.CONTRACT: "C",
                JobType.INTERNSHIP: "I",
            }
            if params.job_type in type_map:
                query_parts.append(f"f_JT={type_map[params.job_type]}")
        
        # Experience level
        if params.experience_level:
            exp_map = {
                ExperienceLevel.ENTRY: "1",
                ExperienceLevel.MID: "3",
                ExperienceLevel.SENIOR: "4",
            }
            if params.experience_level in exp_map:
                query_parts.append(f"f_E={exp_map[params.experience_level]}")
        
        return f"{base}?{'&'.join(query_parts)}"
    
    def _extract_job_from_card(self, card) -> Optional[JobListing]:
        """Extract job data from a LinkedIn job card."""
        try:
            # Job ID from data attribute or URL
            job_link = card.query_selector(self.SELECTORS["job_link"])
            if not job_link:
                return None
            
            href = job_link.get_attribute('href') or ''
            job_id_match = re.search(r'/jobs/view/(\d+)', href)
            job_id = job_id_match.group(1) if job_id_match else href.split('/')[-1].split('?')[0]
            
            # Basic info
            title_el = card.query_selector(self.SELECTORS["job_title"])
            title = title_el.inner_text().strip() if title_el else "Unknown"
            
            company_el = card.query_selector(self.SELECTORS["job_company"])
            company = company_el.inner_text().strip() if company_el else "Unknown"
            
            location_el = card.query_selector(self.SELECTORS["job_location"])
            location = location_el.inner_text().strip() if location_el else "Unknown"
            
            # Check for Easy Apply
            easy_apply = bool(card.query_selector("[aria-label*='Easy Apply']"))
            
            return JobListing(
                job_id=f"linkedin_{job_id}",
                title=title,
                company=company,
                location=location,
                description="",  # Will be fetched separately
                url=f"{self.BASE_URL}{href}" if href.startswith('/') else href,
                posted_date=None,
                job_type=None,
                remote_allowed="remote" in location.lower(),
                easy_apply=easy_apply,
                source_portal="linkedin",
                raw_data={"linkedin_id": job_id}
            )
            
        except Exception as e:
            self.logger.warning(f"Extraction error: {e}")
            return None
    
    def get_job_details(self, job_id: str) -> Optional[JobListing]:
        """Get full job details by clicking and scraping."""
        try:
            # Navigate to job URL
            linkedin_id = job_id.replace("linkedin_", "")
            url = f"{self.BASE_URL}/jobs/view/{linkedin_id}"
            
            self.page.goto(url)
            self.page.wait_for_load_state('networkidle')
            
            # Click show more if present
            try:
                show_more = self.page.wait_for_selector(
                    self.SELECTORS["show_more"], 
                    timeout=3000
                )
                if show_more:
                    show_more.click()
                    time.sleep(0.5)
            except:
                pass
            
            # Extract description
            desc_el = self.page.wait_for_selector(
                self.SELECTORS["job_description"], 
                timeout=5000
            )
            description = desc_el.inner_text() if desc_el else ""
            
            # Extract requirements from description
            requirements = self._extract_requirements(description)
            
            # Update job listing
            return JobListing(
                job_id=job_id,
                title="",  # Would be populated from search results
                company="",
                location="",
                description=description,
                url=url,
                requirements=requirements,
                source_portal="linkedin"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get job details: {e}")
            return None
    
    def _extract_requirements(self, description: str) -> List[str]:
        """Extract requirements from job description."""
        requirements = []
        
        # Look for requirements section
        patterns = [
            r'(?:Requirements?|Qualifications?|What You Need|Must Have).*?\n(.*?)(?:\n\n|\Z)',
            r'(?:Basic Qualifications?).*?\n(.*?)(?:\n\n|\Z)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Split by bullet points or newlines
                items = re.split(r'[•·\-\*]\s+|\n+', match)
                requirements.extend([i.strip() for i in items if len(i.strip()) > 5])
        
        return requirements[:20]  # Limit to 20 requirements
    
    def apply_to_job(self, job: JobListing, profile_data: Dict[str, Any]) -> bool:
        """Apply to a job using LinkedIn Easy Apply."""
        if not job.easy_apply:
            self.logger.info(f"Job {job.job_id} doesn't have Easy Apply")
            return False
        
        try:
            self.logger.info(f"Applying to {job.title} at {job.company}")
            
            # Navigate to job
            self.page.goto(job.url)
            self.page.wait_for_load_state('networkidle')
            
            # Click Easy Apply button
            easy_apply = self.page.wait_for_selector(
                self.SELECTORS["easy_apply_button"],
                timeout=5000
            )
            easy_apply.click()
            time.sleep(1)
            
            # Handle the application flow
            max_steps = 10
            for step in range(max_steps):
                self.logger.info(f"Application step {step + 1}")
                
                # Check for submit button (final step)
                submit = self.page.query_selector(self.SELECTORS["submit_button"])
                if submit and submit.is_visible():
                    submit.click()
                    self.logger.info("Application submitted!")
                    time.sleep(2)
                    
                    # Dismiss confirmation
                    try:
                        done = self.page.wait_for_selector(
                            self.SELECTORS["done_button"],
                            timeout=3000
                        )
                        done.click()
                    except:
                        pass
                    
                    return True
                
                # Check for review button
                review = self.page.query_selector(self.SELECTORS["review_button"])
                if review and review.is_visible():
                    review.click()
                    time.sleep(1)
                    continue
                
                # Click next/continue
                next_btn = self.page.query_selector(self.SELECTORS["next_button"])
                if next_btn and next_btn.is_visible():
                    next_btn.click()
                    time.sleep(1.5)
                else:
                    # No more steps
                    break
            
            self.logger.warning("Application flow incomplete")
            return False
            
        except Exception as e:
            self.logger.error(f"Application failed: {e}")
            return False
    
    def get_rate_limit_delay(self) -> float:
        """LinkedIn needs more conservative delays."""
        return 15.0  # 15 seconds between actions
    
    def close(self):
        """Clean up browser resources."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.logger.info("Browser closed")
        except Exception as e:
            self.logger.warning(f"Error closing browser: {e}")


# Register the adapter
PortalRegistry.register("linkedin", LinkedInAdapter)
