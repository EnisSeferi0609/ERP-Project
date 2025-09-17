"""Configuration management for the ERP application."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./erp.db")

    # Application Settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

    # Security
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    
    # PDF Generation
    WKHTMLTOPDF_PATH = os.getenv("WKHTMLTOPDF_PATH", "/usr/local/bin/wkhtmltopdf")
    
    # File Storage Paths
    BASE_DIR = Path(__file__).resolve().parent
    RECEIPTS_DIR = BASE_DIR / os.getenv("RECEIPTS_DIR", "receipts")
    INVOICES_DIR = BASE_DIR / os.getenv("INVOICES_DIR", "rechnungen")
    STATIC_DIR = BASE_DIR / "app" / "static"
    TEMPLATES_DIR = BASE_DIR / "app" / "templates"
    
    # Development Settings
    RELOAD = os.getenv("RELOAD", "False").lower() == "true"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        cls.RECEIPTS_DIR.mkdir(exist_ok=True)
        cls.INVOICES_DIR.mkdir(exist_ok=True)

# Create a global config instance
config = Config()