# error_logger.py
# Global error/crash logging system for JARVIS
#
# Every error, crash, and failure is logged to errors.md with:
#   - Timestamp
#   - Error type and message
#   - Stack trace (if available)
#   - Context (what was being done when error occurred)
#   - Resolution status (open/resolved)
#
# JARVIS can read/write this file and report on all errors.

import sys
import os
import json
import traceback
import datetime
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Path to the errors.md file
ERRORS_FILE = Path.home() / ".jarvis" / "errors.md"
ERRORS_DIR = Path.home() / ".jarvis"

# Ensure directory exists
ERRORS_DIR.mkdir(parents=True, exist_ok=True)

# Thread safety
_errors_lock = threading.Lock()

# In-memory error cache for quick access
_error_cache: List[Dict] = []
_cache_lock = threading.Lock()


def _now() -> str:
    """Get current timestamp in ISO format"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _now_short() -> str:
    """Get current date for grouping"""
    return datetime.datetime.now().strftime("%Y-%m-%d")


def _format_error(
    error_type: str,
    error_message: str,
    context: str = "",
    stack_trace: str = "",
    command: str = "",
    agent: str = "",
    additional_info: Dict = None,
    error_id: str = ""
) -> str:
    """Format an error entry as a markdown block"""
    info = additional_info or {}
    
    markdown = f"""## 🔴 Error: {error_id} ({error_type})

- **Date**: {_now()}
- **Error Type**: {error_type}
- **Error ID**: {error_id}
- **Message**: {error_message}
"""
    
    if command:
        markdown += f"- **Command**: `{command}`\n"
    if agent:
        markdown += f"- **Agent**: {agent}\n"
    if context:
        markdown += f"- **Context**: {context}\n"
    if stack_trace:
        markdown += f"- **Stack Trace**:\n```\n{stack_trace[:2000]}\n```\n"
    
    for key, value in info.items():
        markdown += f"- **{key}**: {value}\n"
    
    markdown += f"- **Status**: Open\n---\n\n"
    
    return markdown


def log_error(
    error_type: str,
    error_message: str,
    context: str = "",
    stack_trace: str = "",
    command: str = "",
    agent: str = "",
    additional_info: Dict = None
) -> str:
    """
    Log an error/crash to errors.md. Returns the error ID.
    
    Args:
        error_type: Category of error (e.g., "API Error", "File Not Found", "Agent Failed")
        error_message: The actual error message
        context: What was being done when the error occurred
        stack_trace: Full traceback if available
        command: The command that triggered the error
        agent: Which agent encountered the error
        additional_info: Any extra info to log
    
    Returns:
        Error ID string
    """
    error_id = f"ERR-{_now().replace(' ', '-').replace(':', '')}"
    
    # Format the error entry
    entry = _format_error(
        error_type, error_message, context, stack_trace, command, agent, additional_info, error_id
    )
    
    # Write to errors.md
    with _errors_lock:
        try:
            # Read existing content
            if ERRORS_FILE.exists():
                with open(ERRORS_FILE, "r", encoding="utf-8") as f:
                    existing = f.read()
            else:
                existing = ""
            
            # Add header if new file
            if not existing.strip():
                existing = """# JARVIS Error Log

All errors, crashes, and failures are automatically logged here.
Errors are organized by date with full context for debugging.

## Summary
- Total Errors: 0
- Last Updated: N/A
- Open Issues: 0

---

