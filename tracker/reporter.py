"""
Nova Apply - Reporter
Generates daily WhatsApp reports on application activity.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from dataclasses import dataclass


@dataclass
class DailyReport:
    """Daily application report."""
    date: date
    total_submitted: int
    total_confirmed: int
    confirmation_rate: float
    by_profile: Dict[str, int]
    by_portal: Dict[str, int]
    blockers: List[str]
    highlights: List[str]
    next_steps: List[str]
    
    def to_whatsapp_message(self) -> str:
        """Format report for WhatsApp."""
        lines = [
            f"📊 *Nova Apply - Daily Report*",
            f"📅 {self.date.strftime('%A, %B %d, %Y')}",
            "",
            f"✅ *Applications Submitted:* {self.total_submitted}",
            f"📬 *Confirmations Received:* {self.total_confirmed}",
            f"📈 *Confirmation Rate:* {self.confirmation_rate:.1%}",
            "",
        ]
        
        # By profile
        if self.by_profile:
            lines.append("*By Profile:*")
            for profile, count in self.by_profile.items():
                lines.append(f"  • {profile}: {count}")
            lines.append("")
        
        # By portal
        if self.by_portal:
            lines.append("*By Portal:*")
            for portal, count in self.by_portal.items():
                lines.append(f"  • {portal}: {count}")
            lines.append("")
        
        # Blockers
        if self.blockers:
            lines.append("⚠️ *Blockers:*")
            for blocker in self.blockers:
                lines.append(f"  • {blocker}")
            lines.append("")
        
        # Highlights
        if self.highlights:
            lines.append("🎯 *Highlights:*")
            for highlight in self.highlights:
                lines.append(f"  • {highlight}")
            lines.append("")
        
        # Next steps
        if self.next_steps:
            lines.append("🚀 *Next Steps:*")
            for step in self.next_steps:
                lines.append(f"  • {step}")
        
        return "\n".join(lines)
    
    def to_text_summary(self) -> str:
        """Short text summary for quick reading."""
        return (
            f"Nova Apply Report ({self.date}): "
            f"{self.total_submitted} apps submitted, "
            f"{self.total_confirmed} confirmed "
            f"({self.confirmation_rate:.0%} rate)"
        )


class Reporter:
    """Generates reports from application data."""
    
    def __init__(self, tracker):
        self.tracker = tracker
    
    def generate_daily_report(self, target_date: Optional[date] = None) -> DailyReport:
        """Generate daily report from tracker data."""
        if target_date is None:
            target_date = date.today()
        
        stats = self.tracker.get_today_stats()
        
        # Get recent applications for highlights
        recent = self.tracker.get_recent_applications(limit=10)
        
        # Generate highlights
        highlights = []
        if recent:
            high_matches = [r for r in recent if r.get('match_score', 0) > 0.8]
            if high_matches:
                highlights.append(f"{len(high_matches)} high-match applications")
        
        # Check for blockers
        blockers = []
        # TODO: Add blocker detection logic
        
        # Next steps
        next_steps = [
            "Continue monitoring Gmail for confirmations",
            "Review tomorrow's job matches"
        ]
        
        return DailyReport(
            date=target_date,
            total_submitted=stats.get('submitted', 0),
            total_confirmed=stats.get('confirmed', 0),
            confirmation_rate=stats.get('confirmation_rate', 0),
            by_profile=stats.get('by_profile', {}),
            by_portal=stats.get('by_portal', {}),
            blockers=blockers,
            highlights=highlights,
            next_steps=next_steps
        )
    
    def send_whatsapp_report(self, report: DailyReport) -> bool:
        """Send report via WhatsApp."""
        message = report.to_whatsapp_message()
        # TODO: Integrate with OpenClaw messaging
        print(f"[Reporter] Would send WhatsApp report:\n{message}")
        return True


def generate_end_of_session_report(
    profile_id: str,
    applications_sent: int,
    thank_yous_received: int,
    blockers: List[str],
    next_steps: List[str]
) -> str:
    """Generate session-end report for memory file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    lines = [
        f"## Session Report - {timestamp}",
        f"",
        f"**Profile:** {profile_id}",
        f"**Applications Sent:** {applications_sent}",
        f"**Thank You Emails:** {thank_yous_received}",
        f"",
    ]
    
    if blockers:
        lines.append("**Blockers:**")
        for b in blockers:
            lines.append(f"- {b}")
        lines.append("")
    
    if next_steps:
        lines.append("**Next Steps:**")
        for s in next_steps:
            lines.append(f"- {s}")
    
    return "\n".join(lines)
