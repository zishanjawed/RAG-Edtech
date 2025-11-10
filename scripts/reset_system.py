"""
System Reset Script - Delete all users, documents, questions, vectors, and files.

This script provides a complete system reset with safety checks and dry-run mode.

Usage:
    python scripts/reset_system.py --dry-run  # Preview what will be deleted
    python scripts/reset_system.py --confirm  # Actually perform deletion
"""
import asyncio
import os
import sys
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from pinecone import Pinecone
import redis.asyncio as redis
from shared.logging.logger import get_logger
from shared.config.settings import settings

logger = get_logger("reset_system")


class SystemReset:
    """Handle complete system reset."""
    
    def __init__(self, dry_run: bool = True):
        """
        Initialize system reset.
        
        Args:
            dry_run: If True, only preview changes without actually deleting
        """
        self.dry_run = dry_run
        self.mongo_client = None
        self.redis_client = None
        self.pinecone_client = None
        self.stats = {
            "users_deleted": 0,
            "documents_deleted": 0,
            "questions_deleted": 0,
            "vectors_deleted": 0,
            "files_deleted": 0,
            "cache_keys_deleted": 0
        }
    
    async def connect_databases(self):
        """Connect to all databases."""
        logger.info("Connecting to databases...")
        
        # MongoDB
        self.mongo_client = AsyncIOMotorClient(settings.mongodb_url)
        self.db = self.mongo_client[settings.mongodb_database]
        await self.mongo_client.admin.command('ping')
        logger.info("Connected to MongoDB")
        
        # Redis
        if settings.redis_url:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        
        # Pinecone
        if settings.pinecone_api_key:
            self.pinecone_client = Pinecone(api_key=settings.pinecone_api_key)
            self.pinecone_index = self.pinecone_client.Index(settings.pinecone_index_name)
            logger.info(f"Connected to Pinecone index: {settings.pinecone_index_name}")
    
    async def delete_users(self):
        """Delete all users from MongoDB."""
        logger.info("Deleting users...")
        
        # Count users
        user_count = await self.db.users.count_documents({})
        logger.info(f"Found {user_count} users to delete")
        self.stats["users_deleted"] = user_count
        
        if not self.dry_run:
            result = await self.db.users.delete_many({})
            logger.info(f"Deleted {result.deleted_count} users")
        else:
            logger.info(f"[DRY RUN] Would delete {user_count} users")
    
    async def delete_questions(self):
        """Delete all questions from MongoDB."""
        logger.info("Deleting questions...")
        
        # Count questions
        question_count = await self.db.questions.count_documents({})
        logger.info(f"Found {question_count} questions to delete")
        self.stats["questions_deleted"] = question_count
        
        if not self.dry_run:
            result = await self.db.questions.delete_many({})
            logger.info(f"Deleted {result.deleted_count} questions")
        else:
            logger.info(f"[DRY RUN] Would delete {question_count} questions")
    
    async def delete_documents(self):
        """Delete all documents from MongoDB."""
        logger.info("Deleting documents...")
        
        # Get all content_ids for Pinecone cleanup
        documents = []
        async for doc in self.db.content.find({}):
            documents.append(doc)
        
        doc_count = len(documents)
        logger.info(f"Found {doc_count} documents to delete")
        self.stats["documents_deleted"] = doc_count
        
        if not self.dry_run:
            result = await self.db.content.delete_many({})
            logger.info(f"Deleted {result.deleted_count} documents from MongoDB")
        else:
            logger.info(f"[DRY RUN] Would delete {doc_count} documents from MongoDB")
        
        return [doc.get('content_id') for doc in documents if doc.get('content_id')]
    
    async def delete_vectors(self, content_ids: list):
        """Delete all vectors from Pinecone."""
        if not self.pinecone_client:
            logger.warning("Pinecone not configured, skipping vector deletion")
            return
        
        logger.info(f"Deleting vectors from Pinecone for {len(content_ids)} documents...")
        
        vectors_deleted = 0
        for content_id in content_ids:
            try:
                if not self.dry_run:
                    # Delete all vectors in the namespace
                    self.pinecone_index.delete(delete_all=True, namespace=content_id)
                    logger.info(f"Deleted vectors for namespace: {content_id}")
                    vectors_deleted += 1
                else:
                    logger.info(f"[DRY RUN] Would delete vectors for namespace: {content_id}")
                    vectors_deleted += 1
            except Exception as e:
                logger.error(f"Failed to delete vectors for {content_id}: {e}")
        
        self.stats["vectors_deleted"] = vectors_deleted
        logger.info(f"Deleted vectors from {vectors_deleted} namespaces")
    
    async def clear_cache(self):
        """Clear all cache entries from Redis."""
        if not self.redis_client:
            logger.warning("Redis not configured, skipping cache cleanup")
            return
        
        logger.info("Clearing cache from Redis...")
        
        try:
            # Find all RAG cache keys
            cache_patterns = [
                "rag:cache:*",
                "analytics:*",
                "rate_limit:*"
            ]
            
            total_deleted = 0
            for pattern in cache_patterns:
                keys = []
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys.append(key)
                
                logger.info(f"Found {len(keys)} keys matching pattern: {pattern}")
                total_deleted += len(keys)
                
                if not self.dry_run and keys:
                    await self.redis_client.delete(*keys)
                    logger.info(f"Deleted {len(keys)} keys")
                else:
                    logger.info(f"[DRY RUN] Would delete {len(keys)} keys")
            
            self.stats["cache_keys_deleted"] = total_deleted
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def delete_upload_files(self):
        """Delete all files from uploads directory."""
        logger.info("Deleting upload files...")
        
        uploads_dir = Path(__file__).parent.parent / "uploads"
        
        if not uploads_dir.exists():
            logger.info("Uploads directory does not exist")
            return
        
        files_deleted = 0
        for item in uploads_dir.iterdir():
            if item.is_file():
                files_deleted += 1
                if not self.dry_run:
                    item.unlink()
                    logger.info(f"Deleted file: {item.name}")
                else:
                    logger.info(f"[DRY RUN] Would delete file: {item.name}")
            elif item.is_dir() and item.name != ".gitkeep":
                files_in_dir = len(list(item.rglob("*")))
                files_deleted += files_in_dir
                if not self.dry_run:
                    shutil.rmtree(item)
                    logger.info(f"Deleted directory: {item.name} ({files_in_dir} files)")
                else:
                    logger.info(f"[DRY RUN] Would delete directory: {item.name} ({files_in_dir} files)")
        
        self.stats["files_deleted"] = files_deleted
        logger.info(f"Deleted {files_deleted} files/directories")
    
    async def disconnect_databases(self):
        """Disconnect from all databases."""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("Disconnected from MongoDB")
        
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def execute(self):
        """Execute the complete reset."""
        try:
            mode = "DRY RUN" if self.dry_run else "EXECUTION"
            logger.info(f"=" * 60)
            logger.info(f"SYSTEM RESET - {mode} MODE")
            logger.info(f"=" * 60)
            
            # Connect
            await self.connect_databases()
            
            # Delete in order (questions first to avoid orphans)
            await self.delete_questions()
            content_ids = await self.delete_documents()
            await self.delete_vectors(content_ids)
            await self.delete_users()
            await self.clear_cache()
            self.delete_upload_files()
            
            # Disconnect
            await self.disconnect_databases()
            
            # Print summary
            logger.info(f"=" * 60)
            logger.info("RESET SUMMARY:")
            logger.info(f"=" * 60)
            logger.info(f"Users deleted: {self.stats['users_deleted']}")
            logger.info(f"Documents deleted: {self.stats['documents_deleted']}")
            logger.info(f"Questions deleted: {self.stats['questions_deleted']}")
            logger.info(f"Vector namespaces deleted: {self.stats['vectors_deleted']}")
            logger.info(f"Cache keys deleted: {self.stats['cache_keys_deleted']}")
            logger.info(f"Files deleted: {self.stats['files_deleted']}")
            logger.info(f"=" * 60)
            
            if self.dry_run:
                logger.info("This was a DRY RUN. No data was actually deleted.")
                logger.info("Run with --confirm to actually delete data.")
            else:
                logger.info("System reset completed successfully!")
            
        except Exception as e:
            logger.error(f"Reset failed: {e}", exc_info=True)
            raise
        finally:
            await self.disconnect_databases()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset the RAG Edtech system")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without actually deleting data"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually perform the deletion (DANGEROUS!)"
    )
    
    args = parser.parse_args()
    
    # Default to dry run unless confirm is specified
    dry_run = not args.confirm
    
    if not dry_run:
        print("\n" + "=" * 60)
        print("WARNING: You are about to DELETE ALL DATA from the system!")
        print("=" * 60)
        print("This will delete:")
        print("  - All users (teachers and students)")
        print("  - All documents and their metadata")
        print("  - All questions and answers")
        print("  - All vectors from Pinecone")
        print("  - All cache entries from Redis")
        print("  - All uploaded files")
        print("=" * 60)
        response = input("Type 'DELETE ALL DATA' to confirm: ")
        
        if response != "DELETE ALL DATA":
            print("Aborted. No data was deleted.")
            return
    
    # Execute reset
    reset = SystemReset(dry_run=dry_run)
    await reset.execute()


if __name__ == "__main__":
    asyncio.run(main())