"""
            
            # Prepend new entry (newest first)
            new_content = existing + "\n" + entry
            
            # Write back
            with open(ERRORS_FILE, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            # Update summary in header
            _update_summary()
            
        except Exception as e:
            # If we can't write to the file, at least log to console
            print(f"[ErrorLogger] ⚠️ Could not write to errors.md: {e}")
            print(f"[ErrorLogger] Error was: {error_type}: {error_message}")
    
    # Update in-memory cache
    error_entry = {
        "error_id": error_id,
        "error_type": error_type,
        "error_message": error_message,
        "context": context,
        "stack_trace": stack_trace[:500] if stack_trace else "",
        "command": command,
        "agent": agent,
        "additional_info": additional_info or {},
        "timestamp": _now(),
        "status": "open"
    }
    
    with _cache_lock:
        global _error_cache
        _error_cache.insert(0, error_entry)
        # Keep cache size manageable
        if len(_error_cache) > 200:
            _error_cache = _error_cache[:200]
    
    return error_id


def _update_summary():
    """Update the summary section at the top of errors.md"""
    try:
        if not ERRORS_FILE.exists():
            return
        
        with open(ERRORS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Count errors
        total_errors = content.count("## 🔴 Error:")
        open_errors = content.count("- **Status**: Open")
        resolved_errors = content.count("- **Status**: Resolved")
        last_update = _now()
        
        # Find and update summary
        summary_end = content.find("---")
        if summary_end > 0:
            new_summary = f"""## Summary
- Total Errors: {total_errors}
- Last Updated: {last_update}
- Open Issues: {open_errors}
- Resolved: {resolved_errors}

---

