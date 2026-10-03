import { apiClient } from './client'
import type { HealthResponse } from './types'

export async function fetchHealth(): Promise<HealthResponse> {
  return apiClient<HealthResponse>('/health')
}
