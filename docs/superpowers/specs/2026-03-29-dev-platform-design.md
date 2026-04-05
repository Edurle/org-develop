# Spec-Driven Team Development Platform - Design Spec

## Context

构建一个**规范驱动开发**的团队协作平台。核心流程：产品经理记录需求 → 开发人员编写结构化规范 → 规范评审锁定（版本化，不可变）→ 开发按锁定规范实现 → 测试用例强制覆盖规范条款。平台支持 AI Agent 通过 MCP 参与。不是单纯的敏捷管理工具，而是通过规范约束整个开发过程的平台。

## Architecture

**Monorepo + MCP旁路服务**: FastAPI 单体后端 + Vue3 前端 + 独立 FastMCP 服务进程。

```
org-dev/
├── frontend/                  # Vue3 前端
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   ├── components/       # 通用组件
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── api/              # API 调用层
│   │   ├── router/           # Vue Router
│   │   └── utils/            # 工具函数
│   └── vite.config.ts
├── backend/                   # FastAPI 后端
│   ├── app/
│   │   ├── main.py           # 入口
│   │   ├── config.py         # 配置（支持 SQLite/MySQL/MongoDB 切换）
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── schemas/          # Pydantic 请求/响应模型
│   │   ├── routers/          # API 路由（按模块）
│   │   ├── services/         # 业务逻辑层
│   │   ├── auth/             # 认证（JWT + API Key）
│   │   └── database.py       # 数据库连接
│   ├── alembic/              # 数据库迁移
│   └── tests/
├── mcp/                       # FastMCP 旁路服务
│   ├── server.py             # MCP 服务入口
│   ├── tools/                # MCP 工具定义
│   └── auth.py               # API Key 验证
└── docs/
```

## Tech Stack

- **Frontend**: Vue3 + TypeScript + Pinia + Vue Router + UnoCSS
- **Backend**: FastAPI + SQLAlchemy + Alembic + Pydantic v2
- **Database**: SQLAlchemy (抽象层，SQLite for test / MySQL for prod) + Motor/PyMongo (MongoDB for prod)
- **Auth**: JWT (Web) + API Key with scopes (Agent/MCP)
- **MCP**: FastMCP (独立进程，HTTP 调用后端 API)
- **Notification**: Webhook (异步发送)
- **UI**: No component library, UnoCSS + hand-crafted components

## Spec-Driven Development Process

这是平台的核心流程，所有功能围绕此流程设计：

```
1. 产品经理创建需求 (Requirement)
2. 需求进入"规范编写"阶段
3. 开发人员为需求编写结构化规范 (Specification)
   ├── 接口规范 (API Spec) — 端点、请求/响应格式、状态码
   ├── 数据模型规范 (Data Spec) — 表结构、字段定义、关系
   ├── 业务流程规范 (Flow Spec) — 操作流程、状态流转、规则
   └── 前端设计规范 (UI Spec) — 组件结构、交互行为、布局
4. 规范分解为可验证的条款 (SpecClause)
5. 团队评审规范 (Review) → 锁定 (Locked)
6. 规范版本化，锁定后不可变
7. 开发人员基于锁定规范创建开发任务 (DevTask)
8. 测试人员基于规范条款创建测试用例 (TestCase)
9. 平台强制校验：每个规范条款必须被至少一个测试用例覆盖
10. 需求完成条件：所有任务完成 + 所有条款被测试覆盖且通过
```

### 强制约束规则

- 规范未锁定的需求，不能创建开发任务
- 开发任务必须关联特定规范版本
- 测试用例必须关联规范条款
- 需求标记完成前，平台校验所有条款覆盖率
- 规范锁定后只能新建版本，不能修改已锁定版本

## Data Model

### Entity Relationship

```
Organization
  └── Team (1:N)
        └── Project (1:N, 项目完全独立)
              └── Iteration (1:N)
              │     ├── Requirement (归属迭代)
              │     │     ├── Specification (1:N, 规范)
              │     │     │     ├── SpecVersion (版本化, 锁定后不可变)
              │     │     │     │     └── SpecClause (规范条款, 最小覆盖单位)
              │     │     ├── DevTask (关联 SpecVersion, 归属迭代)
              │     │     └── TestTask (归属迭代)
              │     │           └── TestCase (关联 SpecClause, 经典格式)
              └── WebhookConfig
```

### MySQL Tables (Structured Data)

