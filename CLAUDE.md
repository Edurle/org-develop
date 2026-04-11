# CLAUDE.md

本文件为 AI 编码助手（OpenCode / Claude Code 等）在本仓库中工作时提供指导。

## 项目概述

规格驱动开发平台，强制执行结构化工作流：开发前必须编写并锁定规格说明，工作标记完成前测试覆盖率必须达标。Monorepo 架构，包含两个组件：FastAPI 后端和 Vue3 前端。

## 开发命令

### 快速启动（两个服务同时）
```bash
./start.sh          # 启动后端(:8000) + 前端(:3000)，PID 写入 .pids/
./stop.sh           # 停止所有服务（按 PID 或端口 fallback）
```

### 后端 (Python 3.11+, FastAPI)
```bash
# 开发服务器 — 在 backend/ 下运行
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 测试 — 在 backend/ 下运行，pytest-asyncio asyncio_mode = "auto"
cd backend && pytest -v                                                       # 全部
cd backend && pytest tests/test_specification_service.py -v                   # 单文件
cd backend && pytest tests/test_specification_service.py::test_create_spec -v # 单测试

# 数据库迁移 — ⚠️ 必须在仓库根目录运行（alembic.ini 在 backend/ 但 script_location = backend/alembic）
alembic revision --autogenerate -m "description"   # 生成迁移（尚未创建过迁移）
alembic upgrade head                                # 执行迁移
```

### 前端 (Vue 3 + TypeScript)
```bash
cd frontend
npm run dev      # Vite 开发服务器，端口 3000，代理 /api → localhost:8000
npm run build    # vue-tsc 类型检查 + 生产构建（先类型检查再构建）
npm run test     # Vitest（尚未编写测试）
```

前端类型检查也可单独运行：`cd frontend && npx vue-tsc --noEmit`

### 端到端测试
```bash
cd tests && pytest -v
# 需要：后端运行在 localhost:8000、前端运行在 localhost:3000
# 使用 requests（API 测试）+ Playwright（UI 测试）
# helpers/api.py 封装了 ApiHelper，helpers/ui.py 封装了 UiHelper
# 如果后端不可达，全部测试自动 skip（conftest.py 健康检查）
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
- **Locales** (`locales/`) — vue-i18n，`en.json` + `zh-CN.json`
- **样式** — UnoCSS（原子化 CSS + 自定义 shortcuts：`glass-card`、`btn-primary`、`input-glass` 等，定义在 `uno.config.ts`）。不使用组件库
- **路径别名** — `@/` 映射到 `./src/`（vite.config.ts + tsconfig.json）

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

### 后端单元测试 (`backend/tests/`)
- 使用 service 层直接调用（非 HTTP 级别），内存 SQLite + pytest-asyncio（auto mode）
- 每个测试获得独立数据库（conftest.py: `sqlite+aiosqlite://` 内存引擎）
- `seed_data` fixture 预建 org → team → user → project → iteration 层级
- 测试文件：test_spec_driven_flow、test_user_service、test_team_service、test_project_service、test_iteration_service、test_specification_service、test_clause_service、test_task_service、test_testcase_service、test_audit_service、test_pagination、test_edit_functionality

### 端到端测试 (`tests/`)
- HTTP 级 API 测试（requests）+ Playwright UI 测试
- `helpers/api.py`：ApiHelper 封装注册/登录、seed 数据创建
- `helpers/ui.py`：UiHelper 封装 Playwright 页面操作
- 测试文件按领域划分：test_auth、test_users、test_teams、test_projects、test_iterations、test_requirements、test_specifications、test_tasks、test_testcases、test_coverage、test_audit、test_webhooks、test_full_lifecycle、test_integration
- 前端目前无单元测试

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

**每次完成一个开发任务（修复 bug、添加功能、重构、样式调整等）后，必须使用 git-sync subagent 提交并推送代码。**

具体要求：
1. 完成任务代码修改后，不要等待用户指示，立即启动 git-sync subagent 执行提交和推送
2. 提交信息应简洁描述变更内容（中文或英文均可）
3. 即使是微小的样式修改或文本调整，也应提交
4. 唯一例外：用户明确要求"不要提交"或"稍后提交"时，跳过此步骤

## FastAPI 依赖注入注意事项

使用 `Annotated` + `Depends` 声明依赖时，**不要同时在默认值中再写 `Depends(...)`**，FastAPI 会抛出 `AssertionError`。

```python
# ❌ 错误 — Annotated 和默认值中都有 Depends
db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),

# ✅ 正确 — 只在 Annotated 中声明
db: Annotated[AsyncSession, Depends(get_db)],
```

**参数顺序：** `Annotated[..., Depends(...)]` 参数（无默认值）必须放在有默认值的参数（如 `search: str | None = None`）**之前**，否则 Python 会报 `SyntaxError`。

```python
# ❌ 错误 — 无默认值参数在有默认值参数之后
async def list_users(
    search: str | None = None,          # 有默认值
    db: Annotated[AsyncSession, Depends(get_db)],  # 无默认值 → SyntaxError
):

# ✅ 正确 — Depends 参数在前，可选查询参数在后
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    search: str | None = None,
):
```

项目中的统一写法是使用 `Annotated`，不加默认值。参见 `backend/app/routers/` 下所有路由文件。

## vue-i18n 注意事项

在 `frontend/src/locales/*.json` 中编写翻译文本时，**所有 `{` 和 `}` 必须转义**：
- 使用 `{'{'}` 代替 `{`，使用 `{'}'}` 代替 `}`
- vue-i18n 会将 `{ xxx }` 解析为插值占位符，未转义会导致 `SyntaxError: Invalid token in placeholder`
- 示例：`"msg": "配置 {'{'} key: value {'}'}"` → 显示为 `配置 { key: value }`
- `@` 符号同理，使用 `{'@'}` 转义

## 设计文档

- `docs/superpowers/specs/2026-03-29-dev-platform-design.md` — 完整系统设计规格（中文）
- `docs/superpowers/specs/2026-04-04-improvements-design.md` — 改进方案：分页、API 补全、审计日志、测试（4 阶段）
