"""
MongoDB client with connection pooling, retry logic, and error handling.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, OperationFailure
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from shared.exceptions.custom_exceptions import DatabaseError
from shared.logging.logger import get_logger

logger = get_logger("mongodb_client")


class MongoDBClient:
    """MongoDB client wrapper with connection management."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._connection_string: Optional[str] = None
        self._database_name: Optional[str] = None
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionFailure, OperationFailure)),
        reraise=True
    )
    async def connect(self, connection_string: str, database_name: str):
        """
        Connect to MongoDB with retry logic.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Database name
        """
        try:
            self._connection_string = connection_string
            self._database_name = database_name
            
            self.client = AsyncIOMotorClient(
                connection_string,
                maxPoolSize=100,
                minPoolSize=10,
                serverSelectionTimeoutMS=5000,
                retryWrites=True,
                retryReads=True
            )
            
            # Verify connection
            await self.client.admin.command('ping')
            
            self.db = self.client[database_name]
            
            logger.info(f"Connected to MongoDB database: {database_name}")
            
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise DatabaseError(f"Failed to connect to MongoDB: {str(e)}")
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def health_check(self) -> bool:
        """
        Check if MongoDB connection is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {str(e)}")
            return False
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """
        Get database instance.
        
        Returns:
            Database instance
        
        Raises:
            DatabaseError: If not connected
        """
        if self.db is None:
            raise DatabaseError("Not connected to MongoDB")
        return self.db
    
    def get_collection(self, collection_name: str):
        """
        Get collection instance.
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            Collection instance
        """
        return self.get_database()[collection_name]


# Global MongoDB client instance
mongodb_client = MongoDBClient()


async def get_mongodb() -> AsyncIOMotorDatabase:
    """
    Dependency for FastAPI routes.
    
    Returns:
        MongoDB database instance
    """
    return mongodb_client.get_database()

