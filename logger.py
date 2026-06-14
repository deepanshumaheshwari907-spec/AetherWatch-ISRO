import logging
import json
import os
from datetime import datetime, timezone
from config import Config

# Ensure log directory exists
os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON"""
    def format(self, record):
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data) if Config.LOG_FORMAT == "json" else super().format(record)

def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger instance with proper configuration
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        if Config.LOG_FORMAT == "json":
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # File handler
        try:
            file_handler = logging.FileHandler(Config.LOG_FILE)
            file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not create file logger: {e}")
        
        # Console handler
        if Config.LOG_TO_CONSOLE:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
    
    return logger
