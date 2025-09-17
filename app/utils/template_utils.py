"""
Template utilities for consistent Jinja2 setup and common functions.
"""
import json
from pathlib import Path
from fastapi.templating import Jinja2Templates
from config import config


def from_json(value):
    """
    Convert JSON string to Python object for use in templates.

    Args:
        value: JSON string or None

    Returns:
        Parsed JSON object or empty list if invalid/None
    """
    if value:
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return []
    return []


def german_decimal(value, decimals=2):
    """
    Format number with German decimal notation.

    German notation uses:
    - Comma (,) as decimal separator
    - Period (.) as thousands separator

    Args:
        value: Number to format
        decimals: Number of decimal places (default: 2)

    Returns:
        Formatted string in German notation (e.g., "1.234,56")
    """
    if value is None:
        return "0" + "," + "0" * decimals if decimals > 0 else "0"

    try:
        num_value = float(value)

        # Format with thousands separators and decimal places
        # First format with English notation, then convert to German
        formatted = f"{num_value:,.{decimals}f}"

        # Split by decimal point
        if '.' in formatted:
            integer_part, decimal_part = formatted.split('.')
            # Replace commas with dots in integer part (thousands separators)
            german_integer = integer_part.replace(',', '.')
            # Combine with comma as decimal separator
            return f"{german_integer},{decimal_part}"
        else:
            # No decimal part, just replace thousands separators
            return formatted.replace(',', '.')

    except (ValueError, TypeError):
        return "0" + "," + "0" * decimals if decimals > 0 else "0"


def create_templates() -> Jinja2Templates:
    """
    Create a standardized Jinja2Templates instance with common filters.

    Returns:
        Jinja2Templates: Configured templates instance
    """
    # Use config for template directory if available, otherwise fallback
    template_dir = getattr(config, 'TEMPLATES_DIR', 'app/templates')
    templates = Jinja2Templates(directory=str(template_dir))

    # Add common filters
    templates.env.filters['from_json'] = from_json
    templates.env.filters['german_decimal'] = german_decimal

    return templates