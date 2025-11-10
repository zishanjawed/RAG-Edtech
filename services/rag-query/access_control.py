"""
Access control helper for document permissions.
Determines which documents a user can access.
"""
from typing import List
from shared.database.mongodb_client import mongodb_client
from shared.logging.logger import get_logger

logger = get_logger("access_control")


async def get_user_accessible_docs(user_id: str, role: str = None) -> List[str]:
    """
    Get all document IDs accessible to a user.
    
    Access Rules:
    - Teachers: Can access ALL completed documents in the system
    - Students: Can access documents they own OR appear in upload_history
    
    Args:
        user_id: User ID
        role: User role (student/teacher) - if None, will be fetched
    
    Returns:
        List of content_ids user can access
    """
    db = mongodb_client.get_database()
    
    # Get user role if not provided
    if not role:
        user = await db.users.find_one({"user_id": user_id})
        role = user.get("role", "student") if user else "student"
    
    logger.info(f"Getting accessible documents for user {user_id} (role: {role})")
    
    # Teachers can access ALL completed documents
    if role == "teacher":
        cursor = db.content.find(
            {"status": "completed"},
            {"content_id": 1}
        )
        docs = await cursor.to_list(length=None)
        doc_ids = [doc["content_id"] for doc in docs]
        logger.info(f"Teacher access: {len(doc_ids)} documents")
        return doc_ids
    
    # Students can access: owned OR in upload_history OR explicitly shared
    cursor = db.content.find(
        {
            "$or": [
                {"user_id": user_id},
                {"upload_history.user_id": user_id},
                {"shared_with.user_id": user_id}  # Future feature
            ],
            "status": "completed"
        },
        {"content_id": 1}
    )
    
    docs = await cursor.to_list(length=None)
    doc_ids = [doc["content_id"] for doc in docs]
    logger.info(f"Student access: {len(doc_ids)} documents")
    return doc_ids


async def check_document_access(user_id: str, content_id: str, role: str = None) -> bool:
    """
    Check if a user has access to a specific document.
    
    Args:
        user_id: User ID
        content_id: Document ID
        role: User role (optional)
    
    Returns:
        True if user has access, False otherwise
    """
    accessible_docs = await get_user_accessible_docs(user_id, role)
    return content_id in accessible_docs


async def filter_accessible_docs(user_id: str, doc_ids: List[str], role: str = None) -> List[str]:
    """
    Filter a list of document IDs to only those accessible to the user.
    
    Args:
        user_id: User ID
        doc_ids: List of document IDs to filter
        role: User role (optional)
    
    Returns:
        Filtered list of accessible document IDs
    """
    if not doc_ids:
        return []
    
    accessible = await get_user_accessible_docs(user_id, role)
    filtered = [doc_id for doc_id in doc_ids if doc_id in accessible]
    
    logger.info(f"Filtered {len(doc_ids)} to {len(filtered)} accessible documents for user {user_id}")
    return filtered

