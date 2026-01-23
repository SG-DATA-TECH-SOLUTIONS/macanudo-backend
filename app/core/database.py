import logging
from google.cloud import firestore
from google.cloud.firestore import Client as FirestoreClient
from app.core.config import settings

logger = logging.getLogger(__name__)

# Firestore client instance
db: FirestoreClient | None = None


def connect_to_firestore() -> None:
    """Initialize Firestore connection."""
    global db
    try:
        # The project parameter uses the configured project ID
        # If GOOGLE_APPLICATION_CREDENTIALS env var is set, it will use those credentials
        db = firestore.Client(project=settings.FIRESTORE_PROJECT_ID)
        logger.info(f"Connected to Firestore project: {settings.FIRESTORE_PROJECT_ID}")
    except Exception as e:
        logger.error(f"Failed to connect to Firestore: {e}")
        raise


def close_firestore_connection() -> None:
    """Close Firestore connection."""
    global db
    if db:
        db.close()
        logger.info("Closed Firestore connection")


def get_database() -> FirestoreClient:
    """Get Firestore client instance."""
    if db is None:
        raise RuntimeError("Database not initialized. Call connect_to_firestore() first.")
    return db


def get_collection(collection_name: str) -> firestore.CollectionReference:
    """Get a Firestore collection reference."""
    database = get_database()
    return database.collection(collection_name)


# Note: Firestore doesn't require index creation like MongoDB
# Indexes are automatically created for single-field queries
# Composite indexes need to be created in Firebase Console or via firestore.indexes.json
async def create_indexes() -> None:
    """
    Firestore handles single-field indexes automatically.
    Composite indexes should be defined in firestore.indexes.json
    and deployed via Firebase CLI: firebase deploy --only firestore:indexes
    """
    logger.info("Firestore indexes are managed via Firebase Console or firestore.indexes.json")
