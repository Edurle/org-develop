# E2E 测试设计规格

## 目标

为 org-dev 规格驱动开发平台编写全面的端到端测试，覆盖：
- **所有 58 个后端 API 端点**（含请求/响应验证）
- **所有 12 个前端页面/视图**（含交互操作验证）
- **所有状态流转路径**（Requirement、SpecVersion、DevTask、TestCase 的全部合法/非法转换）

## 技术选型

- **框架**: Playwright + pytest
- **策略**: 完全数据隔离（每个测试独立创建资源）
- **后端**: 运行在 localhost:8000
- **前端**: 运行在 localhost:3000，代理 /api 到后端

## 文件结构

```
tests/
├── conftest.py              # 共享 fixtures
├── helpers/
│   ├── __init__.py
│   ├── api.py               # API 请求封装
│   └── ui.py                # UI 操作封装
├── test_auth.py             # 认证模块
├── test_users.py            # 用户模块
├── test_teams.py            # 组织与团队
├── test_projects.py         # 项目管理
├── test_iterations.py       # 迭代管理
├── test_requirements.py     # 需求管理
├── test_specifications.py   # 规格管理
├── test_tasks.py            # 任务管理
├── test_testcases.py        # 测试用例
├── test_coverage.py         # 覆盖率
├── test_webhooks.py         # Webhook
├── test_audit.py            # 审计日志
└── test_full_lifecycle.py   # 完整生命周期
```

## 共享基础设施

### conftest.py

提供以下 fixtures：

1. **`api_client`** — 封装 requests.Session，自动带 JWT token
   - 每个测试注册新用户并登录
   - 提供便捷方法：`create_org()`, `create_team()`, `create_project()`, `create_iteration()`
   - 返回 `ApiHelper` 实例，包含所有 58 个端点的方法

2. **`seed_data`** (autouse) — 自动创建基础层级数据
   - Organization → Team → Project → Iteration
   - 返回 `{org, team, project, iteration}` 字典
   - 测试内可按需覆盖或扩展

3. **`page`** — Playwright browser page（来自 pytest-playwright）
   - 自动导航到前端 URL
   - 提供已登录状态的 page（通过 API 登录后注入 token）

4. **`browser_logged_in`** — 已登录的浏览器页面
   - 通过 API 登录获取 token
   - 设置 localStorage 后刷新页面

### helpers/api.py

`ApiHelper` 类，封装所有 API 调用：

```python
class ApiHelper:
    # Auth
    def register(username, email, password, display_name=None) -> dict
    def login(username, password) -> dict
    def refresh_token(refresh_token) -> dict
    def create_api_key(name, scopes) -> dict
    def delete_api_key(key_id) -> None

    # Users
    def get_me() -> dict
    def update_me(**fields) -> dict
    def get_user(user_id) -> dict

    # Organizations
    def create_org(name, slug) -> dict
    def list_orgs() -> list

    # Teams
    def create_team(org_id, name, slug) -> dict
    def list_teams() -> list
    def add_team_member(team_id, user_id, roles) -> dict
    def list_team_members(team_id) -> list

    # Projects
    def create_project(team_id, name, slug, description=None) -> dict
    def list_projects(team_id=None) -> list
    def get_project(project_id) -> dict
    def update_project(project_id, **fields) -> dict
    def delete_project(project_id) -> None

    # Iterations
    def create_iteration(project_id, name, **fields) -> dict
    def list_iterations(project_id) -> list
    def update_iteration(project_id, iteration_id, **fields) -> dict

    # Requirements
    def create_requirement(project_id, iteration_id, title, priority="medium") -> dict
    def list_requirements(project_id, **filters) -> list
    def get_requirement(requirement_id) -> dict
    def update_requirement(requirement_id, **fields) -> dict
    def update_requirement_status(requirement_id, status) -> dict

    # Specifications
    def create_specification(requirement_id, spec_type, title) -> dict
    def list_specifications(requirement_id) -> list
    def create_spec_version(spec_id, version, content=None) -> dict
    def list_spec_versions(spec_id) -> list
    def submit_spec_version(version_id) -> dict
    def lock_spec_version(version_id) -> dict
    def reject_spec_version(version_id) -> dict
    def create_clause(version_id, clause_id, title, description, category, severity="must") -> dict
    def list_clauses(version_id) -> list

    # Tasks
    def create_dev_task(requirement_id, spec_version_id, iteration_id, title, estimate_hours=None) -> dict
    def list_dev_tasks(project_id) -> list
    def claim_dev_task(task_id) -> dict
    def update_dev_task_status(task_id, status) -> dict
    def create_test_task(requirement_id, iteration_id, title) -> dict
    def list_test_tasks(project_id) -> list

    # Test Cases
    def create_test_case(test_task_id, title, steps, expected_result, clause_ids=None) -> dict
    def list_test_cases(test_task_id) -> list
    def update_test_case_status(test_case_id, status) -> dict

    # Coverage
    def get_coverage(requirement_id) -> dict
    def check_coverage(requirement_id) -> dict

    # Webhooks
    def create_webhook(project_id, url, events, secret=None) -> dict
    def list_webhooks(project_id) -> list
    def delete_webhook(project_id, webhook_id) -> None
    def list_webhook_deliveries(webhook_id) -> list

    # Audit
    def list_audit_logs(**filters) -> dict  # 返回 PaginatedResponse
    def get_audit_log(log_id) -> dict
```

