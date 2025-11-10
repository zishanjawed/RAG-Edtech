"""
Analytics Service - Student engagement and content analytics.
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from aggregations.student_analytics import StudentAnalytics
from aggregations.content_analytics import ContentAnalytics
from cache.redis_cache import AnalyticsCache
from models.schemas import StudentEngagement, ContentStats
from config import settings
from shared.database.mongodb_client import mongodb_client, get_mongodb
from shared.database.redis_client import redis_client
from shared.middleware.error_handler import register_exception_handlers
from shared.logging.logger import get_logger

logger = get_logger(settings.service_name, settings.log_level)

# Create FastAPI app
app = FastAPI(
    title="RAG Edtech - Analytics Service",
    description="Student engagement and content analytics service",
    version="1.0.0"
)

# Add CORS middleware (centralized configuration)
from shared.middleware.cors_config import configure_cors
configure_cors(app, settings.cors_origins)

# Register exception handlers
register_exception_handlers(app)

# Initialize cache
analytics_cache = AnalyticsCache(ttl_seconds=settings.cache_ttl_seconds)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    logger.info("Starting Analytics Service...")
    
    # Connect to MongoDB
    await mongodb_client.connect(
        settings.mongodb_url,
        settings.mongodb_database
    )
    
    # Connect to Redis
    await redis_client.connect(settings.redis_url)
    
    logger.info("Analytics Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Analytics Service...")
    await mongodb_client.disconnect()
    await redis_client.disconnect()
    logger.info("Analytics Service shut down successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    mongo_healthy = await mongodb_client.health_check()
    redis_healthy = await redis_client.health_check()
    
    return {
        "status": "healthy" if (mongo_healthy and redis_healthy) else "degraded",
        "service": "analytics-service",
        "mongodb": "connected" if mongo_healthy else "disconnected",
        "redis": "connected" if redis_healthy else "disconnected"
    }


@app.get("/api/analytics/student/{student_id}", response_model=StudentEngagement)
async def get_student_analytics(student_id: str, db=Depends(get_mongodb)):
    """
    Get analytics for a student.
    
    Args:
        student_id: Student ID
        db: MongoDB database instance
    
    Returns:
        Student engagement metrics
    """
    logger.info(f"Fetching analytics for student {student_id}")
    
    # Check cache
    cache_key = f"student:{student_id}"
    cached = await analytics_cache.get(cache_key)
    
    if cached:
        logger.info("Returning cached analytics")
        return StudentEngagement(**cached)
    
    # Calculate analytics
    analytics = await StudentAnalytics.get_student_engagement(db, student_id)
    
    # Cache result
    await analytics_cache.set(cache_key, analytics)
    
    return StudentEngagement(**analytics)


@app.get("/api/content/{content_id}/questions")
async def get_content_questions(content_id: str, limit: int = 50, db=Depends(get_mongodb)):
    """
    Get all questions asked about a content.
    
    Args:
        content_id: Content ID
        limit: Maximum number of questions
        db: MongoDB database instance
    
    Returns:
        List of questions
    """
    logger.info(f"Fetching questions for content {content_id}")
    
    questions = await ContentAnalytics.get_content_questions(db, content_id, limit)
    
    return {
        "content_id": content_id,
        "questions": questions,
        "total": len(questions)
    }


@app.get("/api/content/{content_id}/question-types")
async def get_question_types(content_id: str, db=Depends(get_mongodb)):
    """
    Get question type distribution for content.
    
    Args:
        content_id: Content ID
        db: MongoDB database instance
    
    Returns:
        Question type statistics
    """
    logger.info(f"Getting question type stats for content: {content_id}")
    
    stats = await ContentAnalytics.get_question_type_stats(db, content_id)
    
    return stats


@app.get("/api/content/{content_id}/stats", response_model=ContentStats)
async def get_content_stats(content_id: str, db=Depends(get_mongodb)):
    """
    Get statistics for a content.
    
    Args:
        content_id: Content ID
        db: MongoDB database instance
    
    Returns:
        Content statistics
    """
    logger.info(f"Fetching stats for content {content_id}")
    
    # Check cache
    cache_key = f"content:{content_id}:stats"
    cached = await analytics_cache.get(cache_key)
    
    if cached:
        logger.info("Returning cached stats")
        return ContentStats(**cached)
    
    # Calculate stats
    stats = await ContentAnalytics.get_content_stats(db, content_id)
    
    # Cache result
    await analytics_cache.set(cache_key, stats)
    
    return ContentStats(**stats)


# ============================================================================
# TEACHER DASHBOARD ENDPOINTS
# ============================================================================

@app.get("/api/analytics/teacher/overview")
async def get_teacher_overview(
    teacher_id: str,
    db=Depends(get_mongodb)
):
    """
    Get overview dashboard for teacher.
    
    Returns:
        Overview metrics for all students
    """
    logger.info(f"Getting teacher overview for: {teacher_id}")
    
    # Get all students (in a real system, would filter by teacher)
    students_pipeline = [
        {"$group": {
            "_id": "$student_id",
            "total_questions": {"$sum": 1},
            "last_activity": {"$max": "$timestamp"}
        }},
        {"$lookup": {
            "from": "users",
            "localField": "_id",
            "foreignField": "user_id",
            "as": "user_info"
        }},
        {"$addFields": {
            "student_name": {"$arrayElemAt": ["$user_info.full_name", 0]},
            "student_email": {"$arrayElemAt": ["$user_info.email", 0]}
        }},
        {"$sort": {"last_activity": -1}},
        {"$limit": 100}
    ]
    
    students = await db.questions.aggregate(students_pipeline).to_list(100)
    
    # Remove ObjectIds and convert dates
    for student in students:
        if "_id" in student:
            del student["_id"]
        if "user_info" in student:
            del student["user_info"]  # Remove array with ObjectIds
        if "last_activity" in student and hasattr(student["last_activity"], "isoformat"):
            student["last_activity"] = student["last_activity"].isoformat()
        if "first_activity" in student and hasattr(student["first_activity"], "isoformat"):
            student["first_activity"] = student["first_activity"].isoformat()
    
    # Get overall stats
    total_questions = await db.questions.count_documents({})
    total_students = len(students)
    
    # Get content usage
    content_pipeline = [
        {"$group": {
            "_id": "$content_id",
            "question_count": {"$sum": 1},
            "unique_students": {"$addToSet": "$student_id"}
        }},
        {"$lookup": {
            "from": "content",
            "localField": "_id",
            "foreignField": "content_id",
            "as": "content_info"
        }},
        {"$project": {
            "content_id": "$_id",
            "content_title": {"$arrayElemAt": ["$content_info.metadata.title", 0]},
            "content_subject": {"$arrayElemAt": ["$content_info.metadata.subject", 0]},
            "question_count": 1,
            "student_count": {"$size": "$unique_students"}
        }},
        {"$sort": {"question_count": -1}},
        {"$limit": 10}
    ]
    
    top_contents = await db.questions.aggregate(content_pipeline).to_list(10)
    
    # Remove ObjectIds from content
    for content in top_contents:
        if "_id" in content:
            del content["_id"]
        if "content_info" in content:
            del content["content_info"]  # Remove array with ObjectIds
    
    return {
        "teacher_id": teacher_id,
        "overview": {
            "total_students": total_students,
            "total_questions": total_questions,
            "avg_questions_per_student": round(total_questions / total_students, 2) if total_students > 0 else 0
        },
        "top_contents": top_contents,
        "recent_students": students[:10]
    }


@app.get("/api/analytics/teacher/students")
async def get_all_students_activity(
    teacher_id: str,
    limit: int = 50,
    db=Depends(get_mongodb)
):
    """
    Get activity metrics for all students.
    
    Returns:
        List of students with activity metrics
    """
    logger.info(f"Getting student activity for teacher: {teacher_id}")
    
    pipeline = [
        {"$group": {
            "_id": "$student_id",
            "total_questions": {"$sum": 1},
            "unique_contents": {"$addToSet": "$content_id"},
            "avg_response_time": {"$avg": "$response_time_ms"},
            "last_activity": {"$max": "$timestamp"},
            "first_activity": {"$min": "$timestamp"}
        }},
        {"$lookup": {
            "from": "users",
            "localField": "_id",
            "foreignField": "user_id",
            "as": "user_info"
        }},
        {"$project": {
            "student_id": "$_id",
            "student_name": {"$arrayElemAt": ["$user_info.full_name", 0]},
            "student_email": {"$arrayElemAt": ["$user_info.email", 0]},
            "total_questions": 1,
            "unique_content": {"$size": "$unique_contents"},
            "avg_response_time": {"$round": ["$avg_response_time", 0]},
            "last_activity": 1,
            "first_activity": 1,
            "days_active": {
                "$round": [{
                    "$divide": [
                        {"$subtract": ["$last_activity", "$first_activity"]},
                        86400000  # Convert ms to days
                    ]
                }, 0]
            },
            "status": "active"  # Default to active for all students with activity
        }},
        {"$sort": {"last_activity": -1}},
        {"$limit": limit}
    ]
    
    students = await db.questions.aggregate(pipeline).to_list(limit)
    
    # Remove ObjectIds and convert dates
    for student in students:
        if "_id" in student:
            del student["_id"]
        if "user_info" in student:
            del student["user_info"]  # Remove array with ObjectIds
        if "last_activity" in student and hasattr(student["last_activity"], "isoformat"):
            student["last_activity"] = student["last_activity"].isoformat()
        if "first_activity" in student and hasattr(student["first_activity"], "isoformat"):
            student["first_activity"] = student["first_activity"].isoformat()
    
    return {
        "teacher_id": teacher_id,
        "students": students,
        "total_count": len(students)
    }


@app.get("/api/analytics/content/{content_id}/engagement")
async def get_content_engagement(
    content_id: str,
    db=Depends(get_mongodb)
):
    """
    Get engagement metrics for specific content.
    
    Returns:
        Detailed engagement analytics
    """
    logger.info(f"Getting engagement for content: {content_id}")
    
    # Question trends over time
    trends_pipeline = [
        {"$match": {"content_id": content_id}},
        {"$group": {
            "_id": {
                "$dateToString": {
                    "format": "%Y-%m-%d",
                    "date": "$timestamp"
                }
            },
            "question_count": {"$sum": 1},
            "unique_students": {"$addToSet": "$student_id"}
        }},
        {"$project": {
            "date": "$_id",
            "question_count": 1,
            "student_count": {"$size": "$unique_students"}
        }},
        {"$sort": {"date": 1}},
        {"$limit": 30}
    ]
    
    trends = await db.questions.aggregate(trends_pipeline).to_list(30)
    
    # Question type distribution
    type_stats = await ContentAnalytics.get_question_type_stats(db, content_id)
    
    # Student engagement levels
    student_pipeline = [
        {"$match": {"content_id": content_id}},
        {"$group": {
            "_id": "$student_id",
            "questions": {"$sum": 1},
            "avg_response_time": {"$avg": "$response_time_ms"}
        }},
        {"$sort": {"questions": -1}}
    ]
    
    student_engagement = await db.questions.aggregate(student_pipeline).to_list(100)
    
    # Categorize students by engagement
    high_engagement = len([s for s in student_engagement if s["questions"] >= 10])
    medium_engagement = len([s for s in student_engagement if 5 <= s["questions"] < 10])
    low_engagement = len([s for s in student_engagement if s["questions"] < 5])
    
    return {
        "content_id": content_id,
        "trends": trends,
        "question_types": type_stats.get("question_types", []),
        "engagement_levels": {
            "high": high_engagement,
            "medium": medium_engagement,
            "low": low_engagement
        },
        "top_students": student_engagement[:10]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

