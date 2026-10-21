"""MyFarmAI Backend - Entry point using app factory."""

from app.factory import get_default_app

# The default app instance is created lazily with default settings
# For custom configurations, use create_app(custom_settings)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(get_default_app(), host="0.0.0.0", port=8000)
