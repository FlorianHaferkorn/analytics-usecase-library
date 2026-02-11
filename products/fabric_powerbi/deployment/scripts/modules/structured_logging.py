"""
Structured Logging Module

Provides structured logging capabilities for deployment operations.
Logs can be written to console, file, or both.
"""
import os
import sys
import json
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """Structured logger for deployment operations."""
    
    def __init__(self, log_file: Optional[str] = None, log_level: LogLevel = LogLevel.INFO):
        self.log_file = log_file
        self.log_level = log_level
        self.logs: List[Dict[str, Any]] = []
        
        # Create log directory if needed
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged based on log level."""
        levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
        return levels.index(level) >= levels.index(self.log_level)
    
    def _write_log(self, level: LogLevel, message: str, context: Dict[str, Any] = None):
        """Write log entry."""
        if not self._should_log(level):
            return
        
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": level.value,
            "message": message,
            "context": context or {}
        }
        
        self.logs.append(log_entry)
        
        # Write to file if configured
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except Exception as e:
                # Don't fail if logging fails
                print(f"Warning: Failed to write to log file: {e}", file=sys.stderr)
    
    def debug(self, message: str, context: Dict[str, Any] = None):
        """Log debug message."""
        self._write_log(LogLevel.DEBUG, message, context)
    
    def info(self, message: str, context: Dict[str, Any] = None):
        """Log info message."""
        self._write_log(LogLevel.INFO, message, context)
    
    def warning(self, message: str, context: Dict[str, Any] = None):
        """Log warning message."""
        self._write_log(LogLevel.WARNING, message, context)
    
    def error(self, message: str, context: Dict[str, Any] = None):
        """Log error message."""
        self._write_log(LogLevel.ERROR, message, context)
    
    def critical(self, message: str, context: Dict[str, Any] = None):
        """Log critical message."""
        self._write_log(LogLevel.CRITICAL, message, context)
    
    def log_operation(self, operation: str, status: str, details: Dict[str, Any] = None):
        """Log an operation with status."""
        context = {
            "operation": operation,
            "status": status,
            **{k: v for k, v in (details or {}).items() if v is not None}
        }
        
        if status.lower() in ["success", "completed"]:
            self.info(f"Operation {operation} {status}", context)
        elif status.lower() in ["failed", "error"]:
            self.error(f"Operation {operation} {status}", context)
        else:
            self.info(f"Operation {operation} {status}", context)
    
    def export_logs(self, output_file: str):
        """Export all logs to a JSON file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error exporting logs: {e}", file=sys.stderr)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of logs."""
        total = len(self.logs)
        by_level = {}
        for level in LogLevel:
            by_level[level.value] = len([l for l in self.logs if l["level"] == level.value])
        
        return {
            "total_logs": total,
            "by_level": by_level,
            "first_log": self.logs[0]["timestamp"] if self.logs else None,
            "last_log": self.logs[-1]["timestamp"] if self.logs else None
        }
