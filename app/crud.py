from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, ItemUpdate, User, UserCreate, UserUpdate


async def create_user(db: AsyncIOMotorDatabase, user_create: UserCreate) -> User:
    """Create new user."""
    user_dict = user_create.model_dump(exclude={"password"})
    user_dict["hashed_password"] = get_password_hash(user_create.password)

    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id

    return User(**user_dict)


async def update_user(
    db: AsyncIOMotorDatabase, user_id: str, user_in: UserUpdate
) -> User | None:
    """Update user."""
    update_data = user_in.model_dump(exclude_unset=True, exclude={"password"})

    if user_in.password:
        update_data["hashed_password"] = get_password_hash(user_in.password)

    if update_data:
        update_data["updated_at"] = user_in.updated_at
        await db.users.update_one(
            {"_id": ObjectId(user_id)}, {"$set": update_data}
        )

    return await get_user_by_id(db, user_id)


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> User | None:
    """Get user by email."""
    user_dict = await db.users.find_one({"email": email})
    if user_dict:
        return User(**user_dict)
    return None


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> User | None:
    """Get user by ID."""
    user_dict = await db.users.find_one({"_id": ObjectId(user_id)})
    if user_dict:
        return User(**user_dict)
    return None


async def authenticate(db: AsyncIOMotorDatabase, email: str, password: str) -> User | None:
    """Authenticate user."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
