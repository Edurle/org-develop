/** Shared TypeScript types matching backend Pydantic schemas. */

// ── Auth ──
export interface User {
  id: string
  username: string
  email: string
  display_name: string | null
  is_active: boolean
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

// ── Org / Team ──
export interface Organization {
  id: string
  name: string
  slug: string
  created_at: string
  updated_at: string
}

export interface Team {
  id: string
  org_id: string
  name: string
  slug: string
  created_at: string
  updated_at: string
}

export interface TeamMember {
  id: string
  user_id: string
  team_id: string
  roles: string
  joined_at: string
}

// ── Project ──
export interface Project {
  id: string
  team_id: string
  name: string
  slug: string
  description: string | null
  created_at: string
  updated_at: string
}

// ── Iteration ──
export interface Iteration {
  id: string
  project_id: string
  name: string
  status: string
  start_date: string | null
  end_date: string | null
  created_at: string
  updated_at: string
}

// ── Requirement ──
export type ReqStatus =
  | 'draft'
  | 'spec_writing'
  | 'spec_review'
  | 'spec_locked'
  | 'spec_rejected'
  | 'in_progress'
  | 'testing'
  | 'done'
  | 'cancelled'

export type Priority = 'low' | 'medium' | 'high' | 'critical'

export interface Requirement {
  id: string
  iteration_id: string
  title: string
  priority: Priority
  status: ReqStatus
  creator_id: string
  assignee_id: string | null
  created_at: string
  updated_at: string
}

// ── Specification ──
export type SpecType = 'api' | 'data' | 'flow' | 'ui'

export interface Specification {
  id: string
  requirement_id: string
  spec_type: SpecType
  title: string
  current_version: number
  created_at: string
  updated_at: string
}

export type VersionStatus = 'draft' | 'reviewing' | 'locked' | 'rejected'

export interface SpecVersion {
  id: string
  spec_id: string
  version: number
  status: VersionStatus
  content: Record<string, unknown>
  locked_at: string | null
  locked_by: string | null
  created_at: string
  updated_at: string
}

export type Severity = 'must' | 'should' | 'may'
export type ClauseCategory =
  | 'functional'
  | 'validation'
  | 'security'
  | 'performance'
  | 'ui_element'

export interface SpecClause {
  id: string
  spec_version_id: string
  clause_id: string
  title: string
  description: string
  category: ClauseCategory
  severity: Severity
  created_at: string
}

// ── Tasks ──
export type TaskStatus =
  | 'open'
  | 'in_progress'
  | 'review'
  | 'done'
  | 'blocked'

export interface DevTask {
  id: string
  requirement_id: string
  spec_version_id: string | null
  iteration_id: string
  title: string
  status: TaskStatus
  assignee_id: string | null
  estimate_hours: number | null
  created_at: string
  updated_at: string
}

export interface TestTask {
  id: string
  requirement_id: string
  iteration_id: string
  title: string
  status: string
  assignee_id: string | null
  created_at: string
  updated_at: string
}

// ── Test Cases ──
export type TCStatus = 'pending' | 'running' | 'passed' | 'failed' | 'blocked'

export interface TestCase {
  id: string
  test_task_id: string
  title: string
  preconditions: string | null
  steps: string
  expected_result: string
  actual_result: string | null
  status: TCStatus
  created_at: string
  updated_at: string
}

// ── Coverage ──
export interface CoverageReport {
  total_clauses: number
  covered_clauses: number
  must_coverage_pct: number
  should_coverage_pct: number
  may_coverage_pct: number
  uncovered_clauses: Array<{
    id: string
    clause_id: string
    title: string
    severity: Severity
    category: ClauseCategory
  }>
}

export interface CoverageCheck {
  sufficient: boolean
}

// ── API Key ──
export interface ApiKey {
  id: string
  name: string
  scopes: string[]
  prefix: string
  created_at: string
}