| Table | Description | Key Fields |
|---|---|---|
| `organizations` | 组织 | name, slug |
| `teams` | 团队 | org_id, name, slug |
| `projects` | 项目 | team_id, name, slug, description |
| `iterations` | 迭代 | project_id, name, start_date, end_date, status |
| `requirements` | 需求 | iteration_id, title, priority, status, creator_id, assignee_id |
| `specifications` | 规范 | requirement_id, spec_type (api/data/flow/ui), title, current_version |
| `spec_versions` | 规范版本 | spec_id, version (int), status (draft/reviewing/locked), content (JSON), locked_at, locked_by |
| `spec_clauses` | 规范条款 | spec_version_id, clause_id (auto), title, description, category, severity (must/should/may) |
| `dev_tasks` | 开发任务 | requirement_id, spec_version_id, iteration_id, title, status, assignee_id, estimate_hours |
| `test_tasks` | 测试任务 | requirement_id, iteration_id, title, status, assignee_id |
| `test_cases` | 测试用例 | test_task_id, clause_id (FK→spec_clauses), title, preconditions, steps, expected_result, actual_result, status |
| `clause_coverage` | 条款覆盖 | clause_id, test_case_id (多对多关联) |
| `users` | 用户 | username, email, password_hash |
| `team_members` | 团队成员 | user_id, team_id, roles[] |
| `api_keys` | API密钥 | user_id, key_hash, name, scopes[], expires_at |
| `webhook_configs` | Webhook配置 | project_id, url, events[], secret |
| `audit_logs` | 操作日志 | user_id, action, resource_type, resource_id, detail |

### 规范内容结构 (spec_versions.content - JSON)

不同类型的规范有不同的 JSON Schema：

**接口规范 (api)**:
```json
{
  "endpoints": [
    {
      "path": "/api/projects",
      "method": "POST",
      "request_body": { /* JSON Schema */ },
      "response_body": { /* JSON Schema */ },
      "status_codes": { "200": "...", "400": "..." },
      "auth_required": true
    }
  ]
}
```

**数据模型规范 (data)**:
```json
{
  "tables": [
    {
      "name": "requirements",
      "fields": [
        { "name": "id", "type": "UUID", "constraints": ["PK"] },
        { "name": "title", "type": "VARCHAR(200)", "constraints": ["NOT NULL"] }
      ],
      "indexes": [...],
      "relations": [...]
    }
  ]
}
```

**业务流程规范 (flow)**:
```json
{
  "flows": [
    {
      "name": "需求状态流转",
      "states": ["draft", "review", "confirmed", ...],
      "transitions": [
        { "from": "draft", "to": "review", "trigger": "submit", "conditions": [...] }
      ],
      "rules": ["规范未锁定不能创建任务", ...]
    }
  ]
}
```

**前端设计规范 (ui)** — 内嵌元素定位规范:
```json
{
  "common_components": [
    {
      "component_id": "confirm-dialog",
      "name": "确认对话框",
      "elements": [
        {
          "role": "interactive",
          "description": "确认按钮",
          "locator": { "type": "data-testid", "value": "confirm-dialog-confirm-btn" }
        },
        {
          "role": "interactive",
          "description": "取消按钮",
          "locator": { "type": "data-testid", "value": "confirm-dialog-cancel-btn" }
        },
        {
          "role": "display",
          "description": "提示消息文本",
          "locator": { "type": "data-testid", "value": "confirm-dialog-message" }
        }
      ]
    }
  ],
  "views": [
    {
      "route": "/projects/:id/requirements",
      "name": "需求列表页",
      "layout": "...",
      "components": ["confirm-dialog"],
      "elements": [
        {
          "role": "interactive",
          "description": "创建需求按钮",
          "locator": { "type": "data-testid", "value": "create-requirement-btn" }
        },
        {
          "role": "interactive",
          "description": "需求标题输入框",
          "locator": { "type": "name", "value": "requirement-title" }
        },
        {
          "role": "display",
          "description": "需求总数统计",
          "locator": { "type": "data-testid", "value": "requirement-count" }
        }
      ],
      "interactions": [
        { "element": "create-requirement-btn", "event": "click", "action": "打开创建表单" }
      ]
    }
  ]
}
```

### 元素定位规范规则

**定位方式**（按优先级）：
1. `data-testid` — 首选，用于所有交互元素和关键展示元素
2. `name` — 用于表单输入元素（input, select, textarea）

**元素分类**：
- `interactive` — 可交互元素（按钮、输入框、下拉框、链接、开关等），必须定义定位
- `display` — 关键展示元素（状态文本、错误提示、数据统计、表格数据等），需要断言的必须定义定位

