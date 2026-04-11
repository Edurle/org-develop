# 团队成员 CRUD 设计

## 背景

当前 `TeamsView.vue`（团队与组织页面）只支持创建组织和团队，缺少团队成员管理功能。后端 API 已完整支持团队成员 CRUD（添加、列表、移除、修改角色），前端 API 层和类型定义也已就绪。需要在「团队与组织」页面中添加成员管理入口。

## 角色系统

### 新角色定义（6 种）

| 角色 | 标识 | 说明 |
|------|------|------|
| 团队管理员 | `team_admin` | 管理团队设置和成员 |
| 产品负责人 | `product_owner` | 创建/管理需求和规格 |
| 设计师 | `designer` | 参与规格编写和评审 |
| 开发者 | `developer` | 创建/修改开发任务 |
| 测试 | `tester` | 编写和执行测试用例 |
| 查看者 | `viewer` | 只读访问 |

### 变更范围

- 后端 `TeamMember` 模型的 `roles` 字段默认值从 `"developer"` 不变
- 后端 `TeamMemberCreate` schema 的 `roles` 默认值不变
- 前端角色选择器从 4 种（admin/member/viewer/developer）更新为 6 种
- `ProjectMembersView.vue` 的角色选项同步更新
- i18n 翻译文件添加新角色的翻译键

## UI 设计

### 团队卡片改造

每个团队卡片在现有内容下方增加：

1. **成员数量徽标**：显示「N 位成员」，可点击
2. **展开/折叠的成员面板**：
   - 点击徽标切换面板展开状态
   - 展开后加载该团队的成员列表（使用 `teamApi.membersDetail`）
   - 面板内包含：
     - 成员列表（头像首字母、姓名、角色标签、加入时间）
     - 每个成员行的操作：修改角色（下拉）、移除（带确认）
     - 底部「添加成员」按钮

### 添加成员 Modal

- 用户搜索框：输入用户名搜索（复用 `userApi.list`，300ms 防抖）
- 搜索结果列表：显示用户名和邮箱，点击选中
- 角色选择：6 种角色下拉选择
- 确认按钮

### 修改角色

- 点击成员的角色标签，弹出下拉选择器
- 选择新角色后直接保存（调用 `teamApi.updateMember`）

### 移除成员

- 点击移除按钮 → 确认 Modal
- 显示成员信息
- 确认后调用 `teamApi.removeMember`

## 不变部分

- 后端 API 路由：已完整，无需修改
- 后端 service 层：已有 `add_team_member`、`remove_team_member`、`update_team_member_role`
- 前端 API 层：`teamApi` 已有所有方法
- 前端类型：`TeamMember` 和 `TeamMemberDetail` 已定义

## 实现范围

### 后端变更（最小化）

无 API 层变更。仅确保现有 API 能正确处理新角色值（已支持，roles 是自由字符串）。

### 前端变更

1. **`frontend/src/views/TeamsView.vue`**：主要变更文件
   - 团队卡片增加成员面板（展开/折叠）
   - 集成添加成员 Modal
   - 集成修改角色下拉
   - 集成移除确认 Modal

2. **`frontend/src/views/ProjectMembersView.vue`**：角色选项同步更新

3. **`frontend/src/locales/en.json`** 和 **`zh-CN.json`**：
   - 添加 6 种角色的翻译键
   - 添加成员管理相关文本

### 测试

- 后端：无新增（现有 API 已测试）
- 前端：手动验证 TeamsView 的成员 CRUD 操作
