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
    - Teachers: Can access ALL completed documents + their own processing documents
    - Students: Can access ALL completed documents uploaded by ANY teacher + their own documents
    
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
    
    # Teachers can access ALL completed documents + their own processing documents
    if role == "teacher":
        cursor = db.content.find(
            {
                "$or": [
                    {"status": "completed"},  # All completed documents
                    {"user_id": user_id, "status": {"$in": ["processing", "pending"]}}  # Own processing docs
                ]
            },
            {"content_id": 1}
        )
        docs = await cursor.to_list(length=None)
        doc_ids = [doc["content_id"] for doc in docs]
        logger.info(f"Teacher access: {len(doc_ids)} documents (completed + own processing)")
        return doc_ids
    
    # Students can access: ALL documents uploaded by ANY teacher + their own documents
    # Get all teacher user IDs
    teachers = await db.users.find({"role": "teacher"}, {"user_id": 1}).to_list(length=None)
    teacher_ids = [t["user_id"] for t in teachers] if teachers else []
    
    # Students get ALL completed documents uploaded by teachers + their own documents (any status)
    cursor = db.content.find(
        {
            "$or": [
                {"user_id": user_id},  # Owned by student (any status)
                {"upload_history.user_id": user_id},  # Student uploaded (any status)
                {"user_id": {"$in": teacher_ids}, "status": "completed"},  # Uploaded by any teacher (completed only)
                {"original_uploader_id": {"$in": teacher_ids}, "status": "completed"},  # Originally by teacher (completed only)
                {"shared_with.user_id": user_id}  # Explicitly shared
            ]
        },
        {"content_id": 1}
    )
    
    docs = await cursor.to_list(length=None)
    doc_ids = [doc["content_id"] for doc in docs]
    logger.info(f"Student access: {len(doc_ids)} documents (all teacher docs + own docs, {len(teacher_ids)} teacher(s))")
    
    # Add debug logging when no documents found
    if len(doc_ids) == 0:
        logger.warning(f"[DEBUG] No documents found for student {user_id}. Checking all statuses...")
        all_docs = await db.content.find(
            {"user_id": user_id},
            {"content_id": 1, "status": 1, "filename": 1, "metadata.title": 1}
        ).to_list(length=10)
        logger.warning(f"[DEBUG] Student {user_id} has {len(all_docs)} total documents (any status):")
        for doc in all_docs:
            logger.warning(f"  - {doc.get('metadata', {}).get('title', doc.get('filename', 'Unknown'))}: status={doc.get('status', 'unknown')}")
    
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


async def get_completed_docs_for_search(doc_ids: List[str]) -> List[str]:
    """
    Filter document IDs to only include completed documents (ready for search).
    
    Args:
        doc_ids: List of document IDs to filter
    
    Returns:
        List of completed document IDs ready for vector search
    """
    if not doc_ids:
        return []
    
    db = mongodb_client.get_database()
    completed_docs = await db.content.find(
        {
            "content_id": {"$in": doc_ids},
            "status": "completed"
        },
        {"content_id": 1}
    ).to_list(length=None)
    
    completed_ids = [doc["content_id"] for doc in completed_docs]
    
    if len(completed_ids) < len(doc_ids):
        processing_count = len(doc_ids) - len(completed_ids)
        logger.info(f"Filtered {len(doc_ids)} docs to {len(completed_ids)} completed (excluding {processing_count} processing)")
    
    return completed_ids

