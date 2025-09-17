"""
File validation utilities for the ERP system.
Consolidates duplicate file validation logic found in rechnung_route.py and buchungen.py.
"""
import os
from typing import Tuple


# File security validation constants
ALLOWED_FILE_TYPES = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.tiff', '.bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_file_upload(file) -> Tuple[bool, str]:
    """
    Validate uploaded file for security and constraints.
    
    Args:
        file: UploadFile object from FastAPI
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not file or not hasattr(file, 'filename') or not file.filename:
        return False, "Keine Datei ausgewählt"
    
    # Check file extension
    file_extension = os.path.splitext(file.filename.lower())[1]
    if file_extension not in ALLOWED_FILE_TYPES:
        return False, f"Dateityp nicht erlaubt. Erlaubte Typen: {', '.join(ALLOWED_FILE_TYPES)}"
    
    # Read file to check size and basic content validation
    file_content = file.file.read()
    file.file.seek(0)  # Reset file pointer
    
    # Check file size
    if len(file_content) > MAX_FILE_SIZE:
        return False, f"Datei zu groß. Maximum: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    # Basic content validation for images
    if file_extension in {'.jpg', '.jpeg', '.png', '.gif', '.tiff', '.bmp'}:
        # Check if file starts with expected magic bytes
        if file_extension in {'.jpg', '.jpeg'} and not file_content.startswith(b'\xff\xd8'):
            return False, "Ungültiges JPEG-Format"
        elif file_extension == '.png' and not file_content.startswith(b'\x89PNG'):
            return False, "Ungültiges PNG-Format"
        elif file_extension == '.gif' and not file_content.startswith(b'GIF8'):
            return False, "Ungültiges GIF-Format"
    
    # Basic content validation for PDF
    elif file_extension == '.pdf' and not file_content.startswith(b'%PDF'):
        return False, "Ungültiges PDF-Format"
    
    return True, "OK"