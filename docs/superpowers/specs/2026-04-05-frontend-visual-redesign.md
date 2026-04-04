# 前端视觉重设计方案

日期：2026-04-05

## 概述

对 OrgDev 平台前端进行全面视觉升级，采用「毛玻璃现代」设计风格，将现有的功能性 UI 转变为美观、优雅、专业的企业管理级界面。覆盖全站所有页面。

**目标用户**：企业管理层（产品经理、高管）

**设计关键词**：通透、轻盈、专业、有视觉冲击力

## 技术方案

**纯 UnoCSS 主题系统**，不引入外部 UI 库。通过 UnoCSS 自定义主题（theme）、快捷方式（shortcuts）和 `@keyframes` 动画实现全部视觉效果。

- 零外部依赖，bundle 最小
- 完全掌控视觉细节
- 与现有技术栈无缝集成

## 设计 Token

### 配色

| 用途 | 值 | 说明 |
|------|------|------|
| 主色 | `#2563eb` → `#06b6d4` 渐变 | 蓝青渐变，按钮、链接、选中态 |
| 成功 | `#10b981` | 完成状态、覆盖率达标 |
| 警告 | `#f59e0b` | 评审中、中优先级 |
| 危险 | `#ef4444` | 错误、删除、高优先级 |
| 信息 | `#8b5cf6` | 测试状态、团队成员 |
| 页面背景 | `#f0f4f8` | 浅蓝灰底色 |
| 卡片背景 | `rgba(255,255,255,0.7)` | 半透明白 + backdrop-filter |
| 主文字 | `#0f172a` | 标题 |
| 次文字 | `#64748b` | 正文、标签 |
| 辅助文字 | `#94a3b8` | 日期、占位 |

### 毛玻璃效果

三种级别：

| 级别 | background | backdrop-filter | border | 用途 |
|------|-----------|----------------|--------|------|
| 标准 | `rgba(255,255,255,0.7)` | `blur(12px)` | `rgba(37,99,235,0.08)` | 内容卡片、表格容器 |
| 导航栏 | `rgba(255,255,255,0.85)` | `blur(20px)` | `rgba(37,99,235,0.06)` | 顶部导航 |
| 登录卡片 | `rgba(255,255,255,0.08)` | `blur(24px)` | `rgba(255,255,255,0.12)` | 深色背景上的登录框 |

### 阴影

带蓝色调的柔和阴影，4 级：

| 级别 | box-shadow | 用途 |
|------|-----------|------|
| xs | `0 1px 3px rgba(37,99,235,0.04)` | 表格行 |
| sm | `0 4px 12px rgba(37,99,235,0.06)` | 卡片默认态 |
| md | `0 8px 24px rgba(37,99,235,0.08)` | 卡片悬浮态 |
| lg | `0 16px 40px rgba(37,99,235,0.12)` | 模态框、下拉菜单 |

### 圆角

统一使用 `rounded-lg` 系列：

| 元素 | 圆角 |
|------|------|
| 按钮 | `10px`（`rounded-[10px]`） |
| 输入框 | `10px` |
| 卡片 | `14-16px`（`rounded-[14px]`） |
| 徽章 | `20px`（`rounded-full` 胶囊） |
| 头像 | `50%`（圆形） |
| 模态框 | `20px`（`rounded-[20px]`） |

### 字体

使用系统字体栈，不引入自定义字体：

```
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
```

| 用途 | 大小 | 字重 |
|------|------|------|
| 页面标题 | 20px | 700 |
| 区域标题 | 14px | 700 |
| 正文 | 13px | 400 |
| 标签/辅助 | 11-12px | 500-600 |
| 徽章文字 | 10-11px | 600 |

## 布局变更

### 导航：侧栏 → 顶部导航栏

从固定左侧边栏改为顶部毛玻璃导航栏：

- 高度：56-60px
- 内容：左侧 Logo + 胶囊式导航切换器，右侧通知图标 + 用户头像
- 导航切换器：`rgba(37,99,235,0.04)` 底色，选中项白底 + 阴影凸起
- 吸顶效果（sticky），滚动时保持可见

### 内容区

- 最大宽度不限，充分利用横向空间
- 统计卡片使用 CSS Grid：4 列（仪表盘）、3 列（项目列表）
- 间距统一：`gap-3`（12px）

## 核心组件规范

### 按钮

| 类型 | 样式 |
|------|------|
| 主要 | `bg-gradient-135deg from-blue-600 to-blue-700` + 白字 + 蓝色阴影 |
| 次要 | 白底 + 蓝色边框 `rgba(37,99,235,0.2)` + 蓝字 |
| 幽灵 | `bg-blue-50` 无边框 + 蓝字 |
| 危险 | 红色渐变 + 红色阴影 |

三种尺寸：sm（12px/8px 14px）、default（13px/9px 20px）、lg（14px/11px 24px）

