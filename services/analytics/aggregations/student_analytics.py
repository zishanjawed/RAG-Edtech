"""
MongoDB aggregations for student analytics.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from shared.logging.logger import get_logger

logger = get_logger("student_analytics")


class StudentAnalytics:
    """Student engagement analytics."""
    
    @staticmethod
    async def get_student_engagement(db, student_id: str) -> Dict[str, Any]:
        """
        Get engagement metrics for a student.
        
        Args:
            db: MongoDB database instance
            student_id: Student ID
        
        Returns:
            Engagement metrics
        """
        # Total questions asked
        total_questions = await db.questions.count_documents({"student_id": student_id})
        
        # Questions in last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_questions_7d = await db.questions.count_documents({
            "student_id": student_id,
            "timestamp": {"$gte": seven_days_ago}
        })
        
        # Average response time
        pipeline = [
            {"$match": {"student_id": student_id}},
            {"$group": {
                "_id": None,
                "avg_response_time": {"$avg": "$response_time_ms"},
                "total_tokens": {"$sum": "$tokens_used.total"}
            }}
        ]
        
        agg_result = await db.questions.aggregate(pipeline).to_list(1)
        avg_response_time = agg_result[0]['avg_response_time'] if agg_result else 0
        total_tokens = agg_result[0].get('total_tokens', 0) if agg_result else 0
        
        # Unique content accessed
        unique_content_cursor = db.questions.distinct("content_id", {"student_id": student_id})
        unique_content_list = await unique_content_cursor
        unique_content_accessed = len(unique_content_list)
        
        # First and last activity
        first_question = await db.questions.find_one(
            {"student_id": student_id},
            sort=[("timestamp", 1)]
        )
        last_question = await db.questions.find_one(
            {"student_id": student_id},
            sort=[("timestamp", -1)]
        )
        
        first_activity = first_question['timestamp'].isoformat() if first_question else None
        last_activity = last_question['timestamp'].isoformat() if last_question else datetime.utcnow().isoformat()
        
        # Recent questions
        recent_questions_cursor = db.questions.find(
            {"student_id": student_id},
            {"_id": 1, "content_id": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(5)
        recent_questions_list = await recent_questions_cursor.to_list(5)
        
        recent_questions = [
            {
                "question_id": str(q['_id']),
                "content_id": q['content_id'],
                "timestamp": q['timestamp'].isoformat()
            }
            for q in recent_questions_list
        ]
        
        # Questions by content (for backward compatibility)
        pipeline = [
            {"$match": {"student_id": student_id}},
            {"$group": {
                "_id": "$content_id",
                "question_count": {"$sum": 1}
            }},
            {"$sort": {"question_count": -1}},
            {"$limit": 5}
        ]
        
        top_content = await db.questions.aggregate(pipeline).to_list(5)
        
        # Activity by day (last 7 days)
        pipeline = [
            {"$match": {
                "student_id": student_id,
                "timestamp": {"$gte": seven_days_ago}
            }},
            {"$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        daily_activity = await db.questions.aggregate(pipeline).to_list(7)
        
        return {
            "student_id": student_id,
            "total_questions": total_questions,
            "unique_content_accessed": unique_content_accessed,
            "avg_response_time_ms": int(avg_response_time) if avg_response_time else 0,
            "first_activity": first_activity,
            "last_activity": last_activity,
            "recent_questions": recent_questions,
            # Legacy fields for backward compatibility
            "recent_questions_7d": recent_questions_7d,
            "total_tokens_used": total_tokens,
            "top_content": [
                {
                    "content_id": item['_id'],
                    "question_count": item['question_count']
                }
                for item in top_content
            ],
            "daily_activity": [
                {
                    "date": item['_id'],
                    "questions": item['count']
                }
                for item in daily_activity
            ]
        }

