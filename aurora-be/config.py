"""Aurora module configuration"""

from pydantic_settings import BaseSettings


class AuroraConfig(BaseSettings):
    """Configuration for Aurora module"""

    # Token settings
    invitation_expiry_days: int = 7
    token_length: int = 32

    # Email settings
    company_name: str = "Your Company"
    support_email: str = "support@example.com"
    brand_primary_color: str = "#4F46E5"
    app_url: str = "http://localhost:3000"

    # Pagination limits
    max_page_size: int = 100
    default_page_size: int = 50

    class Config:
        env_prefix = "AURORA_"


# Global config instance
aurora_config = AuroraConfig()