**命名规范**：
- `data-testid` 格式：`{区域/模块}-{元素描述}-{类型后缀}`，如 `login-submit-btn`, `requirement-title-input`, `requirement-count`
- `name` 属性：语义化命名，如 `username`, `password`, `requirement-title`
- 公共组件的 testid 以组件名前缀：`confirm-dialog-confirm-btn`

**覆盖要求**：
- 每个页面的所有交互元素必须有定位定义
- 测试用例中需要断言内容的展示元素必须有定位定义
- 公共组件只定义一次，页面通过引用复用

### MongoDB Collections (Long Text)

| Collection | Description |
|---|---|
| `requirement_descriptions` | 需求详细描述、富文本、附件引用 |
| `spec_discussions` | 规范评审讨论记录 |
| `task_comments` | 任务评论、讨论记录 |
| `test_case_details` | 测试步骤详细说明、截图引用 |
| `activity_streams` | 活动流、变更历史 |

## Auth Design

- **Web Login**: JWT (access_token + refresh_token)
- **API Key**: Key with scopes (e.g. `requirements:read`, `specs:write`, `tasks:write`), associated to user, inherits user permissions
- API Key 用于 Agent/MCP 访问

## Status Flows

### Requirement (增加规范阶段)

```
draft → spec_writing → spec_review → spec_locked → in_progress → testing → done
                          ↓              ↓                          ↓
                       spec_rejected  spec_rejected             cancelled
```

**关键状态门控**：
- `draft → spec_writing`: 产品经理确认需求，转给开发写规范
- `spec_writing → spec_review`: 开发提交规范，进入评审
- `spec_review → spec_locked`: 评审通过，规范版本锁定
- `spec_review → spec_rejected`: 评审不通过，退回修改
- `spec_locked → in_progress`: 开发开始（此时才允许创建开发任务）
- `in_progress → testing`: 开发完成，进入测试
- 测试完成且所有条款覆盖 → `done`

### Specification Version

```
draft → reviewing → locked (不可变)
           ↓
        rejected (退回 draft)
```

### Task (Dev & Test)

```
open → in_progress → review → done
           ↓
        blocked
```

### Test Case

```
pending → running → passed / failed / blocked
```

## Coverage Enforcement

### 条款覆盖校验逻辑

1. 每个规范版本包含多个 `SpecClause`（条款）
2. 每个测试用例通过 `clause_coverage` 关联到一个或多个条款
3. **校验规则**：
   - 每个 `must` 级别条款必须被至少 1 个测试用例覆盖
   - `should` 级别条款覆盖率达到 80% 视为通过
   - `may` 级别条款不强制覆盖
4. **校验时机**：
   - 创建测试用例时，必须选择关联的条款
   - 需求从 `testing → done` 时，自动校验覆盖率
   - 覆盖率不达标时，平台阻止状态流转

### 覆盖率报告

平台提供按需求维度的覆盖率报告：
- 总条款数 / 已覆盖条款数
- 按规范类型分组的覆盖率
- 按严重级别 (must/should/may) 分组的覆盖率
- 未覆盖条款清单

## API Endpoints

```
# Auth
POST   /api/auth/login
POST   /api/auth/refresh
POST   /api/auth/api-keys
DELETE /api/auth/api-keys/{key_id}

# Org/Team/Project
GET/POST       /api/teams
GET/POST       /api/projects
GET/PATCH/DEL  /api/projects/{id}

# Iterations
GET/POST       /api/projects/{pid}/iterations
PATCH          /api/projects/{pid}/iterations/{id}/status

# Requirements
GET/POST       /api/projects/{pid}/requirements
GET/PATCH/DEL  /api/projects/{pid}/requirements/{id}
PATCH          /api/projects/{pid}/requirements/{id}/status

# Specifications
GET/POST       /api/projects/{pid}/requirements/{rid}/specifications
GET/PATCH      /api/projects/{pid}/requirements/{rid}/specifications/{sid}

# Spec Versions
GET/POST       /api/specifications/{sid}/versions
PATCH          /api/specifications/{sid}/versions/{vid}/status   # draft→reviewing→locked
GET            /api/specifications/{sid}/versions/{vid}/clauses

# Spec Clauses
GET/POST       /api/spec-versions/{vid}/clauses
PATCH/DEL      /api/spec-clauses/{cid}

# Dev Tasks (需要 spec_locked 状态)
GET/POST       /api/projects/{pid}/dev-tasks
PATCH          /api/projects/{pid}/dev-tasks/{id}/status
PATCH          /api/projects/{pid}/dev-tasks/{id}/claim

# Test Tasks & Cases
GET/POST       /api/projects/{pid}/test-tasks
GET/POST       /api/projects/{pid}/test-cases
PATCH          /api/projects/{pid}/test-cases/{id}/status
POST           /api/test-cases/{tcid}/coverages    # 关联条款

# Coverage
GET            /api/projects/{pid}/requirements/{rid}/coverage
GET            /api/projects/{pid}/requirements/{rid}/coverage/report

# Webhook
GET/POST/DEL   /api/projects/{pid}/webhooks
```