### 表单

- 输入框：毛玻璃背景 `rgba(255,255,255,0.7)` + 蓝色调边框 `rgba(37,99,235,0.12)` + 10px 圆角
- 聚焦态：边框加深 + 蓝色外发光
- 标签：12px/600 字重

### 状态徽章

胶囊形（`rounded-full`），每种状态对应颜色：

| 状态 | 背景 | 文字 | 边框 |
|------|------|------|------|
| draft | 灰色渐变 | `#64748b` | `rgba(100,116,139,0.15)` |
| spec_writing | 蓝色渐变 | `#2563eb` | `rgba(37,99,235,0.15)` |
| spec_review | 黄色渐变 | `#d97706` | `rgba(245,158,11,0.15)` |
| spec_locked | 绿色渐变 | `#059669` | `rgba(16,185,129,0.15)` |
| in_progress | 蓝色渐变（深） | `#2563eb` | `rgba(37,99,235,0.18)` |
| testing | 紫色渐变 | `#7c3aed` | `rgba(139,92,246,0.15)` |
| done | 绿色渐变（深） | `#059669` | `rgba(16,185,129,0.2)` |
| failed | 红色渐变 | `#dc2626` | `rgba(239,68,68,0.15)` |

背景均为 `linear-gradient(135deg, rgba(color,0.1), rgba(color,0.05))`。

### 表格

- 包裹在毛玻璃卡片中（`border-radius: 14px` + `overflow: hidden`）
- 表头：蓝青渐变极淡背景 `rgba(37,99,235,0.04)`
- 行分割线：`rgba(37,99,235,0.05)`
- 行悬浮：`rgba(37,99,235,0.01)`
- 带渐变头像圆点的负责人列

### 模态框

- 毛玻璃背景 + lg 级阴影
- 20px 圆角
- 遮罩层：`bg-black/30 backdrop-blur-sm`

## 页面设计

### 登录页

- 全屏深色渐变背景 `#0f172a → #1e3a5f → #0f4c75`
- 三个装饰性光晕球体（蓝/青/紫），`radial-gradient` + 定位
- 居中毛玻璃登录卡片（380px 宽，深色玻璃效果）
- 蓝色渐变登录按钮 + 蓝色阴影光晕
- 淡色文字/链接

### 仪表盘首页

- 个性化欢迎语「下午好，张三 👋」
- 4 列统计卡片：活跃项目、需求总数、测试覆盖、团队成员
  - 每张卡片带 emoji 图标容器（渐变底色圆角方块）
  - 趋势指标（绿色上升箭头 + 文字）
  - 覆盖率卡片带渐变进度条
  - 团队卡片带头像叠加组
- 2 列底部区域：
  - 左：近期活动流（彩色圆点 + 标题 + 时间）
  - 右：项目进度列表（渐变进度条 + 百分比）

### 项目列表页

- 标题栏 + 渐变「+ 新建项目」按钮
- 3 列项目卡片网格
- 每张卡片：
  - 渐变色首字母头像（42px 圆角方块）
  - 项目名 + 创建日期
  - 描述文本
  - 状态徽章 + 成员头像叠加组
  - 渐变进度条 + 需求统计

### 需求详情页

- 面包屑导航条
- 标题栏：需求名 + 状态徽章 + 编辑按钮
- 标签页：规格说明 / 开发任务 / 测试用例 / 覆盖率报告
  - 选中态：蓝色文字 + 底部 2px 蓝色边框
- 标签页内容：
  - 规格卡片：版本号、锁定状态、条款统计
  - 覆盖率概览：环形进度图 + must/should 双进度条
  - 条款列表：MUST（红底白字）/ SHOULD（黄底白字）标签 + 覆盖状态

## 动效系统

### 进场动画

通过 CSS `@keyframes` 实现，在 UnoCSS 中定义为工具类。

| 动画 | 效果 | 用途 |
|------|------|------|
| `fadeInUp` | 从下方 12px 淡入 | 统计卡片、列表项进场 |
| `fadeIn` | 纯透明度渐变 | 模态框、页面切换 |
| `scaleIn` | 从 95% 缩放至 100% | 卡片首次渲染 |
| `slideInRight` | 从右侧 20px 滑入 | 标签页内容切换 |
| `countUp` | 数字从 0 滚动至目标值 | 统计数字 |

### 交错动画

卡片列表使用 `animation-delay` 交错进场，间隔 80ms：

```
第1张: delay 0ms
第2张: delay 80ms
第3张: delay 160ms
...
```

通过 Vue 的 `:style="{ animationDelay: index * 80 + 'ms' }"` 实现。

### 过渡动画

