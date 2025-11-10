"""
Document deletion service - Complete removal from all systems.
"""
import os
from pathlib import Path
from typing import Optional
from shared.database.mongodb_client import mongodb_client
from shared.database.redis_client import redis_client
from shared.logging.logger import get_logger

logger = get_logger("deletion_service")


class DocumentDeletionService:
    """Handle complete document deletion across all systems."""
    
    @staticmethod
    async def delete_document_complete(
        content_id: str,
        pinecone_client: Optional[any] = None
    ) -> dict:
        """
        Completely delete a document from all systems.
        
        Args:
            content_id: Content ID to delete
            pinecone_client: Optional Pinecone client for vector deletion
        
        Returns:
            Deletion statistics
        """
        stats = {
            "mongodb_deleted": False,
            "vectors_deleted": False,
            "file_deleted": False,
            "cache_cleared": False,
            "questions_affected": 0
        }
        
        try:
            db = mongodb_client.get_database()
            
            # 1. Get document metadata before deletion
            content_doc = await db.content.find_one({"content_id": content_id})
            
            if not content_doc:
                logger.warning(f"Document {content_id} not found in MongoDB")
                return stats
            
            filename = content_doc.get('filename', '')
            logger.info(f"Deleting document: {filename} ({content_id})")
            
            # 2. Delete from MongoDB
            result = await db.content.delete_one({"content_id": content_id})
            stats["mongodb_deleted"] = result.deleted_count > 0
            logger.info(f"Deleted from MongoDB: {stats['mongodb_deleted']}")
            
            # 3. Delete vectors from Pinecone (entire namespace)
            if pinecone_client:
                try:
                    pinecone_client.delete_namespace(content_id)
                    stats["vectors_deleted"] = True
                    logger.info(f"Deleted Pinecone namespace: {content_id}")
                except Exception as e:
                    logger.error(f"Failed to delete Pinecone namespace: {e}")
            
            # 4. Delete physical file
            try:
                # Determine file path (adjust based on your upload directory structure)
                uploads_dir = Path(__file__).parent.parent.parent / "uploads"
                file_path = uploads_dir / filename
                
                if file_path.exists():
                    os.remove(file_path)
                    stats["file_deleted"] = True
                    logger.info(f"Deleted physical file: {filename}")
                else:
                    logger.warning(f"Physical file not found: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete physical file: {e}")
            
            # 5. Clear Redis cache entries
            if redis_client.client:
                try:
                    # Delete all cache keys related to this content
                    pattern = f"rag:cache:*{content_id}*"
                    deleted_count = 0
                    
                    async for key in redis_client.client.scan_iter(match=pattern):
                        await redis_client.client.delete(key)
                        deleted_count += 1
                    
                    stats["cache_cleared"] = deleted_count > 0
                    logger.info(f"Cleared {deleted_count} cache entries")
                except Exception as e:
                    logger.error(f"Failed to clear cache: {e}")
            
            # 6. Handle related questions (mark as orphaned or delete)
            try:
                # Count affected questions
                question_count = await db.questions.count_documents({"content_id": content_id})
                stats["questions_affected"] = question_count
                
                # Option 1: Delete questions (chosen approach)
                result = await db.questions.delete_many({"content_id": content_id})
                logger.info(f"Deleted {result.deleted_count} related questions")
                
                # Option 2: Mark as orphaned (alternative)
                # await db.questions.update_many(
                #     {"content_id": content_id},
                #     {"$set": {"content_deleted": True, "deleted_at": datetime.utcnow()}}
                # )
                
            except Exception as e:
                logger.error(f"Failed to handle related questions: {e}")
            
            logger.info(f"Document deletion completed: {content_id}")
            logger.info(f"Deletion stats: {stats}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Document deletion failed: {e}", exc_info=True)
            raise


# Global instance
deletion_service = DocumentDeletionService()

