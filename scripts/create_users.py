"""
Create Users Script - Populate system with superhero-themed teachers and students.

This script creates:
- 5 Teachers (mix of MCU and DC characters)
- 10 Students (mix of MCU and DC characters)
- All users have password: TestPass@123

Usage:
    python scripts/create_users.py
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from shared.utils.security import password_hasher
from shared.logging.logger import get_logger
from shared.config.settings import settings

logger = get_logger("create_users")


# User data
TEACHERS = [
    {"full_name": "Tony Stark", "email": "tony.stark@edtech.com"},  # Iron Man - MCU
    {"full_name": "Bruce Wayne", "email": "bruce.wayne@edtech.com"},  # Batman - DC
    {"full_name": "Diana Prince", "email": "diana.prince@edtech.com"},  # Wonder Woman - DC
    {"full_name": "Steve Rogers", "email": "steve.rogers@edtech.com"},  # Captain America - MCU
    {"full_name": "Clark Kent", "email": "clark.kent@edtech.com"},  # Superman - DC
]

STUDENTS = [
    {"full_name": "Peter Parker", "email": "peter.parker@edtech.com"},  # Spider-Man - MCU
    {"full_name": "Barry Allen", "email": "barry.allen@edtech.com"},  # The Flash - DC
    {"full_name": "Natasha Romanoff", "email": "natasha.romanoff@edtech.com"},  # Black Widow - MCU
    {"full_name": "Arthur Curry", "email": "arthur.curry@edtech.com"},  # Aquaman - DC
    {"full_name": "Wanda Maximoff", "email": "wanda.maximoff@edtech.com"},  # Scarlet Witch - MCU
    {"full_name": "Hal Jordan", "email": "hal.jordan@edtech.com"},  # Green Lantern - DC
    {"full_name": "T'Challa", "email": "tchalla@edtech.com"},  # Black Panther - MCU
    {"full_name": "Oliver Queen", "email": "oliver.queen@edtech.com"},  # Green Arrow - DC
    {"full_name": "Carol Danvers", "email": "carol.danvers@edtech.com"},  # Captain Marvel - MCU
    {"full_name": "Victor Stone", "email": "victor.stone@edtech.com"},  # Cyborg - DC
]

PASSWORD = "TestPass@123"


class UserCreator:
    """Create users in the system."""
    
    def __init__(self):
        self.mongo_client = None
        self.db = None
        self.created_users = []
    
    async def connect(self):
        """Connect to MongoDB."""
        logger.info("Connecting to MongoDB...")
        self.mongo_client = AsyncIOMotorClient(settings.mongodb_url)
        self.db = self.mongo_client[settings.mongodb_database]
        await self.mongo_client.admin.command('ping')
        logger.info("Connected to MongoDB")
    
    async def create_user(self, full_name: str, email: str, role: str):
        """
        Create a single user.
        
        Args:
            full_name: User's full name
            email: User's email
            role: User role (teacher or student)
        
        Returns:
            Created user document
        """
        # Hash password
        password_hash = password_hasher.hash_password(PASSWORD)
        
        # Create user document
        user_doc = {
            "user_id": str(uuid4()),
            "email": email,
            "full_name": full_name,
            "role": role,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "is_active": True,
            "metadata": {}
        }
        
        # Insert into database
        await self.db.users.insert_one(user_doc)
        
        logger.info(f"Created {role}: {full_name} ({email})")
        
        # Return without password hash
        user_doc.pop('password_hash')
        return user_doc
    
    async def create_all_users(self):
        """Create all teachers and students."""
        logger.info("=" * 60)
        logger.info("CREATING USERS")
        logger.info("=" * 60)
        
        # Create teachers
        logger.info("\nCreating Teachers:")
        logger.info("-" * 40)
        for teacher_data in TEACHERS:
            user = await self.create_user(
                full_name=teacher_data["full_name"],
                email=teacher_data["email"],
                role="teacher"
            )
            self.created_users.append(user)
        
        # Create students
        logger.info("\nCreating Students:")
        logger.info("-" * 40)
        for student_data in STUDENTS:
            user = await self.create_user(
                full_name=student_data["full_name"],
                email=student_data["email"],
                role="student"
            )
            self.created_users.append(user)
        
        logger.info("\n" + "=" * 60)
        logger.info("USER CREATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total users created: {len(self.created_users)}")
        logger.info(f"Teachers: {len(TEACHERS)}")
        logger.info(f"Students: {len(STUDENTS)}")
        logger.info(f"Password for all users: {PASSWORD}")
        logger.info("=" * 60)
        
        # Print user credentials table
        logger.info("\n" + "=" * 60)
        logger.info("USER CREDENTIALS")
        logger.info("=" * 60)
        logger.info(f"{'Role':<10} | {'Full Name':<25} | {'Email':<35}")
        logger.info("-" * 60)
        for user in self.created_users:
            logger.info(f"{user['role']:<10} | {user['full_name']:<25} | {user['email']:<35}")
        logger.info("=" * 60)
        logger.info(f"Password for all: {PASSWORD}")
        logger.info("=" * 60)
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("Disconnected from MongoDB")
    
    async def execute(self):
        """Execute user creation."""
        try:
            await self.connect()
            await self.create_all_users()
        except Exception as e:
            logger.error(f"User creation failed: {e}", exc_info=True)
            raise
        finally:
            await self.disconnect()


async def main():
    """Main entry point."""
    creator = UserCreator()
    await creator.execute()


if __name__ == "__main__":
    asyncio.run(main())