### helpers/ui.py

`UiHelper` 类，封装常见 UI 操作：

```python
class UiHelper:
    def __init__(self, page, base_url="http://localhost:3000")

    # 导航
    def goto_login()
    def goto_dashboard()
    def goto_teams()
    def goto_projects()
    def goto_project(project_id)
    def goto_project_requirements(project_id)
    def goto_project_tasks(project_id)
    def goto_project_members(project_id)
    def goto_project_settings(project_id)
    def goto_requirement(project_id, requirement_id)
    def goto_specification(project_id, requirement_id, spec_id)
    def goto_coverage(project_id, requirement_id)

    # 操作
    def login(username, password)  # 填写表单并提交
    def fill_modal_field(field_id, value)
    def click_button(text)
    def select_dropdown(field_id, value)
    def wait_for_api_response(url_pattern)
    def assert_toast_message(text)
    def assert_page_contains(text)
    def assert_status_badge(status)
```

## 测试覆盖矩阵

### test_auth.py (8 tests)

**API:**
1. `test_register_success` — 注册新用户，验证返回 access_token + refresh_token
2. `test_register_duplicate_username` — 重复用户名返回 409
3. `test_login_success` — 正确凭据登录
4. `test_login_wrong_password` — 错误密码返回 401
5. `test_refresh_token` — 刷新令牌
6. `test_create_api_key` — 创建 API 密钥，验证返回 key 前缀 `odk_`
7. `test_delete_api_key` — 删除 API 密钥

**UI:**
8. `test_login_page_ui` — 登录页面加载、输入、错误提示、成功跳转

### test_users.py (4 tests)

**API:**
1. `test_get_me` — 获取当前用户信息
2. `test_update_me` — 更新 display_name 和 email
3. `test_get_user_by_id` — 按 ID 获取用户
4. `test_get_user_not_found` — 不存在的用户返回 404

### test_teams.py (8 tests)

**API:**
1. `test_create_organization` — 创建组织
2. `test_list_organizations` — 列出组织
3. `test_create_team` — 创建团队
4. `test_list_teams` — 列出团队
5. `test_add_team_member` — 添加团队成员
6. `test_list_team_members` — 列出团队成员

**UI:**
7. `test_teams_page_create_org` — 通过 UI 创建组织
8. `test_teams_page_create_team` — 通过 UI 创建团队

### test_projects.py (12 tests)

**API:**
1. `test_create_project` — 创建项目
2. `test_list_projects` — 列出项目
3. `test_list_projects_filter_by_team` — 按 team_id 筛选
4. `test_get_project` — 获取项目详情
5. `test_update_project` — 更新项目名称/描述
6. `test_delete_project` — 删除项目

**UI:**
7. `test_projects_page_create` — 通过 UI 创建项目
8. `test_project_overview_inline_edit` — 内联编辑项目名称
9. `test_project_settings_edit` — 设置页面编辑项目
10. `test_project_settings_delete` — 设置页面删除项目（需确认）
11. `test_project_members_add` — 添加项目成员
12. `test_project_navigation` — 项目内 Tab 导航

### test_iterations.py (5 tests)

**API:**
1. `test_create_iteration` — 创建迭代
2. `test_list_iterations` — 列出迭代
3. `test_update_iteration` — 更新迭代
4. `test_iteration_status_planning_to_active` — planning → active
5. `test_iteration_status_active_to_completed` — active → completed

### test_requirements.py (14 tests)

**API:**
1. `test_create_requirement` — 创建需求（默认 medium 优先级）
2. `test_create_requirement_high_priority` — 创建高优先级需求
3. `test_list_requirements` — 列出需求
4. `test_list_requirements_filter_by_status` — 按状态筛选
5. `test_list_requirements_filter_by_iteration` — 按迭代筛选
6. `test_get_requirement` — 获取需求详情
7. `test_update_requirement` — 更新需求标题
8. `test_status_draft_to_spec_writing` — draft → spec_writing
9. `test_status_spec_writing_to_spec_review` — spec_writing → spec_review
10. `test_status_spec_review_to_spec_locked` — spec_review → spec_locked（所有 spec locked 后自动转换）
11. `test_status_spec_locked_to_in_progress` — spec_locked → in_progress
12. `test_status_in_progress_to_testing` — in_progress → testing
13. `test_status_testing_to_done` — testing → done（需覆盖率达标）
14. `test_status_invalid_transition` — 非法状态转换返回 400

**UI:**
15. `test_requirements_page_create` — 通过 UI 创建需求
16. `test_requirements_page_filter` — 通过 UI 筛选需求
17. `test_requirement_detail_status_transitions` — UI 上操作状态流转按钮

### test_specifications.py (14 tests)

