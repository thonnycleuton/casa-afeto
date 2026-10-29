import { apiClient } from './client'
import type {
  AuthTokens,
  LoginRequest,
  UserProfile,
  UserCreateInput,
  UserResponse,
  UserUpdateInput,
} from './types'

export async function login(data: LoginRequest): Promise<AuthTokens> {
  return apiClient<AuthTokens>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function refresh(refreshToken: string): Promise<AuthTokens> {
  return apiClient<AuthTokens>('/api/v1/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
}

export async function logout(refreshToken: string): Promise<void> {
  await apiClient('/api/v1/auth/logout', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
}

export async function getMe(): Promise<UserProfile> {
  return apiClient<UserProfile>('/api/v1/auth/me')
}

export async function forgotPassword(email: string): Promise<void> {
  await apiClient('/api/v1/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  await apiClient('/api/v1/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, new_password: newPassword }),
  })
}

export async function setupAdmin(
  email: string,
  password: string,
  fullName: string,
): Promise<void> {
  await apiClient('/api/v1/setup/create-admin', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name: fullName }),
  })
}

// --- User management (admin only) ---

export async function fetchUsers(): Promise<UserResponse[]> {
  return apiClient<UserResponse[]>('/api/v1/users')
}

export async function createUser(data: UserCreateInput): Promise<UserResponse> {
  return apiClient<UserResponse>('/api/v1/users', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateUser(
  userId: number,
  data: UserUpdateInput,
): Promise<UserResponse> {
  return apiClient<UserResponse>(`/api/v1/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deactivateUser(userId: number): Promise<UserResponse> {
  return apiClient<UserResponse>(`/api/v1/users/${userId}`, {
    method: 'DELETE',
  })
}
