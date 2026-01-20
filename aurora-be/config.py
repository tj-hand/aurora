"""
Aurora Configuration

Environment-based configuration for Aurora module.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class AuroraSettings(BaseSettings):
    """Aurora module settings."""
    
    # Module identification
    module_name: str = "aurora"
    version: str = "0.1.0"
    
    # API settings
    api_prefix: str = "/api/v1/aurora"
    
    # Feature flags
    enable_audit_log: bool = True
    
    class Config:
        env_prefix = "AURORA_"
        case_sensitive = False


@lru_cache()
def get_settings() -> AuroraSettings:
    """Get cached settings instance."""
    return AuroraSettings()


settings = get_settings()
