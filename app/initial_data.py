import asyncio
import logging

from app.core.db import close_mongo_connection, connect_to_mongo, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init() -> None:
    await connect_to_mongo()
    await init_db()
    await close_mongo_connection()


def main() -> None:
    logger.info("Creating initial data")
    asyncio.run(init())
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
