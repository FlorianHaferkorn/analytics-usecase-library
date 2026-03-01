"""
Miscellaneous helper functions for Fabric automation.
Handles JSON loading/merging, logging, error handling.
"""
import json
import os
import sys
import uuid
from typing import Dict, Any, Optional

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        # Try to set UTF-8 encoding
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        # Fallback for older Python versions
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Color codes for terminal output
CDEFAULT = '\033[0m'
CDEFAULT_BOLD = '\033[1m'
CRED = '\033[91m'
CRED_BOLD = '\033[1;91m'
CYELLOW = '\033[33m'
CYELLOW_BOLD = '\033[1;33m'
CGREEN = '\033[32m'
CGREEN_BOLD = '\033[1;32m'
CBLUE_BOLD = '\033[1;34m'

# Unicode symbols with ASCII fallbacks
# Detect if console supports UTF-8, fallback to ASCII if not
_check_unicode_support = True
if sys.platform == 'win32':
    # On Windows, check encoding
    try:
        encoding = sys.stdout.encoding or 'utf-8'
        if encoding.lower() in ('cp1252', 'ascii', 'latin1'):
            _check_unicode_support = False
    except:
        _check_unicode_support = False

if _check_unicode_support:
    CHECKMARK = '✓'
    CROSSMARK = '✗'
    BULLET = '•'
    ARROW = '→'
else:
    CHECKMARK = '[OK]'
    CROSSMARK = '[X]'
    BULLET = '*'
    ARROW = '->'


def print_error(value: str, bold: bool = False):
    """Print error message in red."""
    try:
        if bold:
            print(f"{CRED_BOLD}{value}{CDEFAULT}", flush=True)
        else:
            print(f"{CRED}{value}{CDEFAULT}", flush=True)
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback to ASCII-safe output
        safe_value = value.encode('ascii', 'replace').decode('ascii')
        if bold:
            print(f"[ERROR] {safe_value}", flush=True)
        else:
            print(f"ERROR: {safe_value}", flush=True)


def print_warning(value: str, bold: bool = False):
    """Print warning message in yellow."""
    try:
        if bold:
            print(f"{CYELLOW_BOLD}{value}{CDEFAULT}", flush=True)
        else:
            print(f"{CYELLOW}{value}{CDEFAULT}", flush=True)
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback to ASCII-safe output
        safe_value = value.encode('ascii', 'replace').decode('ascii')
        if bold:
            print(f"[WARNING] {safe_value}", flush=True)
        else:
            print(f"WARNING: {safe_value}", flush=True)


def print_success(value: str, bold: bool = False):
    """Print success message in green."""
    try:
        if bold:
            print(f"{CGREEN_BOLD}{value}{CDEFAULT}", flush=True)
        else:
            print(f"{CGREEN}{value}{CDEFAULT}", flush=True)
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback to ASCII-safe output
        safe_value = value.encode('ascii', 'replace').decode('ascii')
        if bold:
            print(f"[SUCCESS] {safe_value}", flush=True)
        else:
            print(f"SUCCESS: {safe_value}", flush=True)


def print_info(value: str = "", bold: bool = False, end: str = "\n"):
    """Print info message."""
    try:
        if bold:
            print(f"{CDEFAULT_BOLD}{value}{CDEFAULT}", end=end, flush=True)
        else:
            print(f"{value}", end=end, flush=True)
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback to ASCII-safe output
        safe_value = value.encode('ascii', 'replace').decode('ascii')
        if bold:
            print(f"[INFO] {safe_value}", end=end, flush=True)
        else:
            print(f"{safe_value}", end=end, flush=True)


def print_header(value: str):
    """Print section header."""
    try:
        print("")
        print(f"{CBLUE_BOLD}{'#' * 125}{CDEFAULT}")
        print(f"{CBLUE_BOLD}# {value.center(123)} #{CDEFAULT}")
        print(f"{CBLUE_BOLD}{'#' * 125}{CDEFAULT}")
    except (UnicodeEncodeError, UnicodeDecodeError):
        safe_value = value.encode('ascii', 'replace').decode('ascii')
        print("")
        print("#" * 125)
        print(f"# {safe_value.center(123)} #")
        print("#" * 125)


def print_subheader(value: str):
    """Print subsection header."""
    try:
        print("")
        print(f"{CYELLOW_BOLD}{'#' * 110}{CDEFAULT}")
        print(f"{CYELLOW_BOLD}# {value.center(108)} #{CDEFAULT}")
        print(f"{CYELLOW_BOLD}{'#' * 110}{CDEFAULT}")
    except (UnicodeEncodeError, UnicodeDecodeError):
        safe_value = value.encode('ascii', 'replace').decode('ascii')
        print("")
        print("#" * 110)
        print(f"# {safe_value.center(108)} #")
        print("#" * 110)


def load_json(file_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON file and return dictionary."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON in file {file_path}: {e}")
            return None
    else:
        print_error(f"JSON file not found: {file_path}")
        return None


def is_guid(value: str) -> bool:
    """Check if string is a valid GUID."""
    try:
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj) == value.lower()
    except (ValueError, AttributeError, TypeError):
        return False


def merge_json(base: Dict[str, Any], override: Dict[str, Any], merge_type: int = 2) -> Dict[str, Any]:
    """
    Merge two JSON dictionaries.
    
    merge_type:
    1 = Override completely (replace entire value)
    2 = Deep merge (merge nested dictionaries, override lists)
    
    Args:
        base: Base dictionary
        override: Override dictionary
        merge_type: Merge strategy (1 or 2)
    
    Returns:
        Merged dictionary
    """
    if merge_type == 1:
        # Complete override
        result = base.copy()
        result.update(override)
        return result
    
    # Deep merge (merge_type == 2)
    result = base.copy()
    
    for key, value in override.items():
        if key == "merge_type":
            continue  # Skip merge_type metadata
        
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            nested_merge_type = value.get("merge_type", merge_type)
            result[key] = merge_json(result[key], value, nested_merge_type)
        else:
            # Override or add new key
            result[key] = value
    
    return result


def replace_template_variables(text: str, variables: Dict[str, str]) -> str:
    """Replace template variables in string (e.g., {environment} -> dev)."""
    result = text
    for key, value in variables.items():
        result = result.replace(f"{{{key}}}", value)
    return result


def format_workspace_name(template: str, layer: str, environment: str) -> str:
    """Format workspace name from template."""
    return replace_template_variables(template, {
        "layer": layer,
        "environment": environment
    })
