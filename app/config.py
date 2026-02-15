"""
Configuration settings for the Office Wi-Fi Tracker.
Loads settings from environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Office Wi-Fi configuration
    office_wifi_name: str = "YourOfficeWiFiName"
    
    # Server configuration
    server_host: str = "127.0.0.1"
    server_port: int = 8787
    
    # Logging configuration
    log_level: str = "INFO"
    log_to_file: bool = False
    log_file_path: str = "logs/app.log"
    
    # Work duration settings
    work_duration_hours: int = 4
    buffer_minutes: int = 10
    
    # Check intervals (in seconds)
    wifi_check_interval_seconds: int = 30
    timer_check_interval_seconds: int = 60
    
    # Testing mode
    test_mode: bool = False
    test_duration_minutes: int = 2
    
    # Data directory (legacy - for file storage fallback)
    data_dir: str = "data"
    archive_dir: str = "data/archive"

    # MongoDB configuration (NEW)
    mongodb_uri: str = "mongodb+srv://rahul4317:Ad%400000121Rahul@cluster0.dwi1fgs.mongodb.net/wifi-calculator"
    mongodb_database: str = "wifi-calculator"

    # Grace period settings (NEW)
    grace_period_minutes: int = 2

    # Network connectivity check (NEW)
    connectivity_check_interval_seconds: int = 30

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
