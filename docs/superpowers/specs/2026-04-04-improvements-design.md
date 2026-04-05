# 改进方案：API 补全 + 分页 + 审计日志 + 测试

## Context

项目核心功能（规格驱动开发流程、前后端、MCP 服务器）已完整实现，但存在以下缺口：
- 部分 CRUD 端点缺失（详情查询、删除、更新操作）
- 所有列表端点缺少分页支持
- AuditLog 模型已定义但未使用
- 后端测试覆盖不足（仅 18 个核心流程测试）

本方案按依赖关系分 4 个阶段实施。

---

## 阶段 1：分页支持

### 设计决策

- 使用 FastAPI `Query` 参数依赖，支持 `?page=1&page_size=20`
- 复用已有 `PaginatedResponse[T]` 泛型包装器（`schemas/common.py`）
- 响应格式：`{items: [...], total: int, page: int, page_size: int, total_pages: int}`
- 破坏性变更：前端 API 层需同步适配

### 实施步骤

1. 更新 `backend/app/schemas/common.py`
   - 将 `PaginationParams` 改为 FastAPI 依赖类（使用 `Query` 参数）
   - 添加 `paginate()` 辅助函数

2. 更新 12 个列表端点（7 个 router 文件）
   - `GET /organizations`（teams.py）
   - `GET /teams`（teams.py）
   - `GET /teams/{team_id}/members`（teams.py）
   - `GET /projects`（projects.py）
   - `GET /projects/{project_id}/iterations`（iterations.py）
   - `GET /projects/{project_id}/requirements`（requirements.py）
   - `GET /requirements/{req_id}/specifications`（specifications.py）
   - `GET /specifications/{spec_id}/versions`（specifications.py）
   - `GET /spec-versions/{version_id}/clauses`（specifications.py）
   - `GET /projects/{project_id}/dev-tasks`（tasks.py）
   - `GET /projects/{project_id}/test-tasks`（tasks.py）
   - `GET /test-tasks/{task_id}/test-cases`（testcases.py）

每个端点：
- 注入 `PaginationParams` 依赖
- SQLAlchemy 查询添加 `.offset().limit()`
- 单独 `SELECT COUNT` 获取总数
- 响应模型从 `list[XResponse]` 改为 `PaginatedResponse[XResponse]`

### 涉及文件

- `backend/app/schemas/common.py` — 修改
- `backend/app/routers/teams.py` — 3 端点修改
- `backend/app/routers/projects.py` — 1 端点修改
- `backend/app/routers/iterations.py` — 1 端点修改
- `backend/app/routers/requirements.py` — 1 端点修改
- `backend/app/routers/specifications.py` — 3 端点修改
- `backend/app/routers/tasks.py` — 2 端点修改
- `backend/app/routers/testcases.py` — 1 端点修改

---

## 阶段 2：API 端点补全（19 个新端点）

### 2.1 用户管理（新 router）

创建 `backend/app/routers/users.py`：

- `GET /api/users/me` — 返回当前用户信息
- `PATCH /api/users/me` — 更新当前用户资料（display_name, email）
- `GET /api/users/{user_id}` — 按用户 ID 查询

Service 层（`services/user.py`）：
- 添加 `update_user(db, user_id, **fields)` 方法

Schema：`UserResponse` 已存在。

### 2.2 组织/团队管理（扩展 teams router）

向 `routers/teams.py` 添加 6 个端点：

- `GET /organizations/{org_id}` — 组织详情
- `PATCH /organizations/{org_id}` — 更新组织
- `DELETE /organizations/{org_id}` — 删除组织（级联删除团队）
- `GET /teams/{team_id}` — 团队详情
- `PATCH /teams/{team_id}` — 更新团队
- `DELETE /teams/{team_id}` — 删除团队（级联删除项目）
- `DELETE /teams/{team_id}/members/{user_id}` — 移除成员
- `PATCH /teams/{team_id}/members/{user_id}` — 更新成员角色

Service 层（`services/team.py`）添加方法：
- `get_organization()`, `update_organization()`, `delete_organization()`
- `get_team()`, `update_team()`, `delete_team()`
- `remove_team_member()`, `update_team_member_roles()`

### 2.3 迭代管理（扩展 iterations router）

向 `routers/iterations.py` 添加：
- `DELETE /projects/{project_id}/iterations/{iteration_id}`
- `GET /iterations/{iteration_id}`

Service 层添加 `delete_iteration()`, `get_iteration()`。

### 2.4 规格版本（扩展 specifications router）

添加 `GET /spec-versions/{version_id}` — 路由直接查询。

### 2.5 任务管理（扩展 tasks router）

向 `routers/tasks.py` 添加：
- `GET /dev-tasks/{task_id}` — 开发任务详情
- `GET /test-tasks/{task_id}` — 测试任务详情
- `PATCH /test-tasks/{task_id}/claim` — 认领测试任务
- `PATCH /test-tasks/{task_id}/status` — 更新测试任务状态

Service 层（`services/task.py`）添加 `claim_test_task()`, `update_test_task_status()`。