**API:**
1. `test_create_specification_api_type` — 创建 API 类型规格
2. `test_create_specification_data_type` — 创建 Data 类型规格
3. `test_create_specification_flow_type` — 创建 Flow 类型规格
4. `test_create_specification_ui_type` — 创建 UI 类型规格
5. `test_list_specifications` — 列出规格
6. `test_create_spec_version` — 创建规格版本
7. `test_list_spec_versions` — 列出版本
8. `test_submit_spec_version` — 提交评审 draft → reviewing
9. `test_lock_spec_version` — 锁定 reviewing → locked
10. `test_reject_spec_version` — 拒绝 reviewing → draft
11. `test_create_clause` — 创建条款
12. `test_list_clauses` — 列出条款
13. `test_clause_severity_must_should_may` — 三种严重级别
14. `test_spec_locked_immutable` — 锁定版本不可修改

**UI:**
15. `test_spec_detail_create_version` — UI 创建版本
16. `test_spec_detail_add_clause` — UI 添加条款
17. `test_spec_detail_submit_and_lock` — UI 提交并锁定

### test_tasks.py (10 tests)

**API:**
1. `test_create_dev_task` — 创建开发任务（需 spec_locked 状态）
2. `test_create_dev_task_before_spec_locked_fails` — spec 未锁定时创建失败
3. `test_list_dev_tasks` — 列出开发任务
4. `test_claim_dev_task` — 认领任务 open → in_progress
5. `test_dev_task_status_open_to_in_progress` — 状态转换
6. `test_dev_task_status_in_progress_to_review` — 状态转换
7. `test_dev_task_status_review_to_done` — 状态转换
8. `test_dev_task_status_to_blocked` — 转为 blocked
9. `test_create_test_task` — 创建测试任务
10. `test_list_test_tasks` — 列出测试任务

**UI:**
11. `test_project_tasks_claim` — UI 认领任务
12. `test_project_tasks_status_change` — UI 变更任务状态

### test_testcases.py (6 tests)

**API:**
1. `test_create_test_case` — 创建测试用例
2. `test_create_test_case_with_clause_ids` — 关联条款
3. `test_list_test_cases` — 列出测试用例
4. `test_update_test_case_passed` — pending → running → passed
5. `test_update_test_case_failed` — pending → running → failed
6. `test_update_test_case_blocked` — pending → running → blocked

### test_coverage.py (6 tests)

**API:**
1. `test_get_coverage_report` — 获取覆盖率报告
2. `test_coverage_check_sufficient` — 覆盖率充足（must 100%, should ≥80%）
3. `test_coverage_check_insufficient_must` — must 覆盖不足
4. `test_coverage_check_insufficient_should` — should 覆盖不足
5. `test_coverage_empty_no_clauses` — 无条款时 0%
6. `test_cannot_mark_done_without_coverage` — 覆盖率不足无法完成需求

**UI:**
7. `test_coverage_report_page` — UI 查看覆盖率报告

### test_webhooks.py (5 tests)

**API:**
1. `test_create_webhook` — 创建 webhook
2. `test_list_webhooks` — 列出 webhook
3. `test_delete_webhook` — 删除 webhook
4. `test_webhook_deliveries` — 查看投递记录
5. `test_webhook_event_triggered` — 创建需求触发 webhook

### test_audit.py (4 tests)

**API:**
1. `test_list_audit_logs` — 列出审计日志（分页）
2. `test_filter_audit_by_resource_type` — 按资源类型筛选
3. `test_filter_audit_by_action` — 按操作类型筛选
4. `test_get_audit_log` — 获取单条审计日志

### test_full_lifecycle.py (5 tests)

1. `test_happy_path` — 完整正向流程：注册 → 创建组织/团队/项目/迭代 → 创建需求 → 编写规格 → 添加条款 → 提交评审 → 锁定 → 创建开发任务 → 认领并完成 → 创建测试任务 → 添加测试用例 → 运行测试 → 覆盖率达标 → 标记完成
2. `test_spec_rejection_flow` — 规格被拒绝后修改重新提交
3. `test_insufficient_coverage_blocks_done` — 覆盖率不足阻止完成
4. `test_cancelled_requirement` — 需求取消流程
5. `test_full_lifecycle_via_ui` — 通过 UI 走完主要流程

## 运行方式

```bash
# 启动后端
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 启动前端
cd frontend && npm run dev &

# 运行全部 e2e 测试
cd tests && pytest -v

# 运行单个模块
cd tests && pytest test_auth.py -v

# 运行完整生命周期测试
cd tests && pytest test_full_lifecycle.py -v

# 仅运行 UI 测试
cd tests && pytest -v -k "ui"
```

## 关键设计决策

1. **数据隔离**: 每个测试注册新用户、创建独立资源层级，避免测试间干扰
2. **API helper 封装**: 所有 API 调用统一封装，修改端点只需改一处
3. **UI helper 封装**: 页面操作统一封装，选择器变更只需改一处
4. **混合测试**: 同一模块的 API 测试和 UI 测试放在同一文件，便于对照
5. **生命周期测试**: 独立的 `test_full_lifecycle.py` 验证跨模块的完整工作流
