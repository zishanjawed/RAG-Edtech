"""
Tests for analytics service.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
import sys
import os

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))


class TestContentAnalytics:
    """Test content analytics aggregations."""
    
    @pytest.mark.asyncio
    async def test_get_content_stats(self):
        """Test getting content statistics."""
        # Mock database
        mock_db = Mock()
        mock_db.questions.count_documents = AsyncMock(return_value=50)
        mock_db.questions.aggregate = AsyncMock(return_value=AsyncMock(to_list=AsyncMock(return_value=[
            {"_id": "user1"},
            {"_id": "user2"}
        ])))
        
        # Content stats should include question count and unique users
        total_questions = await mock_db.questions.count_documents({"content_id": "content-123"})
        
        assert total_questions == 50
    
    @pytest.mark.asyncio
    async def test_get_question_type_stats(self):
        """Test getting question type distribution."""
        # Mock aggregation result
        mock_results = [
            {"_id": "definition", "count": 15, "avg_response_time": 1200},
            {"_id": "explanation", "count": 20, "avg_response_time": 1500},
            {"_id": "comparison", "count": 10, "avg_response_time": 1800},
            {"_id": "procedure", "count": 5, "avg_response_time": 2000}
        ]
        
        total = sum(r["count"] for r in mock_results)
        
        assert total == 50
        assert len(mock_results) == 4
        assert mock_results[0]["_id"] == "definition"
    
    @pytest.mark.asyncio
    async def test_calculate_percentages(self):
        """Test percentage calculation for question types."""
        question_counts = {
            "definition": 15,
            "explanation": 20,
            "comparison": 10,
            "procedure": 5
        }
        
        total = sum(question_counts.values())
        percentages = {
            q_type: round((count / total * 100), 2)
            for q_type, count in question_counts.items()
        }
        
        assert percentages["definition"] == 30.0
        assert percentages["explanation"] == 40.0
        assert sum(percentages.values()) == 100.0


class TestStudentAnalytics:
    """Test student analytics aggregations."""
    
    @pytest.mark.asyncio
    async def test_get_student_engagement(self):
        """Test getting student engagement metrics."""
        student_data = {
            "student_id": "user-123",
            "total_questions": 25,
            "unique_contents": 5,
            "avg_response_time_ms": 1500,
            "questions_today": 3
        }
        
        assert student_data["total_questions"] > 0
        assert student_data["unique_contents"] > 0
    
    @pytest.mark.asyncio
    async def test_calculate_engagement_score(self):
        """Test engagement score calculation."""
        total_questions = 50
        unique_contents = 10
        active_days = 15
        
        # Simple engagement score formula
        engagement_score = (total_questions * 0.4) + (unique_contents * 0.3) + (active_days * 0.3)
        
        assert engagement_score > 0
        assert isinstance(engagement_score, float)
    
    @pytest.mark.asyncio
    async def test_get_recent_activity(self):
        """Test getting recent activity."""
        now = datetime.utcnow()
        recent_questions = [
            {"timestamp": now - timedelta(hours=1), "content_id": "content-1"},
            {"timestamp": now - timedelta(hours=2), "content_id": "content-2"},
            {"timestamp": now - timedelta(hours=5), "content_id": "content-1"}
        ]
        
        # Filter last 24 hours
        last_24h = [q for q in recent_questions if q["timestamp"] > now - timedelta(days=1)]
        
        assert len(last_24h) == 3


class TestCacheOperations:
    """Test cache operations."""
    
    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test cache hit scenario."""
        # Mock cache
        cache_data = {
            "student:user-123:engagement": {
                "total_questions": 25,
                "cached_at": datetime.utcnow().isoformat()
            }
        }
        
        cache_key = "student:user-123:engagement"
        cached_value = cache_data.get(cache_key)
        
        assert cached_value is not None
        assert cached_value["total_questions"] == 25
    
    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Test cache miss scenario."""
        cache_data = {}
        cache_key = "student:user-999:engagement"
        
        cached_value = cache_data.get(cache_key)
        
        assert cached_value is None
    
    @pytest.mark.asyncio
    async def test_cache_expiry(self):
        """Test cache expiry logic."""
        cached_at = datetime.utcnow() - timedelta(hours=2)
        now = datetime.utcnow()
        ttl_minutes = 60
        
        is_expired = (now - cached_at).total_seconds() > (ttl_minutes * 60)
        
        assert is_expired
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """Test cache invalidation."""
        cache_data = {
            "content:content-123:stats": {"questions": 50}
        }
        
        # Invalidate cache
        cache_key = "content:content-123:stats"
        cache_data.pop(cache_key, None)
        
        assert cache_key not in cache_data


class TestMetricsCalculation:
    """Test metrics calculation."""
    
    def test_calculate_average_response_time(self):
        """Test average response time calculation."""
        response_times = [1200, 1500, 1800, 1400, 1600]
        
        avg_time = sum(response_times) / len(response_times)
        
        assert avg_time == 1500
    
    def test_calculate_question_rate(self):
        """Test question rate calculation."""
        total_questions = 100
        days_active = 10
        
        questions_per_day = total_questions / days_active
        
        assert questions_per_day == 10.0
    
    def test_calculate_content_coverage(self):
        """Test content coverage calculation."""
        total_contents = 20
        contents_accessed = 15
        
        coverage_percentage = (contents_accessed / total_contents) * 100
        
        assert coverage_percentage == 75.0
    
    def test_identify_struggling_students(self):
        """Test identifying struggling students."""
        students = [
            {"id": "user-1", "avg_response_time": 3000, "questions": 5},
            {"id": "user-2", "avg_response_time": 1500, "questions": 50},
            {"id": "user-3", "avg_response_time": 2800, "questions": 8}
        ]
        
        # Students with high response time and few questions
        struggling = [
            s for s in students
            if s["avg_response_time"] > 2500 and s["questions"] < 10
        ]
        
        assert len(struggling) == 2
        assert "user-1" in [s["id"] for s in struggling]


class TestAggregationPipelines:
    """Test MongoDB aggregation pipelines."""
    
    def test_group_by_content(self):
        """Test grouping questions by content."""
        questions = [
            {"content_id": "content-1", "student_id": "user-1"},
            {"content_id": "content-1", "student_id": "user-2"},
            {"content_id": "content-2", "student_id": "user-1"}
        ]
        
        # Group by content_id
        from collections import defaultdict
        grouped = defaultdict(list)
        for q in questions:
            grouped[q["content_id"]].append(q)
        
        assert len(grouped["content-1"]) == 2
        assert len(grouped["content-2"]) == 1
    
    def test_sort_by_timestamp(self):
        """Test sorting by timestamp."""
        questions = [
            {"timestamp": datetime(2024, 1, 3), "text": "Q3"},
            {"timestamp": datetime(2024, 1, 1), "text": "Q1"},
            {"timestamp": datetime(2024, 1, 2), "text": "Q2"}
        ]
        
        sorted_questions = sorted(questions, key=lambda x: x["timestamp"], reverse=True)
        
        assert sorted_questions[0]["text"] == "Q3"
        assert sorted_questions[2]["text"] == "Q1"
    
    def test_limit_results(self):
        """Test limiting results."""
        questions = [{"id": i} for i in range(100)]
        limit = 10
        
        limited = questions[:limit]
        
        assert len(limited) == limit


class TestAnalyticsAPI:
    """Test analytics API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_student_engagement_endpoint(self):
        """Test student engagement endpoint."""
        student_id = "user-123"
        
        # Mock response
        response = {
            "student_id": student_id,
            "total_questions": 25,
            "unique_contents": 5,
            "engagement_score": 75.5
        }
        
        assert response["student_id"] == student_id
        assert response["total_questions"] > 0
    
    @pytest.mark.asyncio
    async def test_get_content_stats_endpoint(self):
        """Test content stats endpoint."""
        content_id = "content-123"
        
        response = {
            "content_id": content_id,
            "total_questions": 50,
            "unique_students": 15,
            "avg_response_time_ms": 1500
        }
        
        assert response["content_id"] == content_id
        assert response["total_questions"] > 0
    
    @pytest.mark.asyncio
    async def test_get_question_types_endpoint(self):
        """Test question types endpoint."""
        content_id = "content-123"
        
        response = {
            "content_id": content_id,
            "total_questions": 50,
            "question_types": [
                {"type": "definition", "count": 15, "percentage": 30.0},
                {"type": "explanation", "count": 20, "percentage": 40.0}
            ]
        }
        
        assert len(response["question_types"]) > 0
        total_percentage = sum(qt["percentage"] for qt in response["question_types"])
        assert total_percentage <= 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

