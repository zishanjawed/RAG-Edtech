/**
 * Analytics Service
 * API calls for student analytics and content statistics
 */
import { analyticsClient } from './client'
import type {
  StudentEngagement,
  ContentStats,
  Question,
  QuestionTypeDistribution,
} from './types'

export const analyticsService = {
  /**
   * Get student engagement metrics
   */
  async getStudentEngagement(studentId: string): Promise<StudentEngagement> {
    const response = await analyticsClient.get<StudentEngagement>(
      `/api/analytics/student/${studentId}`
    )
    return response.data
  },

  /**
   * Get content statistics
   */
  async getContentStats(contentId: string): Promise<ContentStats> {
    const response = await analyticsClient.get<ContentStats>(
      `/api/content/${contentId}/stats`
    )
    return response.data
  },

  /**
   * Get questions for specific content
   */
  async getContentQuestions(
    contentId: string,
    limit: number = 50
  ): Promise<{ content_id: string; questions: Question[]; total: number }> {
    const response = await analyticsClient.get(
      `/api/content/${contentId}/questions`,
      {
        params: { limit },
      }
    )
    return response.data
  },

  /**
   * Get question type distribution for content (NEW)
   */
  async getQuestionTypes(contentId: string): Promise<QuestionTypeDistribution> {
    const response = await analyticsClient.get<QuestionTypeDistribution>(
      `/api/content/${contentId}/question-types`
    )
    return response.data
  },
}

