# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在本仓库中工作时提供指导。

## 项目概述

规格驱动开发平台，强制执行结构化工作流：开发前必须编写并锁定规格说明，工作标记完成前测试覆盖率必须达标。Monorepo 架构，包含两个组件：FastAPI 后端和 Vue3 前端。

## 开发命令

### 后端 (Python 3.11+, FastAPI)
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000   # 开发服务器
pytest -v                                                     # 运行全部测试（配置在 pyproject.toml，asyncio_mode = "auto"）
pytest tests/test_requirement_service.py -v                   # 运行单个测试文件
pytest tests/test_requirement_service.py::test_create_requirement -v  # 运行单个测试
alembic revision --autogenerate -m "description"              # 生成新迁移（尚未创建过迁移）
alembic upgrade head                                           # 执行迁移
```

### 前端 (Vue 3 + TypeScript)
```bash
cd frontend
npm run dev      # Vite 开发服务器，端口 3000，代理 /api 到 localhost:8000
npm run build    # 生产构建
npm run test     # Vitest（尚未编写测试）
```

### 集成测试
```bash
cd tests
pytest test_integration.py -v  # 需要后端运行在 localhost:8000
```

## 架构

```
┌─────────────┐     ┌──────────────┐
│  Frontend   │────▶│   Backend    │
│  Vue3/TS    │     │  FastAPI     │
│  :3000      │     │  :8000       │
└─────────────┘     └──────┬───────┘
                           │
                    ┌──────┴──────┐
                    │ SQLite/MySQL│
                    │ + MongoDB   │
                    └─────────────┘
```

### 后端结构 (`backend/app/`)
- **Models** (`models/`) — SQLAlchemy 2.0 异步 ORM。所有模型继承 `BaseMixin`（UUID 主键、时间戳）。核心层级：Organization → Team → Project → Iteration → Requirement → Specification/Task/TestCase。辅助模型：User/TeamMember、AuditLog、WebhookConfig
- **Services** (`services/`) — 业务逻辑层。处理状态流转、验证、覆盖率计算、审计日志记录和 Webhook 分发。包含 `audit.py`（审计日志，所有 CUD 操作自动记录）、`spec_validation.py`（规格验证）、`clause.py`（条款管理）
- **Routers** (`routers/`) — `/api` 前缀下的 FastAPI 路由处理器，全部使用 async。包括 auth、users、teams、projects、iterations、requirements、specifications、tasks、testcases、coverage、webhooks、audit
- **Schemas** (`schemas/`) — Pydantic v2 请求/响应模型。`common.py` 提供 `PaginationParams` 依赖和 `PaginatedResponse[T]` 泛型包装器
- **Auth** (`auth/`) — JWT 令牌（Web 端）+ 带作用域的 API 密钥（智能体端）。API 密钥前缀：`odk_`

### 前端结构 (`frontend/src/`)
- **API 层** (`api/`) — 带认证拦截器的 Axios 实例 + `endpoints.ts` 中的类型化端点函数
- **Router** (`router/`) — Vue Router 配置，带嵌套路由和 auth guards
- **Stores** (`stores/`) — Pinia stores（组合式 API 风格），按领域划分：auth、project、requirement、specification、task、testcase、iteration、coverage
- **Views** (`views/`) — 懒加载页面组件。项目详情使用嵌套路由（Overview、Members、Settings、Tasks）
- **Components** (`components/`) — 可复用组件：AppLayout、ProjectLayout、StatusBadge、Modal、EmptyState
- **Types** (`types/index.ts`) — TypeScript 接口，与后端 Pydantic schemas 对应
- **样式** — UnoCSS（原子化 CSS，不使用组件库）

## 核心工作流（规格驱动开发）

需求状态流转及强制门控：
```
draft → spec_writing → spec_review → spec_locked → in_progress → testing → done
```

服务层强制执行的关键约束：
- 开发任务只能基于 `locked` 状态的规格版本创建
- 规格版本锁定后**不可变**
- 测试用例必须关联规格条款（must/should/may 类别）
- 覆盖率阈值：`must` 条款要求 100%，`should` 要求 80%
- 需求在覆盖率不足时无法流转至 `done`
- UI 规格在提交评审前需要特殊验证

## 测试

后端测试在 `backend/tests/`，12 个测试文件按 service 一一对应（含 conftest.py）。测试通过 service 层直接调用（非 HTTP 级别），使用内存 SQLite + pytest-asyncio（auto mode）。主要测试文件：test_spec_driven_flow、test_user_service、test_team_service、test_project_service、test_iteration_service、test_requirement_service、test_specification_service、test_clause_service、test_task_service、test_testcase_service、test_audit_service、test_pagination。

集成测试在 `tests/test_integration.py`，使用 Playwright，需要后端运行在 localhost:8000。

## 关键模式

- **全链路异步** — 后端使用 async SQLAlchemy + async 路由处理器
- **基于作用域的认证** — API 密钥具有细粒度作用域，如 `requirements:read`、`tasks:write`
- **分页** — 所有列表端点支持 `?page=1&page_size=20`，响应使用 `PaginatedResponse[T]` 泛型（`schemas/common.py`）
- **审计日志** — Service 层自动记录所有 CUD 操作，命名模式 `{resource_type}.{action}`，通过 `GET /api/audit-logs` 查询
- **Webhook 系统** — HMAC-SHA256 签名负载，含重试逻辑（最多 3 次）
- **双认证机制** — Web 用户使用 JWT，API 密钥用于程序化访问
- **数据库灵活性** — 开发/测试使用 SQLite（aiosqlite），生产使用 MySQL（aiomysql），MongoDB 可选用于长文本存储

## 配置

后端通过 `.env` 文件或环境变量配置（参见 `backend/app/config.py`）：
- `DATABASE_URL` — 默认：`sqlite+aiosqlite:///./dev.db`
- `SECRET_KEY` — JWT 签名密钥（生产环境务必修改）
- `MONGO_URL` / `MONGO_DB_NAME` — 可选，用于长文本内容的 MongoDB
- `ENVIRONMENT` — `development` | `production`

前端：Vite 开发服务器端口 3000，代理 `/api` 到 `http://localhost:8000`（参见 `frontend/vite.config.ts`）。

## 任务完成后的自动提交规则

**每次完成一个开发任务（修复 bug、添加功能、重构、样式调整等）后，必须使用 `/commit` 命令（subagent）提交并同步代码。**

具体要求：
1. 完成任务代码修改后，不要等待用户指示，立即执行 `/commit` 命令
2. 该命令会使用 glm-4.7 模型的 subagent 自动检查变更、生成提交信息、提交并推送到远程
3. 即使是微小的样式修改或文本调整，也应提交
4. 唯一例外：用户明确要求"不要提交"或"稍后提交"时，跳过此步骤

## 设计文档

- `docs/superpowers/specs/2026-03-29-dev-platform-design.md` — 完整系统设计规格（中文）
- `docs/superpowers/specs/2026-04-04-improvements-design.md` — 改进方案：分页、API 补全、审计日志、测试（4 阶段）
