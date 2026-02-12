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
    
    # Check intervals (in seconds)
    wifi_check_interval_seconds: int = 30
    timer_check_interval_seconds: int = 60
    
    # Testing mode
    test_mode: bool = False
    test_duration_minutes: int = 2
    
    # Data directory
    data_dir: str = "data"
    archive_dir: str = "data/archive"
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
