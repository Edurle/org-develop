# 测试任务添加测试用例功能

## 概述

在需求详情页（RequirementDetailView）的测试任务展开区域添加"创建测试用例"按钮和模态框，支持填写测试用例基本信息并关联规格条款。

## 现状分析

- **后端**：`POST /api/test-tasks/{task_id}/test-cases` 已完整支持，接受 `clause_ids` 参数关联规格条款
- **前端 store**：`tcStore.create(testTaskId, data)` 已支持调用
- **前端 API**：`tcApi.create(testTaskId, data)` 已封装
- **缺失**：RequirementDetailView 中展开测试任务后，只有编辑/删除测试用例的操作，没有"创建测试用例"的 UI 入口

## 修改范围

仅修改前端，后端无需变更。

### 1. RequirementDetailView.vue

#### 状态变量（script setup）

新增：
- `showCreateTcModal` — 控制创建模态框显示
- `createTcTaskId` — 当前创建测试用例的目标测试任务 ID
- `newTcTitle`, `newTcPreconditions`, `newTcSteps`, `newTcExpected` — 表单字段
- `selectedClauseIds` — 已选中的条款 ID 列表（`ref<string[]>([])`)
- `availableClauses` — 可选条款列表（`ref<SpecClause[]>([])`）

#### 数据加载

在 `toggleTestTaskExpand` 展开测试任务时，额外加载该需求的所有 locked 规格版本中的条款：
1. 遍历 `specStore.specs` 中属于当前需求的规格
2. 对每个已加载 locked 版本的规格，调用 `specApi.listClauses(versionId)` 获取条款
3. 合并所有条款到 `availableClauses`

#### 模板修改

1. **展开区域**（`RequirementDetailView.vue:713` 附近）：在测试用例列表之前添加"Create Test Case"按钮
2. **创建模态框**：
   - 标题输入框（必填）
   - 前置条件 textarea（可选）
   - 测试步骤 textarea（必填）
   - 预期结果 textarea（必填）
   - 规格条款多选区域：按严重程度（must/should/may）分组展示条款 checkbox
3. **提交处理**：调用 `tcStore.create(expandedTestTaskId, { title, preconditions, steps, expected_result, clause_ids })`，成功后关闭模态框并刷新列表

### 2. i18n 翻译

在 `en.json` 和 `zh-CN.json` 的 `testcase` 命名空间下添加：
- `createTestCase` — 创建测试用例
- `newTestCase` — 新建测试用例
- `linkClauses` — 关联规格条款
- `noClausesAvailable` — 没有可用的条款（无 locked 规格版本时提示）

## 条款选择器设计

- 从当前需求的所有 locked 规格版本中聚合条款
- 按严重程度分组展示：must（红色）、should（黄色）、may（灰色）
- 每个条款显示 `clause_id + title`，勾选后加入 `selectedClauseIds`
- 仅在有可用条款时显示条款选择区域

## 不涉及

- 后端修改
- ProjectTasksView 页面
- 测试用例状态流转（已有）
