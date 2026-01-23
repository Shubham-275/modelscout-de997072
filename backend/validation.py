"""
Input validation utilities for ModelScout API.

Provides secure validation for user inputs to prevent:
- SQL injection
- Path traversal
- XSS attacks
- DoS via large inputs
"""

import re
from typing import Optional, List


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def validate_model_name(name: str, max_length: int = 200) -> str:
    """
    Validate and sanitize model name.
    
    Rules:
    - Must not be empty
    - Max length: 200 characters
    - Allowed characters: alphanumeric, hyphens, underscores, dots, forward slashes
    - No path traversal attempts (../)
    - No SQL injection patterns
    
    Args:
        name: Model name to validate
        max_length: Maximum allowed length
        
    Returns:
        Sanitized model name
        
    Raises:
        ValidationError: If validation fails
    """
    if not name:
        raise ValidationError("Model name cannot be empty")
    
    # Strip whitespace
    name = name.strip()
    
    # Check length
    if len(name) > max_length:
        raise ValidationError(f"Model name too long (max {max_length} characters)")
    
    # Check for path traversal
    if "../" in name or "..\\" in name:
        raise ValidationError("Invalid model name: path traversal detected")
    
    # Check for SQL injection patterns
    sql_patterns = [
        r"(\bOR\b|\bAND\b).*=",
        r";\s*(DROP|DELETE|UPDATE|INSERT)",
        r"--",
        r"/\*.*\*/",
        r"UNION\s+SELECT"
    ]
    for pattern in sql_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            raise ValidationError("Invalid model name: suspicious pattern detected")
    
    # Allow only safe characters: alphanumeric, hyphens, underscores, dots, slashes
    if not re.match(r'^[a-zA-Z0-9\-_./]+$', name):
        raise ValidationError(
            "Invalid model name format. "
            "Only alphanumeric characters, hyphens, underscores, dots, and slashes are allowed."
        )
    
    return name


def validate_source_key(source: str, allowed_sources: List[str]) -> str:
    """
    Validate benchmark source key.
    
    Args:
        source: Source key to validate
        allowed_sources: List of allowed source keys
        
    Returns:
        Validated source key
        
    Raises:
        ValidationError: If validation fails
    """
    if not source:
        raise ValidationError("Source key cannot be empty")
    
    source = source.strip().lower()
    
    if source not in allowed_sources:
        raise ValidationError(
            f"Invalid source key: {source}. "
            f"Allowed sources: {', '.join(allowed_sources)}"
        )
    
    return source


def validate_integer(value: any, min_val: Optional[int] = None, 
                     max_val: Optional[int] = None, name: str = "value") -> int:
    """
    Validate integer input.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Name of the field (for error messages)
        
    Returns:
        Validated integer
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        int_val = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a valid integer")
    
    if min_val is not None and int_val < min_val:
        raise ValidationError(f"{name} must be at least {min_val}")
    
    if max_val is not None and int_val > max_val:
        raise ValidationError(f"{name} must be at most {max_val}")
    
    return int_val


def validate_snapshot_id(snapshot_id: str) -> str:
    """
    Validate snapshot ID format.
    
    Snapshot IDs should be UUIDs or similar safe identifiers.
    
    Args:
        snapshot_id: Snapshot ID to validate
        
    Returns:
        Validated snapshot ID
        
    Raises:
        ValidationError: If validation fails
    """
    if not snapshot_id:
        raise ValidationError("Snapshot ID cannot be empty")
    
    snapshot_id = snapshot_id.strip()
    
    # Check length (UUIDs are typically 36 characters with hyphens)
    if len(snapshot_id) > 100:
        raise ValidationError("Snapshot ID too long")
    
    # Allow only alphanumeric and hyphens
    if not re.match(r'^[a-zA-Z0-9\-]+$', snapshot_id):
        raise ValidationError("Invalid snapshot ID format")
    
    return snapshot_id


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize general string input.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError("Value must be a string")
    
    value = value.strip()
    
    if len(value) > max_length:
        raise ValidationError(f"String too long (max {max_length} characters)")
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    return value