### 2.6 测试用例（扩展 testcases router）

向 `routers/testcases.py` 添加：
- `GET /test-cases/{test_case_id}` — 详情
- `PATCH /test-cases/{test_case_id}` — 更新
- `DELETE /test-cases/{test_case_id}` — 删除

Service 层（`services/testcase.py`）添加 `update_test_case()`, `delete_test_case()`。

### 涉及文件

**新文件：**
- `backend/app/routers/users.py`

**修改文件：**
- `backend/app/services/user.py`
- `backend/app/services/team.py`
- `backend/app/services/iteration.py`
- `backend/app/services/task.py`
- `backend/app/services/testcase.py`
- `backend/app/routers/teams.py`
- `backend/app/routers/iterations.py`
- `backend/app/routers/specifications.py`
- `backend/app/routers/tasks.py`
- `backend/app/routers/testcases.py`
- `backend/app/main.py` — 注册 users router

---

## 阶段 3：审计日志

### 设计决策

- **记录方式**：Service 层调用，与 webhook dispatch 同模式
- **命名模式**：`{resource_type}.{action}`（如 `requirement.status_change`）
- **事务保证**：`log_action()` 在同一事务中 flush，不额外 commit
- **记录范围**：所有 CUD 操作，不记录 GET

### 实施步骤

1. 创建 `backend/app/services/audit.py`
   - `log_action(db, user_id, action, resource_type, resource_id, detail)` — 记录审计日志
   - `query_audit_logs(db, filters, pagination)` — 查询审计日志

2. 创建 `backend/app/schemas/audit.py`
   - `AuditLogResponse` — 审计日志响应模型
   - `AuditLogFilter` — 过滤参数模型

3. 创建 `backend/app/routers/audit.py`
   - `GET /api/audit-logs` — 带过滤和分页的审计日志查询

4. 在 9 个 service 中集成审计日志（约 30 个审计点）：
   - `services/requirement.py` — 3 点
   - `services/specification.py` — 4 点
   - `services/clause.py` — 1 点
   - `services/task.py` — 5 点
   - `services/testcase.py` — 4 点
   - `services/team.py` — 8 点
   - `services/iteration.py` — 2 点
   - `services/project.py` — 3 点
   - `services/user.py` — 2 点

5. 路由层适配 — 传递 `user_id` 给需要审计的 service 方法

### 涉及文件

**新文件：**
- `backend/app/services/audit.py`
- `backend/app/schemas/audit.py`
- `backend/app/routers/audit.py`

**修改文件：**
- 9 个 service 文件 — 添加审计调用
- 相关 router 文件 — 传递 user_id
- `backend/app/main.py` — 注册 audit router

---

## 阶段 4：后端测试补全（~88 个新测试）

### 设计决策

- 沿用现有 `conftest.py` 模式：内存 SQLite + 每测试独立数据库
- 直接调用 service 方法（非 HTTP 级别），更快且符合现有模式
- 测试文件与 service 一一对应

### 测试文件规划

| 文件 | 测试数 | 覆盖内容 |
|------|-------|---------|
| `test_user_service.py` | 8 | CRUD、唯一约束、重复校验 |
| `test_team_service.py` | 12 | 组织/团队/成员完整 CRUD + 边界 |
| `test_project_service.py` | 6 | 项目 CRUD |
| `test_iteration_service.py` | 5 | 迭代 CRUD |
| `test_requirement_service.py` | 8 | 创建、状态转换边界、无效转换 |
| `test_specification_service.py` | 10 | 类型验证、版本创建、状态流转 |
| `test_clause_service.py` | 5 | 条款创建、类别/严重性验证 |
| `test_task_service.py` | 10 | 开发/测试任务、认领、状态转换 |
| `test_testcase_service.py` | 8 | 测试用例 CRUD、状态、条款链接 |
| `test_error_handling.py` | 10 | 404/400 模式验证 |
| `test_pagination.py` | 6 | 分页参数、边界、总数计算 |

### 涉及文件

**新文件：**
- `backend/tests/test_user_service.py`
- `backend/tests/test_team_service.py`
- `backend/tests/test_project_service.py`
- `backend/tests/test_iteration_service.py`
- `backend/tests/test_requirement_service.py`
- `backend/tests/test_specification_service.py`
- `backend/tests/test_clause_service.py`
- `backend/tests/test_task_service.py`
- `backend/tests/test_testcase_service.py`
- `backend/tests/test_error_handling.py`
- `backend/tests/test_pagination.py`

**修改文件：**
- `backend/tests/conftest.py` — 可能需要额外辅助 fixture

---

## 验证方式

每个阶段完成后：
1. 运行 `cd backend && pytest -v` 确认所有测试通过
2. 启动 `uvicorn app.main:app --reload` 验证 API 端点可访问
3. 阶段 2 完成后用 FastAPI Swagger UI 检查新端点
4. 阶段 3 完成后检查 `GET /api/audit-logs` 返回正确记录
5. 阶段 4 完成后确认测试总数约 106 个（18 现有 + 88 新增）