| 元素 | 过渡 | 时长 |
|------|------|------|
| 按钮 hover | 背景色 + 阴影 + 微上移 `translateY(-1px)` | 150ms ease |
| 卡片 hover | 阴影升级 + 微上移 `translateY(-2px)` | 200ms ease |
| 导航项切换 | 背景色变化 | 200ms ease |
| 标签页切换 | 内容淡入 | 200ms ease |
| 进度条 | 宽度从 0% 到目标值 | 800ms ease-out |
| 模态框 | 缩放 + 淡入 | 200ms ease |

### 数字滚动

统计数字使用 CSS counter animation 或轻量 JS 实现：
- 从 0 计数到目标值
- 持续 800ms
- ease-out 缓动

## UnoCSS 配置方案

在 `uno.config.ts` 中扩展：

```typescript
export default defineConfig({
  presets: [presetUno(), presetAttributify()],
  theme: {
    colors: {
      primary: { DEFAULT: '#2563eb', light: '#3b82f6', dark: '#1d4ed8' },
      accent: '#06b6d4',
      surface: '#f0f4f8',
    },
    boxShadow: {
      'glass-xs': '0 1px 3px rgba(37,99,235,0.04)',
      'glass-sm': '0 4px 12px rgba(37,99,235,0.06)',
      'glass-md': '0 8px 24px rgba(37,99,235,0.08)',
      'glass-lg': '0 16px 40px rgba(37,99,235,0.12)',
    },
  },
  shortcuts: {
    'glass-card': 'bg-white/70 backdrop-blur-xl border border-blue-500/8 rounded-[14px] shadow-glass-sm',
    'glass-nav': 'bg-white/85 backdrop-blur-2xl border-b border-blue-500/6',
    'btn-primary': 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-[10px] font-semibold shadow-[0_2px_8px_rgba(37,99,235,0.3)] hover:shadow-[0_4px_16px_rgba(37,99,235,0.4)] hover:-translate-y-px transition-all duration-150',
    'btn-secondary': 'bg-white text-blue-600 border border-blue-500/20 rounded-[10px] font-medium hover:border-blue-500/40 transition-all duration-150',
    'btn-ghost': 'bg-blue-50 text-blue-600 rounded-[10px] font-medium hover:bg-blue-100 transition-all duration-150',
    'badge-base': 'px-2.5 py-1 rounded-full text-xs font-semibold border',
    'input-glass': 'w-full px-3.5 py-2.5 bg-white/70 backdrop-blur-sm border border-blue-500/12 rounded-[10px] text-sm outline-none focus:border-blue-500/30 focus:ring-2 focus:ring-blue-500/10 transition-all duration-150',
  },
})
```

## 涉及文件

需要修改的文件：

### 配置
- `frontend/uno.config.ts` — 添加主题色、阴影、快捷方式、动画定义

### 布局
- `frontend/src/App.vue` — 调整全局布局结构（侧栏 → 顶栏）
- `frontend/src/components/AppLayout.vue` — 重写为顶部导航布局
- `frontend/src/components/ProjectLayout.vue` — 调整为面包屑 + 标签页

### 组件
- `frontend/src/components/Modal.vue` — 毛玻璃效果 + 动画
- `frontend/src/components/StatusBadge.vue` — 新渐变徽章样式
- `frontend/src/components/EmptyState.vue` — 新视觉风格

### 页面
- `frontend/src/views/LoginView.vue` — 深色渐变背景 + 毛玻璃卡片
- `frontend/src/views/HomeView.vue` — 统计卡片 + 活动流 + 进度
- `frontend/src/views/ProjectsView.vue` — 卡片网格 + 新视觉
- `frontend/src/views/ProjectDetailView.vue` — 适配新布局
- `frontend/src/views/ProjectOverviewView.vue` — 新统计风格
- `frontend/src/views/RequirementListView.vue` — 新表格 + 筛选器
- `frontend/src/views/RequirementDetailView.vue` — 标签页 + 覆盖率环图
- `frontend/src/views/SpecificationDetailView.vue` — 新视觉
- `frontend/src/views/CoverageReportView.vue` — 进度条 + 新统计
- `frontend/src/views/ProjectTasksView.vue` — 新卡片/表格
- `frontend/src/views/ProjectMembersView.vue` — 新列表风格
- `frontend/src/views/ProjectSettingsView.vue` — 新表单风格
- `frontend/src/views/TeamsView.vue` — 新组织结构视觉

### 样式
- `frontend/src/main.ts` — 导入全局动画 keyframes（如需要）
- `frontend/src/assets/` — 可能需要添加全局 CSS 文件用于 `@keyframes` 定义

## 不做的事

- 不引入外部 UI 组件库
- 不引入外部动画库（如需要后续可增量添加 `@vueuse/motion`）
- 不改变路由结构或 API 接口
- 不改变业务逻辑
- 不做暗色模式（仅浅色毛玻璃主题）
- 不做响应式移动端适配（本次仅优化桌面端）
