/** Typed API functions for all backend endpoints. */

import api from './index'
import type {
  Organization,
  Team,
  TeamMember,
  Project,
  Iteration,
  Requirement,
  Specification,
  SpecVersion,
  SpecClause,
  DevTask,
  TestTask,
  TestCase,
  CoverageReport,
  CoverageCheck,
  TokenPair,
  User,
} from '@/types'

// ── Auth ──

export const authApi = {
  login: (username: string, password: string) =>
    api.post<TokenPair>('/auth/login', { username, password }),
  register: (data: { username: string; email: string; password: string; display_name?: string }) =>
    api.post<TokenPair>('/auth/register', data),
  refresh: (refresh_token: string) =>
    api.post<TokenPair>('/auth/refresh', { refresh_token }),
  me: () => api.get<User>('/auth/me'),
}

// ── Organizations ──

export const orgApi = {
  list: () => api.get<Organization[]>('/organizations'),
  create: (data: { name: string; slug: string }) =>
    api.post<Organization>('/organizations', data),
}

// ── Teams ──

export const teamApi = {
  list: () => api.get<Team[]>('/teams'),
  create: (data: { org_id: string; name: string; slug: string }) =>
    api.post<Team>('/teams', data),
  members: (teamId: string) => api.get<TeamMember[]>(`/teams/${teamId}/members`),
  addMember: (teamId: string, data: { user_id: string; roles: string }) =>
    api.post<TeamMember>(`/teams/${teamId}/members`, data),
}

// ── Projects ──

export const projectApi = {
  list: (teamId?: string) =>
    api.get<Project[]>('/projects', { params: { team_id: teamId } }),
  get: (id: string) => api.get<Project>(`/projects/${id}`),
  create: (data: { team_id: string; name: string; slug: string; description?: string }) =>
    api.post<Project>('/projects', data),
  update: (id: string, data: { name?: string; slug?: string; description?: string }) =>
    api.patch<Project>(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
}

// ── Iterations ──

export const iterationApi = {
  list: (projectId: string) =>
    api.get<Iteration[]>(`/projects/${projectId}/iterations`),
  create: (projectId: string, data: { name: string; start_date?: string; end_date?: string }) =>
    api.post<Iteration>(`/projects/${projectId}/iterations`, data),
  update: (projectId: string, id: string, data: { name?: string; status?: string }) =>
    api.patch<Iteration>(`/projects/${projectId}/iterations/${id}`, data),
}

// ── Requirements ──

export const reqApi = {
  list: (projectId: string, params?: { iteration_id?: string; status?: string }) =>
    api.get<Requirement[]>(`/projects/${projectId}/requirements`, { params }),
  get: (id: string) => api.get<Requirement>(`/requirements/${id}`),
  create: (projectId: string, data: { iteration_id: string; title: string; priority?: string }) =>
    api.post<Requirement>(`/projects/${projectId}/requirements`, data),
  updateStatus: (id: string, status: string) =>
    api.patch<Requirement>(`/requirements/${id}/status`, { status }),
}

// ── Specifications ──

export const specApi = {
  list: (reqId: string) =>
    api.get<Specification[]>(`/requirements/${reqId}/specifications`),
  create: (reqId: string, data: { spec_type: string; title: string }) =>
    api.post<Specification>(`/requirements/${reqId}/specifications`, data),

  // versions
  listVersions: (specId: string) =>
    api.get<SpecVersion[]>(`/specifications/${specId}/versions`),
  createVersion: (specId: string, content: Record<string, unknown>) =>
    api.post<SpecVersion>(`/specifications/${specId}/versions`, { content }),
  submitForReview: (versionId: string) =>
    api.patch<SpecVersion>(`/spec-versions/${versionId}/submit`),
  lock: (versionId: string) =>
    api.patch<SpecVersion>(`/spec-versions/${versionId}/lock`),
  reject: (versionId: string) =>
    api.patch<SpecVersion>(`/spec-versions/${versionId}/reject`),

  // clauses
  listClauses: (versionId: string) =>
    api.get<SpecClause[]>(`/spec-versions/${versionId}/clauses`),
  createClause: (versionId: string, data: {
    clause_id: string; title: string; description: string
    category: string; severity?: string
  }) =>
    api.post<SpecClause>(`/spec-versions/${versionId}/clauses`, data),
}

// ── Tasks ──

export const taskApi = {
  // dev tasks
  createDevTask: (reqId: string, data: {
    spec_version_id: string; iteration_id: string; title: string
    estimate_hours?: number
  }) =>
    api.post<DevTask>(`/requirements/${reqId}/dev-tasks`, data),
  listDevTasks: (projectId: string) =>
    api.get<DevTask[]>(`/projects/${projectId}/dev-tasks`),
  claimDevTask: (taskId: string) =>
    api.patch<DevTask>(`/dev-tasks/${taskId}/claim`),
  updateDevTaskStatus: (taskId: string, status: string) =>
    api.patch<DevTask>(`/dev-tasks/${taskId}/status`, { status }),

  // test tasks
  createTestTask: (reqId: string, data: { iteration_id: string; title: string }) =>
    api.post<TestTask>(`/requirements/${reqId}/test-tasks`, data),
  listTestTasks: (projectId: string) =>
    api.get<TestTask[]>(`/projects/${projectId}/test-tasks`),
}

// ── Test Cases ──

export const tcApi = {
  create: (testTaskId: string, data: {
    title: string; preconditions?: string; steps: string
    expected_result: string; clause_ids?: string[]
  }) =>
    api.post<TestCase>(`/test-tasks/${testTaskId}/test-cases`, data),
  list: (testTaskId: string) =>
    api.get<TestCase[]>(`/test-tasks/${testTaskId}/test-cases`),
  updateStatus: (tcId: string, status: string) =>
    api.patch<TestCase>(`/test-cases/${tcId}/status`, { status }),
}

// ── Coverage ──

export const coverageApi = {
  report: (reqId: string) =>
    api.get<CoverageReport>(`/requirements/${reqId}/coverage`),
  check: (reqId: string) =>
    api.get<CoverageCheck>(`/requirements/${reqId}/coverage/check`),
}