### Webhook Events

`requirement.status_changed`, `spec.submitted`, `spec.locked`, `task.claimed`, `task.completed`, `test_case.failed`, `coverage.insufficient`

## MCP Service Design

### Architecture

```
Agent ←→ MCP Server (FastMCP) ←→ FastAPI Backend API
                  ↑
           API Key Auth
```

### First Batch MCP Tools

| Tool | Function | Scope |
|---|---|---|
| `list_requirements` | 列出需求列表 | `requirements:read` |
| `get_requirement` | 获取需求详情 | `requirements:read` |
| `create_requirement` | 创建需求 | `requirements:write` |
| `update_requirement_status` | 更新需求状态 | `requirements:write` |
| `list_specifications` | 列出需求的规范 | `specs:read` |
| `get_specification` | 获取规范详情（含条款） | `specs:read` |
| `create_specification` | 创建规范 | `specs:write` |
| `submit_spec_for_review` | 提交规范评审 | `specs:write` |
| `list_spec_clauses` | 列出规范条款 | `specs:read` |
| `create_spec_clause` | 创建规范条款 | `specs:write` |
| `list_dev_tasks` | 列出开发任务 | `tasks:read` |
| `create_dev_task` | 创建开发任务（必须关联规范版本） | `tasks:write` |
| `claim_dev_task` | 认领开发任务 | `tasks:write` |
| `update_task_status` | 更新任务状态 | `tasks:write` |
| `list_test_cases` | 列出测试用例 | `testcases:read` |
| `create_test_case` | 创建测试用例（必须关联条款） | `testcases:write` |
| `update_test_case_status` | 更新测试用例状态 | `testcases:write` |
| `get_coverage_report` | 获取覆盖率报告 | `testcases:read` |
| `search` | 全局搜索 | `search:read` |

### Skill Design

- `skill:dev-platform` — 定义 agent 在规范驱动流程中的工作流
- 包含操作模板：
  - 从需求编写规范（四种类型）
  - 从规范分解开发任务
  - 从规范条款生成测试用例
  - 校验覆盖率

## Frontend Pages

| Page | Route | Function |
|---|---|---|
| 登录 | `/login` | 用户名密码登录 |
| 仪表盘 | `/` | 个人待办、全局概览、覆盖率仪表盘 |
| 团队管理 | `/teams` | 团队 CRUD、成员管理、角色分配 |
| 项目列表 | `/projects` | 项目 CRUD |
| 迭代看板 | `/projects/:id/iterations` | 迭代列表、看板视图 |
| 需求列表 | `/projects/:id/requirements` | 需求 CRUD、状态筛选 |
| 需求详情 | `/projects/:id/requirements/:rid` | 详情、关联规范、任务、覆盖率 |
| 规范编辑 | `/projects/:id/requirements/:rid/specs/:sid` | 结构化规范编辑器、条款管理、评审 |
| 规范评审 | `/projects/:id/requirements/:rid/specs/:sid/review` | 评审界面、讨论、通过/拒绝 |
| 任务列表 | `/projects/:id/tasks` | 开发+测试任务统一视图 |
| 测试用例 | `/projects/:id/test-cases` | 测试用例 CRUD、条款关联、执行状态 |
| 覆盖率报告 | `/projects/:id/coverage` | 条款覆盖可视化、未覆盖清单 |
| API Key 管理 | `/settings/api-keys` | 创建/吊销 API Key |
| Webhook 管理 | `/projects/:id/webhooks` | Webhook 配置 |

### Layout

- 顶部导航栏：组织名、当前项目切换、用户菜单
- 左侧边栏：项目内导航（迭代、需求、规范、任务、测试、覆盖率、Webhook）
- 主内容区：页面内容

## Constraints

- 部署模式：先单组织，预留多租户扩展
- 用户：内部用户为主
- MCP：渐进式暴露工具
- 权限：RBAC 可配置，一人多角色
- 项目：完全独立
- 测试用例：经典格式（标题、前置条件、步骤、预期结果、实际结果）
- 通知：Webhook 支持多平台
- **规范驱动**：规范前置、强制约束、版本化不可变、测试覆盖强制校验
