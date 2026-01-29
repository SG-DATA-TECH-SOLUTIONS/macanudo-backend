import asyncio
import logging

from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.db import close_mongo_connection, connect_to_mongo, get_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init() -> None:
    try:
        asyncio.run(_init_async())
    except Exception as e:
        logger.error(e)
        raise e


async def _init_async() -> None:
    await connect_to_mongo()
    db = get_database()
    # Ping to ensure connectivity
    await db.command("ping")
    await close_mongo_connection()


def main() -> None:
    logger.info("Initializing service")
    init()
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
