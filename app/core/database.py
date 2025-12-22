import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient | None = None


async def connect_to_mongo() -> None:
    """Initialize MongoDB connection."""
    global client
    try:
        client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=10,
            minPoolSize=1,
        )
        # Ping to verify connection
        await client.admin.command("ping")
        logger.info(f"Connected to MongoDB at {settings.MONGODB_URL}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection() -> None:
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        logger.info("Closed MongoDB connection")


def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    if client is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return client[settings.MONGODB_DB_NAME]


async def create_indexes() -> None:
    """Create database indexes for optimal performance."""
    db = get_database()

    # User indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("is_active")

    # Item indexes
    await db.items.create_index("owner_id")
    await db.items.create_index("created_at")

    # Product indexes
    await db.products.create_index("name")
    await db.products.create_index("category")
    await db.products.create_index("is_active")

    # Recipe indexes
    await db.recipes.create_index("product_id")
    await db.recipes.create_index("is_active")

    # Sale indexes
    await db.sales.create_index("sale_number", unique=True)
    await db.sales.create_index("user_id")
    await db.sales.create_index("status")
    await db.sales.create_index("created_at")

    # Inventory adjustment indexes
    await db.inventory_adjustments.create_index("item_id")
    await db.inventory_adjustments.create_index("user_id")
    await db.inventory_adjustments.create_index("created_at")

    logger.info("Database indexes created successfully")
