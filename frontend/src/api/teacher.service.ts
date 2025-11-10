/**
 * Teacher Dashboard Service
 * API calls for teacher analytics and classroom insights
 */
import { analyticsClient } from './client'
import type {
  TeacherOverview,
  StudentActivity,
  ContentEngagement,
} from './types'

export const teacherService = {
  /**
   * Get teacher dashboard overview
   */
  async getTeacherOverview(teacherId: string): Promise<TeacherOverview> {
    const response = await analyticsClient.get<TeacherOverview>(
      `/api/analytics/teacher/overview`,
      {
        params: { teacher_id: teacherId },
      }
    )
    return response.data
  },

  /**
   * Get all students activity metrics
   */
  async getAllStudents(
    teacherId: string,
    limit: number = 50
  ): Promise<{ teacher_id: string; students: StudentActivity[]; total_count: number }> {
    const response = await analyticsClient.get(
      `/api/analytics/teacher/students`,
      {
        params: {
          teacher_id: teacherId,
          limit,
        },
      }
    )
    return response.data
  },

  /**
   * Get content engagement analytics
   */
  async getContentEngagement(contentId: string): Promise<ContentEngagement> {
    const response = await analyticsClient.get<ContentEngagement>(
      `/api/analytics/content/${contentId}/engagement`
    )
    return response.data
  },
}

