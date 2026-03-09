"""
Nova Apply - Application Tracker
Tracks applications, monitors Gmail for confirmations, and generates reports.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum


class ApplicationStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
    ERROR = "error"


@dataclass
class ApplicationRecord:
    """Record of a job application."""
    id: Optional[int] = None
    profile_id: str = ""
    job_id: str = ""
    job_title: str = ""
    company: str = ""
    portal: str = ""
    status: ApplicationStatus = ApplicationStatus.PENDING
    match_score: float = 0.0
    applied_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    rejection_at: Optional[datetime] = None
    confirmation_email_id: Optional[str] = None
    notes: str = ""
    error_message: Optional[str] = None


class ApplicationTracker:
    """SQLite-based application tracking."""
    
    def __init__(self, db_path: str = "memory/applications.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    portal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    match_score REAL DEFAULT 0.0,
                    applied_at TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    rejection_at TIMESTAMP,
                    confirmation_email_id TEXT,
                    notes TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(profile_id, job_id)
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_profile ON applications(profile_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON applications(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_applied_date ON applications(applied_at)")
    
    def record_application(self, record: ApplicationRecord) -> int:
        """Record a new application. Returns the record ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO applications 
                (profile_id, job_id, job_title, company, portal, status, match_score, 
                 applied_at, notes, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.profile_id,
                record.job_id,
                record.job_title,
                record.company,
                record.portal,
                record.status.value,
                record.match_score,
                record.applied_at or datetime.now(),
                record.notes,
                record.error_message
            ))
            return cursor.lastrowid
    
    def update_status(self, application_id: int, status: ApplicationStatus, 
                     notes: str = "") -> None:
        """Update application status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE applications 
                SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status.value, notes, application_id))
    
    def confirm_application(self, profile_id: str, job_id: str, 
                           email_id: Optional[str] = None) -> bool:
        """Mark an application as confirmed (from Gmail)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE applications 
                SET status = ?, confirmed_at = ?, confirmation_email_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE profile_id = ? AND job_id = ?
            """, (ApplicationStatus.CONFIRMED.value, datetime.now(), email_id,
                  profile_id, job_id))
            return cursor.rowcount > 0
    
    def get_today_stats(self) -> Dict[str, Any]:
        """Get today's application statistics."""
        today = date.today()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Total submitted today
            submitted = conn.execute("""
                SELECT COUNT(*) FROM applications 
                WHERE DATE(applied_at) = DATE('now')
            """).fetchone()[0]
            
            # Confirmed today
            confirmed = conn.execute("""
                SELECT COUNT(*) FROM applications 
                WHERE DATE(confirmed_at) = DATE('now')
            """).fetchone()[0]
            
            # By profile
            by_profile = conn.execute("""
                SELECT profile_id, COUNT(*) as count 
                FROM applications 
                WHERE DATE(applied_at) = DATE('now')
                GROUP BY profile_id
            """).fetchall()
            
            # By portal
            by_portal = conn.execute("""
                SELECT portal, COUNT(*) as count 
                FROM applications 
                WHERE DATE(applied_at) = DATE('now')
                GROUP BY portal
            """).fetchall()
            
            return {
                "date": today.isoformat(),
                "submitted": submitted,
                "confirmed": confirmed,
                "confirmation_rate": confirmed / submitted if submitted > 0 else 0,
                "by_profile": {row['profile_id']: row['count'] for row in by_profile},
                "by_portal": {row['portal']: row['count'] for row in by_portal}
            }
    
    def get_profile_today_count(self, profile_id: str) -> int:
        """Get count of applications for profile today."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                SELECT COUNT(*) FROM applications 
                WHERE profile_id = ? AND DATE(applied_at) = DATE('now')
            """, (profile_id,)).fetchone()
            return result[0] if result else 0
    
    def get_recent_applications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent applications."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM applications 
                ORDER BY applied_at DESC 
                LIMIT ?
            """, (limit,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def get_unconfirmed_applications(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get applications pending confirmation (for Gmail monitoring)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM applications 
                WHERE status = ? 
                AND applied_at > datetime('now', '-{} days')
                ORDER BY applied_at DESC
            """.format(days), (ApplicationStatus.SUBMITTED.value,)).fetchall()
            
            return [dict(row) for row in rows]


class GmailMonitor:
    """Monitor Gmail for application confirmations."""
    
    CONFIRMATION_KEYWORDS = [
        "application submitted",
        "thank you for applying",
        "application received",
        "we have received your application",
        "your application has been received"
    ]
    
    REJECTION_KEYWORDS = [
        "not moving forward",
        "selected another candidate",
        "decided to move forward with other candidates",
        "position has been filled"
    ]
    
    def __init__(self, tracker: ApplicationTracker):
        self.tracker = tracker
    
    def check_for_confirmations(self) -> List[Dict[str, Any]]:
        """
        Check Gmail for new confirmation emails.
        Returns list of matched confirmations.
        """
        # TODO: Implement Gmail API integration
        # For now, return empty list
        return []
    
    def process_email(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single email for application status."""
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        
        # Check for confirmations
        for keyword in self.CONFIRMATION_KEYWORDS:
            if keyword in subject or keyword in body:
                return {
                    "type": "confirmation",
                    "email_id": email_data.get('id'),
                    "company": self._extract_company(email_data),
                    "job_title": self._extract_job_title(email_data)
                }
        
        # Check for rejections
        for keyword in self.REJECTION_KEYWORDS:
            if keyword in subject or keyword in body:
                return {
                    "type": "rejection",
                    "email_id": email_data.get('id'),
                    "company": self._extract_company(email_data),
                    "job_title": self._extract_job_title(email_data)
                }
        
        return None
    
    def _extract_company(self, email_data: Dict[str, Any]) -> str:
        """Extract company name from email."""
        # Simple extraction - improve with NLP later
        sender = email_data.get('from', '')
        # Remove email part, keep name
        if '<' in sender:
            sender = sender.split('<')[0].strip()
        return sender
    
    def _extract_job_title(self, email_data: Dict[str, Any]) -> str:
        """Extract job title from email."""
        # Simple extraction - improve with NLP later
        subject = email_data.get('subject', '')
        # Look for common patterns
        return "Unknown"
