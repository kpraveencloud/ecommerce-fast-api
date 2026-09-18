from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Backend API
    fastapi_base_url: str = "http://localhost:8000"

    # Retry & Resilience
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60

    # Request Configuration
    request_timeout: int = 30
    payment_timeout: int = 60
    search_timeout: int = 15
    shipping_timeout: int = 20
    connection_pool_size: int = 100
    max_keepalive_connections: int = 20

    # Caching
    cache_enabled: bool = True
    cache_ttl: int = 300

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Logging
    log_level: str = "INFO"
    enable_structured_logging: bool = False

    # Metrics & Monitoring
    enable_metrics: bool = False
    enable_tracing: bool = False

    # Feature Flags
    feature_payments: bool = True
    feature_shipping: bool = True
    feature_inventory: bool = True
    feature_search: bool = True
    feature_promotions: bool = True
    feature_analytics: bool = True
    feature_communication: bool = True
    feature_returns: bool = True
    feature_batch: bool = True

    # Pagination
    default_page_limit: int = 100
    max_page_limit: int = 1000

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )


settings = Settings()
