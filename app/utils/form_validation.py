"""
Form validation utilities for the ERP system.
Complements file_validation.py for complete input validation.
"""

import re
from datetime import date, datetime
from typing import List, Tuple


class FormValidator:
    """Static methods for validating form input data."""

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format (optional field)."""
        if not email or not email.strip():
            return True, ""  # Email is optional

        email = email.strip()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            return False, "Ungültige E-Mail-Adresse"

        if len(email) > 255:
            return False, "E-Mail-Adresse ist zu lang (max. 255 Zeichen)"

        return True, ""

    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """Validate international phone number format."""
        if not phone or not phone.strip():
            return True, ""  # Phone is optional

        # Remove spaces, hyphens, parentheses, dots
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone.strip())

        # Basic international phone number validation
        # Must be between 7-15 digits, can start with + and country code
        if re.match(r'^\+\d{7,15}$', cleaned):  # International format with +
            return True, ""
        elif re.match(r'^0\d{8,14}$', cleaned):  # National format starting with 0
            return True, ""
        elif re.match(r'^\d{7,15}$', cleaned):  # Plain number format
            return True, ""
        else:
            return False, "Ungültige Telefonnummer (7-15 Ziffern, optional mit + oder 0 am Anfang)"

        return True, ""

    @staticmethod
    def validate_positive_number(value: str, field_name: str, allow_zero: bool = False) -> Tuple[bool, str]:
        """Validate positive number."""
        if not value or not value.strip():
            return False, f"{field_name} ist erforderlich"

        try:
            from decimal import Decimal, InvalidOperation
            # Use Decimal for precise currency validation
            num = Decimal(value.replace(',', '.'))  # Handle German decimal notation
            if num < 0:
                return False, f"{field_name} darf nicht negativ sein"
            if not allow_zero and num == 0:
                return False, f"{field_name} muss größer als 0 sein"
            if num > Decimal('999999.99'):
                return False, f"{field_name} ist zu hoch (max. 999.999,99)"
            return True, ""
        except (ValueError, InvalidOperation):
            return False, f"{field_name} muss eine gültige Zahl sein"

    @staticmethod
    def validate_required_text(text: str, field_name: str, max_length: int = 255) -> Tuple[bool, str]:
        """Validate required text field."""
        if not text or not text.strip():
            return False, f"{field_name} ist erforderlich"

        if len(text.strip()) > max_length:
            return False, f"{field_name} ist zu lang (max. {max_length} Zeichen)"

        return True, ""

    @staticmethod
    def validate_plz(plz: str) -> Tuple[bool, str]:
        """Validate German postal code."""
        if not plz or not plz.strip():
            return False, "Postleitzahl ist erforderlich"

        if not re.match(r'^\d{5}$', plz.strip()):
            return False, "Postleitzahl muss 5 Ziffern haben"

        return True, ""

    @staticmethod
    def validate_date(date_str: str, field_name: str, allow_future: bool = True) -> Tuple[bool, str]:
        """Validate date format and logic."""
        if not date_str or not date_str.strip():
            return False, f"{field_name} ist erforderlich"

        try:
            parsed_date = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()

            if parsed_date.year < 1900:
                return False, f"{field_name} ist zu weit in der Vergangenheit"

            if parsed_date.year > 2100:
                return False, f"{field_name} ist zu weit in der Zukunft"

            if not allow_future and parsed_date > date.today():
                return False, f"{field_name} darf nicht in der Zukunft liegen"

            return True, ""
        except ValueError:
            return False, f"{field_name} hat ein ungültiges Format (YYYY-MM-DD erwartet)"


def validate_customer_form(form_data: dict) -> List[str]:
    """Validate customer form and return list of error messages."""
    errors = []

    # Customer type validation
    kundenart = form_data.get('kundenart', '')
    if kundenart not in ['Privatkunde', 'Geschäftskunde']:
        errors.append("Kundenart muss ausgewählt werden")

    if kundenart == 'Privatkunde':
        # Validate private customer fields
        is_valid, error = FormValidator.validate_required_text(
            form_data.get('kunde_vorname', ''), "Vorname", 100)
        if not is_valid:
            errors.append(error)

        is_valid, error = FormValidator.validate_required_text(
            form_data.get('kunde_nachname', ''), "Nachname", 100)
        if not is_valid:
            errors.append(error)

    elif kundenart == 'Geschäftskunde':
        # Validate business customer fields
        is_valid, error = FormValidator.validate_required_text(
            form_data.get('kunde_firmenname', ''), "Firmenname", 200)
        if not is_valid:
            errors.append(error)

        is_valid, error = FormValidator.validate_required_text(
            form_data.get('ansprechpartner_vorname', ''), "Ansprechpartner Vorname", 100)
        if not is_valid:
            errors.append(error)

        is_valid, error = FormValidator.validate_required_text(
            form_data.get('ansprechpartner_nachname', ''), "Ansprechpartner Nachname", 100)
        if not is_valid:
            errors.append(error)

    # Common validations
    is_valid, error = FormValidator.validate_email(form_data.get('kunde_email', ''))
    if not is_valid:
        errors.append(error)

    is_valid, error = FormValidator.validate_phone(form_data.get('kunde_telefon', ''))
    if not is_valid:
        errors.append(error)

    is_valid, error = FormValidator.validate_required_text(
        form_data.get('kunde_rechnungsadresse', ''), "Rechnungsadresse", 300)
    if not is_valid:
        errors.append(error)

    is_valid, error = FormValidator.validate_plz(form_data.get('kunde_rechnung_plz', ''))
    if not is_valid:
        errors.append(error)

    is_valid, error = FormValidator.validate_required_text(
        form_data.get('kunde_rechnung_ort', ''), "Ort", 100)
    if not is_valid:
        errors.append(error)

    return errors