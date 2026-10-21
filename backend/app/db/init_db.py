import asyncio

from app.core.config import settings
from app.db.connection import init_db


async def main() -> None:
    print(f"Initializing database at: {settings.database_path}")
    await init_db()
    print("Database initialized successfully.")


if __name__ == "__main__":
    asyncio.run(main())
