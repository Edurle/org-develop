# 编辑功能补全设计

## 背景

前端当前对需求、规范条款、任务、测试用例仅支持创建和状态流转，缺少字段编辑和删除功能。后端 schemas 已定义但大多无对应路由端点。

## 范围

前后端同步补全，模态框编辑交互，部分实体支持删除（带状态守卫）。

## 后端新增端点

### 需求 (Requirements)

- `PATCH /api/requirements/{id}` — 编辑 title、priority
  - 使用已有 `RequirementUpdate` schema
  - Service 层添加 `update_requirement()` 方法
  - 记录审计日志
- `DELETE /api/requirements/{id}` — 软删除
  - 仅 `draft` / `cancelled` 状态可删
  - Service 层添加 `delete_requirement()` 方法

### 规范条款 (Spec Clauses)

- `PATCH /api/spec-clauses/{id}` — 编辑 clause_id、title、description、category、severity
  - 使用已有 `SpecClauseUpdate` schema
  - 仅 draft 版本的条款可编辑
  - Service 层添加 `update_clause()` 方法
- `DELETE /api/spec-clauses/{id}` — 删除条款
  - 仅 draft 版本的条款可删除

### 开发任务 (Dev Tasks)

- `PATCH /api/dev-tasks/{id}` — 编辑 title、estimate_hours、assignee_id
  - 使用已有 `DevTaskUpdate` schema
  - Service 层添加 `update_dev_task()` 方法
- `DELETE /api/dev-tasks/{id}` — 删除
  - 仅 `open` 状态可删

### 测试用例 (Test Cases)

- `PATCH /api/test-cases/{id}` — 编辑 title、preconditions、steps、expected_result、actual_result
  - 使用已有 `TestCaseUpdate` schema
  - Service 层添加 `update_test_case()` 方法
- `DELETE /api/test-cases/{id}` — 删除
  - 仅 `pending` 状态可删

## 前端改动

### API 层 (`api/endpoints.ts`)

新增端点函数：
- `updateRequirement(id, data)` → PATCH /requirements/{id}
- `deleteRequirement(id)` → DELETE /requirements/{id}
- `updateClause(id, data)` → PATCH /spec-clauses/{id}
- `deleteClause(id)` → DELETE /spec-clauses/{id}
- `updateDevTask(id, data)` → PATCH /dev-tasks/{id}
- `deleteDevTask(id)` → DELETE /dev-tasks/{id}
- `updateTestCase(id, data)` → PATCH /test-cases/{id}
- `deleteTestCase(id)` → DELETE /test-cases/{id}

### Store 层

每个 store 添加 `update()` 和 `remove()` action：
- `requirement.ts` — `update(id, data)`, `remove(id)`
- `specification.ts` — `updateClause(id, data)`, `removeClause(id)`
- `task.ts` — `updateDevTask(id, data)`, `removeDevTask(id)`
- `testcase.ts` — `update(id, data)`, `remove(id)`

### 视图层

**需求列表页 (RequirementListView.vue)**
- 表格 Actions 列：现有 View 按钮旁加 Edit / Delete 按钮
- 编辑复用创建 Modal（双模式：创建时标题 "New Requirement"，编辑时 "Edit Requirement"，预填数据）
- Delete 按钮仅 draft/cancelled 状态显示

**需求详情页 (RequirementDetailView.vue)**
- 标题旁加 Edit 按钮
- Dev Tasks tab 表格每行加 Edit / Delete 按钮（Delete 仅 open 状态）
- Test Tasks tab 展开的测试用例每行加 Edit / Delete 按钮（Delete 仅 pending 状态）

**规范详情页 (SpecificationDetailView.vue)**
- 条款表格每行加 Edit / Delete 按钮（仅 draft 版本时显示）
- 编辑复用 Add Clause Modal

## 状态守卫

| 实体 | 可编辑条件 | 可删除条件 |
|---|---|---|
| 需求 | 任何状态 | draft / cancelled |
| 条款 | 所属版本为 draft | 所属版本为 draft |
| 开发任务 | 任何状态 | open |
| 测试用例 | 任何状态 | pending |

## 不做的事

- 不为规范版本/规范本身添加删除（符合规格不可变原则）
- 不为测试任务添加删除（测试任务通过其测试用例管理）
- 不添加批量编辑/删除
- 不修改已有状态流转逻辑
