import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler

def setup_logging(log_dir: str = "logs", level: str = "INFO") -> None:
    """Setup application-wide logging configuration"""
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Setup handlers
    file_handler = RotatingFileHandler(
        log_dir / "chatbot.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    
    console_handler = RichHandler(rich_tracebacks=True)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    
    # Setup root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[file_handler, console_handler]
    )