"""
Date parsing utilities for consistent date handling across the application.
"""
from datetime import datetime, date
from typing import Optional


def parse_german_date(date_str: str) -> Optional[date]:
    """
    Parse German date format (DD.MM.YYYY) to Python date object.
    
    Args:
        date_str: Date string in German format (DD.MM.YYYY)
        
    Returns:
        date object or None if parsing fails
    """
    if not date_str:
        return None
        
    try:
        return datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError:
        return None


def parse_german_decimal(value_str: str) -> Optional[float]:
    """
    Parse German decimal format (uses comma as decimal separator) to float.
    
    Args:
        value_str: Decimal string in German format (e.g., "123,45")
        
    Returns:
        float value or None if parsing fails
    """
    if not value_str:
        return None
        
    try:
        # Replace comma with dot for parsing
        normalized = value_str.replace(',', '.')
        return float(normalized)
    except (ValueError, AttributeError):
        return None


def format_german_date(date_obj: date) -> str:
    """
    Format date object to German date string (DD.MM.YYYY).
    
    Args:
        date_obj: Python date object
        
    Returns:
        Formatted date string
    """
    if not date_obj:
        return ""
    return date_obj.strftime('%d.%m.%Y')