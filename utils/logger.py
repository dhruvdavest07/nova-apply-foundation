"""
Nova Apply - Logger
Centralized logging for all operations.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for terminal output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        record.levelname = f"{log_color}{record.levelname}{reset}"
        return super().format(record)


def setup_logger(
    name: str = "nova_apply",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """Setup logger with file and console handlers."""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []  # Clear existing handlers
    
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Console handler with colors
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        ))
        logger.addHandler(console_handler)
    
    return logger


class ApplicationLogger:
    """Logger wrapper for application-specific logging."""
    
    def __init__(self, profile_id: Optional[str] = None):
        self.profile_id = profile_id
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = f"logs/nova_apply_{timestamp}.log"
        self.logger = setup_logger(
            name=f"nova_apply.{profile_id}" if profile_id else "nova_apply",
            log_file=log_file
        )
    
    def _format_msg(self, msg: str) -> str:
        if self.profile_id:
            return f"[{self.profile_id}] {msg}"
        return msg
    
    def debug(self, msg: str):
        self.logger.debug(self._format_msg(msg))
    
    def info(self, msg: str):
        self.logger.info(self._format_msg(msg))
    
    def warning(self, msg: str):
        self.logger.warning(self._format_msg(msg))
    
    def error(self, msg: str):
        self.logger.error(self._format_msg(msg))
    
    def critical(self, msg: str):
        self.logger.critical(self._format_msg(msg))
    
    def application_sent(self, job_title: str, company: str, portal: str):
        """Log successful application."""
        self.info(f"✅ APPLICATION SENT | {job_title} @ {company} via {portal}")
    
    def match_found(self, job_title: str, company: str, score: float):
        """Log high-quality match."""
        self.info(f"🎯 MATCH FOUND | {job_title} @ {company} | Score: {score:.2f}")
    
    def rate_limited(self, action: str, wait_time: float):
        """Log rate limiting."""
        self.warning(f"⏱️ RATE LIMITED | {action} | Waiting {wait_time:.1f}s")
    
    def portal_error(self, portal: str, error: str):
        """Log portal error."""
        self.error(f"❌ PORTAL ERROR | {portal}: {error}")
    
    def stealth_action(self, action: str, details: str = ""):
        """Log stealth action."""
        self.debug(f"🥷 STEALTH | {action} {details}")