"""
            # Replace summary section
            start = content.find("# JARVIS Error Log")
            if start >= 0:
                content = content[:start] + new_summary + content[summary_end + 3:]
                with open(ERRORS_FILE, "w", encoding="utf-8") as f:
                    f.write(content)
    except Exception:
        pass


def read_errors(date: str = None, limit: int = 50) -> List[Dict]:
    """
    Read errors from errors.md.
    
    Args:
        date: Filter by date (YYYY-MM-DD). If None, read all.
        limit: Maximum number of errors to return
    
    Returns:
        List of error dictionaries
    """
    # Check in-memory cache first
    with _cache_lock:
        cached = _error_cache[:limit]
        if date:
            cached = [e for e in cached if e["timestamp"].startswith(date)]
        if cached:
            return cached
    
    # Fall back to file
    errors = []
    if not ERRORS_FILE.exists():
        return errors
    
    try:
        with open(ERRORS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Parse markdown blocks
        blocks = content.split("## 🔴 Error:")
        for block in blocks[1:]:  # Skip header
            error = _parse_error_block(block)
            if error and (not date or error["timestamp"].startswith(date)):
                errors.append(error)
            
            if len(errors) >= limit:
                break
    except Exception as e:
        print(f"[ErrorLogger] ⚠️ Could not read errors.md: {e}")
    
    return errors


def _parse_error_block(block: str) -> Optional[Dict]:
    """Parse a markdown error block into a dictionary"""
    lines = block.strip().split("\n")
    error = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith("- **Date**"):
            error["timestamp"] = line.split(": ", 1)[1] if ": " in line else ""
        elif line.startswith("- **Error Type**"):
            error["error_type"] = line.split(": ", 1)[1] if ": " in line else ""
        elif line.startswith("- **Message**"):
            error["error_message"] = line.split(": ", 1)[1] if ": " in line else ""
        elif line.startswith("- **Command**"):
            error["command"] = line.split(": ", 1)[1] if ": " in line else ""
        elif line.startswith("- **Agent**"):
            error["agent"] = line.split(": ", 1)[1] if ": " in line else ""
        elif line.startswith("- **Status**"):
            error["status"] = line.split(": ", 1)[1] if ": " in line else "open"
        elif line.startswith("- **Context**"):
            error["context"] = line.split(": ", 1)[1] if ": " in line else ""
    
    return error if error else None


def resolve_error(error_id: str) -> bool:
    """
    Mark an error as resolved in errors.md.
    
    Args:
        error_id: The error ID to resolve
    
    Returns:
        True if resolved, False if not found
    """
    if not ERRORS_FILE.exists():
        return False
    
    try:
        with open(ERRORS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Find and update the error status
        target_block = f"## 🔴 Error: {error_id}"
        if target_block in content:
            # Replace status
            old_pattern = "- **Status**: Open"
            new_pattern = f"- **Status**: Resolved (resolved at {_now()})"
            
            # Find the block and update it
            block_start = content.find(target_block)
            block_end = content.find("## 🔴 Error:", block_start + 1)
            if block_end == -1:
                block_end = len(content)
            
            block = content[block_start:block_end]
            new_block = block.replace("- **Status**: Open", new_pattern)
            
            new_content = content[:block_start] + new_block + content[block_end:]
            
            with open(ERRORS_FILE, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            # Update cache
            with _cache_lock:
                for entry in _error_cache:
                    if entry.get("error_id") == error_id:
                        entry["status"] = "resolved"
            
            return True
    except Exception as e:
        print(f"[ErrorLogger] ⚠️ Could not resolve error {error_id}: {e}")
    
    return False


def get_error_summary() -> Dict:
    """
    Get a summary of all errors.
    
    Returns:
        Dictionary with error statistics
    """
    errors = read_errors(limit=10000)
    
    total = len(errors)
    open_errors = sum(1 for e in errors if e.get("status") == "open")
    resolved_errors = sum(1 for e in errors if e.get("status") == "resolved")
    
    # Count by type
    by_type = {}
    by_date = {}
    
    for error in errors:
        etype = error.get("error_type", "Unknown")
        by_type[etype] = by_type.get(etype, 0) + 1
        
        date = error.get("timestamp", "")[:10]  # YYYY-MM-DD
        if date:
            by_date[date] = by_date.get(date, 0) + 1
    
    return {
        "total_errors": total,
        "open_errors": open_errors,
        "resolved_errors": resolved_errors,
        "by_type": by_type,
        "by_date": by_date,
        "last_updated": _now(),
        "errors_file": str(ERRORS_FILE)
    }


def get_recent_errors(count: int = 10) -> List[Dict]:
    """Get the most recent errors"""
    return read_errors(limit=count)


def format_errors_for_report(count: int = 10) -> str:
    """
    Format recent errors as a human-readable report.
    
    Returns:
        String formatted for display/speaking
    """
    errors = read_errors(limit=count)
    
    if not errors:
        return "No errors recorded in the log, sir."
    
    lines = [f"Error log shows {len(errors)} recent error(s):"]
    
    for i, error in enumerate(errors, 1):
        timestamp = error.get("timestamp", "unknown")
        etype = error.get("error_type", "Unknown")
        message = error.get("error_message", "")[:80]
        status = error.get("status", "open")
        command = error.get("command", "")[:40]
        
        lines.append(f"  {i}. [{timestamp}] {etype}: {message}")
        if command:
            lines.append(f"     Command: {command}")
        lines.append(f"     Status: {status}")
    
    return "\n".join(lines)


# Convenience wrapper for agent/error_handler integration
def log_agent_error(agent_name: str, error_msg: str, context: str = ""):
    """Log an error from an agent"""
    return log_error(
        error_type="Agent Error",
        error_message=error_msg,
        context=context,
        agent=agent_name
    )


def log_command_error(command: str, error_msg: str, context: str = ""):
    """Log an error from a command execution"""
    return log_error(
        error_type="Command Error",
        error_message=error_msg,
        context=context,
        command=command
    )


def log_api_error(api_name: str, error_msg: str, context: str = ""):
    """Log an API-related error"""
    return log_error(
        error_type="API Error",
        error_message=error_msg,
        context=context,
        additional_info={"api": api_name}
    )


# Test function
def test_error_logger():
    """Test the error logger"""
    error_id = log_error(
        error_type="Test Error",
        error_message="This is a test error",
        context="Testing the error logging system",
        command="test_command",
        agent="TestAgent"
    )
    
    summary = get_error_summary()
    recent = get_recent_errors(3)
    
    print(f"Test error logged: {error_id}")
    print(f"Summary: {summary}")
    print(f"Recent errors: {[e['error_id'] for e in recent]}")
    
    # Clean up test entry
    resolve_error(error_id)
    
    print("Error logger test complete!")


if __name__ == "__main__":
    test_error_logger()