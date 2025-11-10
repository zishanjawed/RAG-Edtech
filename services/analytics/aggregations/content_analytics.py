"""
MongoDB aggregations for content analytics.
"""
from typing import Dict, Any, List
from shared.logging.logger import get_logger

logger = get_logger("content_analytics")


class ContentAnalytics:
    """Content usage analytics."""
    
    @staticmethod
    async def get_question_type_stats(db, content_id: str) -> Dict[str, Any]:
        """
        Get question type distribution for content.
        
        Args:
            db: MongoDB database instance
            content_id: Content ID
        
        Returns:
            Question type statistics
        """
        pipeline = [
            {"$match": {"content_id": content_id}},
            {"$group": {
                "_id": "$question_type",
                "count": {"$sum": 1},
                "avg_response_time": {"$avg": "$response_time_ms"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = await db.questions.aggregate(pipeline).to_list(10)
        
        total = sum(r['count'] for r in results)
        
        return {
            "content_id": content_id,
            "total_questions": total,
            "question_types": [
                {
                    "type": r['_id'] if r['_id'] else "general",
                    "count": r['count'],
                    "percentage": round((r['count'] / total * 100), 2) if total > 0 else 0,
                    "avg_response_time_ms": int(r.get('avg_response_time', 0) or 0)
                }
                for r in results
            ]
        }
    
    
    @staticmethod
    async def get_content_questions(db, content_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all questions asked about a content.
        
        Args:
            db: MongoDB database instance
            content_id: Content ID
            limit: Maximum number of questions to return
        
        Returns:
            List of questions
        """
        questions = await db.questions.find(
            {"content_id": content_id},
            {"_id": 0, "question_id": 1, "student_id": 1, "question_text": 1, "timestamp": 1, "response_time_ms": 1}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return questions
    
    @staticmethod
    async def get_content_stats(db, content_id: str) -> Dict[str, Any]:
        """
        Get statistics for a content.
        
        Args:
            db: MongoDB database instance
            content_id: Content ID
        
        Returns:
            Content statistics
        """
        # Total questions
        total_questions = await db.questions.count_documents({"content_id": content_id})
        
        # Unique students
        pipeline = [
            {"$match": {"content_id": content_id}},
            {"$group": {"_id": "$student_id"}},
            {"$count": "unique_students"}
        ]
        
        unique_result = await db.questions.aggregate(pipeline).to_list(1)
        unique_students = unique_result[0]['unique_students'] if unique_result else 0
        
        # Average response time
        pipeline = [
            {"$match": {"content_id": content_id}},
            {"$group": {
                "_id": None,
                "avg_response_time": {"$avg": "$response_time_ms"}
            }}
        ]
        
        avg_result = await db.questions.aggregate(pipeline).to_list(1)
        avg_response_time = avg_result[0]['avg_response_time'] if avg_result else 0
        
        # Most common question topics (extract key phrases)
        # Simplified: just get most recent questions
        recent_questions = await db.questions.find(
            {"content_id": content_id},
            {"question_text": 1}
        ).limit(10).to_list(10)
        
        question_samples = [q['question_text'] for q in recent_questions]
        
        # Cache hit rate
        pipeline = [
            {"$match": {"content_id": content_id}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "cached": {"$sum": {"$cond": ["$cached", 1, 0]}}
            }}
        ]
        
        cache_result = await db.questions.aggregate(pipeline).to_list(1)
        cache_hit_rate = 0
        if cache_result:
            total = cache_result[0]['total']
            cached = cache_result[0]['cached']
            cache_hit_rate = (cached / total * 100) if total > 0 else 0
        
        return {
            "content_id": content_id,
            "total_questions": total_questions,
            "unique_students": unique_students,
            "avg_response_time_ms": int(avg_response_time) if avg_response_time else 0,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "question_samples": question_samples
        }

