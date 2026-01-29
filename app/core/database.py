import logging
import firebase_admin
from firebase_admin import credentials, firestore as firebase_firestore
from google.cloud import firestore
from google.cloud.firestore import Client as FirestoreClient
from app.core.config import settings

logger = logging.getLogger(__name__)

# Firestore client instance
db: FirestoreClient | None = None


def initialize_firebase() -> None:
    """Initialize Firebase Admin SDK.
    
    En Cloud Run, los paréntesis vacíos permiten que la librería
    detecte automáticamente la cuenta de servicio del entorno.
    En desarrollo local, usa las credenciales del archivo JSON.
    """
    try:
        if not firebase_admin._apps:
            # En producción (Cloud Run), deja los paréntesis vacíos
            # La librería detectará automáticamente la cuenta de servicio
            if settings.ENVIRONMENT in ["staging", "production"]:
                firebase_admin.initialize_app()
                logger.info("Firebase Admin initialized with default credentials (Cloud Run)")
            else:
                # En desarrollo local, usa el archivo de credenciales
                cred = credentials.Certificate("macanudo-credentials.json")
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin initialized with service account file")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin: {e}")
        raise


def connect_to_firestore() -> None:
    """Initialize Firestore connection."""
    global db
    try:
        # Inicializar Firebase Admin primero
        initialize_firebase()
        
        # The project parameter uses the configured project ID
        # If GOOGLE_APPLICATION_CREDENTIALS env var is set, it will use those credentials
        # db = firestore.Client(project=settings.FIRESTORE_PROJECT_ID)
        db = firestore.Client(project="macanudo-479414", database="macanudo")
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
