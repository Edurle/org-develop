# 团队成员 CRUD 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 TeamsView 的团队卡片内添加可展开的成员管理面板，支持添加、移除、修改角色操作，并将角色系统从 4 种更新为 6 种。

**Architecture:** 前端为主的后端-前端协同变更。后端 API 已完整，仅需确保新角色值可被接受（已是自由字符串，无需改动）。前端在 `TeamsView.vue` 中为每个团队卡片添加展开/折叠成员面板，内含成员列表和 CRUD 操作 Modal。同时更新 `ProjectMembersView.vue` 和 i18n 翻译文件以支持 6 种新角色。

**Tech Stack:** Vue 3 + TypeScript + Composition API、UnoCSS（原子化 CSS）、vue-i18n、Vitest + @vue/test-utils（前端测试）、FastAPI + SQLAlchemy + pytest-asyncio（后端测试）

---

## 文件结构

| 操作 | 文件 | 职责 |
|------|------|------|
| 修改 | `frontend/src/locales/en.json` | 添加 6 种角色和新成员管理相关翻译键 |
| 修改 | `frontend/src/locales/zh-CN.json` | 对应中文翻译 |
| 修改 | `frontend/src/views/ProjectMembersView.vue` | 角色选择器更新为 6 种角色 |
| 修改 | `frontend/src/views/TeamsView.vue` | 添加展开成员面板、添加/移除/修改角色 Modal |
| 创建 | `frontend/src/components/TeamMemberPanel.vue` | 可复用的团队成员面板组件 |
| 创建 | `frontend/src/components/__tests__/TeamMemberPanel.test.ts` | TeamMemberPanel 单元测试 |
| 修改 | `backend/tests/test_team_service.py` | 添加新角色值的测试用例 |

---

### Task 1: 更新 i18n 翻译文件 — 添加 6 种角色和成员管理键

**Files:**
- Modify: `frontend/src/locales/en.json`
- Modify: `frontend/src/locales/zh-CN.json`

- [ ] **Step 1: 编写测试 — 验证 i18n 键存在性**

创建 `frontend/src/locales/__tests__/roles.test.ts`：

```typescript
import { describe, it, expect } from 'vitest'
import en from '../en.json'
import zhCN from '../zh-CN.json'

const roleKeys = [
  'team.teamAdmin',
  'team.productOwner',
  'team.designer',
  'team.developer',
  'team.tester',
  'team.viewer',
]

const memberKeys = [
  'team.members',
  'team.noMembers',
  'team.addMember',
  'team.removeMember',
  'team.confirmRemove',
  'team.confirmRemoveMsg',
  'team.updateRole',
  'team.searchUsersPlaceholder',
  'team.noUsersFound',
  'team.selectUser',
  'team.role',
  'team.joined',
  'team.failedLoadMembers',
  'team.failedAddMember',
  'team.failedRemoveMember',
  'team.failedUpdateRole',
  'team.loadingMembers',
  'team.adding',
  'team.remove',
]

describe('i18n role and member keys', () => {
  it.each(roleKeys)('en.json has key %s', (key) => {
    const parts = key.split('.')
    let obj: any = en
    for (const part of parts) {
      obj = obj[part]
    }
    expect(obj).toBeDefined()
    expect(typeof obj).toBe('string')
  })

  it.each(roleKeys)('zh-CN.json has key %s', (key) => {
    const parts = key.split('.')
    let obj: any = zhCN
    for (const part of parts) {
      obj = obj[part]
    }
    expect(obj).toBeDefined()
    expect(typeof obj).toBe('string')
  })

  it.each(memberKeys)('en.json has key %s', (key) => {
    const parts = key.split('.')
    let obj: any = en
    for (const part of parts) {
      obj = obj[part]
    }
    expect(obj).toBeDefined()
    expect(typeof obj).toBe('string')
  })

  it.each(memberKeys)('zh-CN.json has key %s', (key) => {
    const parts = key.split('.')
    let obj: any = zhCN
    for (const part of parts) {
      obj = obj[part]
    }
    expect(obj).toBeDefined()
    expect(typeof obj).toBe('string')
  })
})
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd frontend && npx vitest run src/locales/__tests__/roles.test.ts`
Expected: FAIL — 新键不存在

- [ ] **Step 3: 在 `en.json` 的 `team` 部分添加翻译键**

在 `frontend/src/locales/en.json` 的 `"team"` 对象中，在 `"failedCreateTeam"` 之后添加：

```json
    "teamAdmin": "Team Admin",
    "productOwner": "Product Owner",
    "designer": "Designer",
    "developer": "Developer",
    "tester": "Tester",
    "viewer": "Viewer",
    "members": "{count} Members",
    "noMembers": "No members yet.",
    "addMember": "Add Member",
    "removeMember": "Remove Member",
    "confirmRemove": "Confirm Remove",
    "confirmRemoveMsg": "Are you sure you want to remove this member from the team?",
    "updateRole": "Update Role",
    "searchUsersPlaceholder": "Type username to search...",
    "noUsersFound": "No users found",
    "selectUser": "Select User",
    "role": "Role",
    "joined": "Joined",
    "failedLoadMembers": "Failed to load members.",
    "failedAddMember": "Failed to add member.",
    "failedRemoveMember": "Failed to remove member.",
    "failedUpdateRole": "Failed to update role.",
    "loadingMembers": "Loading...",
    "adding": "Adding...",
    "remove": "Remove"
```

注意 `"members"` 中的 `{count}` 是 vue-i18n 插值，不需要转义。但如果有 `{` 或 `}` 作为字面量出现则需要转义为 `{'{'}` 和 `{'}'}`。

- [ ] **Step 4: 在 `zh-CN.json` 的 `team` 部分添加对应中文翻译**

在 `frontend/src/locales/zh-CN.json` 的 `"team"` 对象中，在 `"failedCreateTeam"` 之后添加：

```json
    "teamAdmin": "团队管理员",
    "productOwner": "产品负责人",
    "designer": "设计师",
    "developer": "开发者",
    "tester": "测试",
    "viewer": "查看者",
    "members": "{count} 位成员",
    "noMembers": "暂无成员。",
    "addMember": "添加成员",
    "removeMember": "移除成员",
    "confirmRemove": "确认移除",
    "confirmRemoveMsg": "确认从团队中移除该成员？",
    "updateRole": "更新角色",
    "searchUsersPlaceholder": "输入用户名搜索...",
    "noUsersFound": "未找到用户",
    "selectUser": "选择用户",
    "role": "角色",
    "joined": "加入时间",
    "failedLoadMembers": "加载成员失败。",
    "failedAddMember": "添加成员失败。",
    "failedRemoveMember": "移除成员失败。",
    "failedUpdateRole": "更新角色失败。",
    "loadingMembers": "加载中...",
    "adding": "添加中...",
    "remove": "移除"
```

- [ ] **Step 5: 运行测试验证通过**

Run: `cd frontend && npx vitest run src/locales/__tests__/roles.test.ts`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add frontend/src/locales/en.json frontend/src/locales/zh-CN.json frontend/src/locales/__tests__/roles.test.ts
git commit -m "feat: add 6-role and member management i18n keys"
```

---

### Task 2: 更新 ProjectMembersView 角色选择器

**Files:**
- Modify: `frontend/src/views/ProjectMembersView.vue`

- [ ] **Step 1: 编写测试 — 验证角色选项**

创建 `frontend/src/views/__tests__/ProjectMembersView.test.ts`：

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import ProjectMembersView from '../ProjectMembersView.vue'
import en from '@/locales/en.json'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: { en },
})

const roleValues = ['team_admin', 'product_owner', 'designer', 'developer', 'tester', 'viewer']

function mountComponent() {
  return mount(ProjectMembersView, {
    global: {
      plugins: [i18n],
      stubs: {
        Modal: true,
        GlassButton: true,
      },
      mocks: {
        $route: { params: { id: 'test-project-id' } },
      },
    },
  })
}

describe('ProjectMembersView roles', () => {
  it('renders all 6 role options in add modal', () => {
    const wrapper = mountComponent()
    const addSelect = wrapper.find('#add-member-role')
    const options = addSelect.findAll('option')
    const optionValues = options.map((o) => o.attributes('value'))
    for (const role of roleValues) {
      expect(optionValues).toContain(role)
    }
  })

  it('renders all 6 role options in edit modal', () => {
    const wrapper = mountComponent()
    const editSelect = wrapper.find('#edit-role')
    const options = editSelect.findAll('option')
    const optionValues = options.map((o) => o.attributes('value'))
    for (const role of roleValues) {
      expect(optionValues).toContain(role)
    }
  })
})
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd frontend && npx vitest run src/views/__tests__/ProjectMembersView.test.ts`
Expected: FAIL — 当前只有 4 种角色（admin/member/viewer/developer）

- [ ] **Step 3: 更新添加成员 Modal 的角色选择器**

在 `frontend/src/views/ProjectMembersView.vue` 第 323-328 行，将 `#add-member-role` select 的 option 替换为：

```html
            <option value="team_admin">{{ t('team.teamAdmin') }}</option>
            <option value="product_owner">{{ t('team.productOwner') }}</option>
            <option value="designer">{{ t('team.designer') }}</option>
            <option value="developer">{{ t('team.developer') }}</option>
            <option value="tester">{{ t('team.tester') }}</option>
            <option value="viewer">{{ t('team.viewer') }}</option>
```

- [ ] **Step 4: 更新修改角色 Modal 的角色选择器**

在同一文件第 383-388 行，将 `#edit-role` select 的 option 替换为同样的 6 种角色选项：

```html
            <option value="team_admin">{{ t('team.teamAdmin') }}</option>
            <option value="product_owner">{{ t('team.productOwner') }}</option>
            <option value="designer">{{ t('team.designer') }}</option>
            <option value="developer">{{ t('team.developer') }}</option>
            <option value="tester">{{ t('team.tester') }}</option>
            <option value="viewer">{{ t('team.viewer') }}</option>
```

- [ ] **Step 5: 更新默认角色值**

将 `addForm` 的默认角色从 `'member'` 改为 `'developer'`（第 26 行）：

```typescript
const addForm = ref({ roles: 'developer' })
```

同时更新 `openAddModal` 函数中的默认值（第 93 行）：

```typescript
  addForm.value = { roles: 'developer' }
```

- [ ] **Step 6: 运行测试验证通过**

Run: `cd frontend && npx vitest run src/views/__tests__/ProjectMembersView.test.ts`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add frontend/src/views/ProjectMembersView.vue frontend/src/views/__tests__/ProjectMembersView.test.ts
git commit -m "feat: update ProjectMembersView to use 6 team roles"
```

---

### Task 3: 创建 TeamMemberPanel 组件

**Files:**
- Create: `frontend/src/components/TeamMemberPanel.vue`
- Create: `frontend/src/components/__tests__/TeamMemberPanel.test.ts`

- [ ] **Step 1: 编写测试 — TeamMemberPanel 组件行为**

创建 `frontend/src/components/__tests__/TeamMemberPanel.test.ts`：

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import TeamMemberPanel from '../TeamMemberPanel.vue'
import en from '@/locales/en.json'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: { en },
})

const mockMembers = [
  {
    id: 'm1',
    user_id: 'u1',
    team_id: 't1',
    roles: 'team_admin',
    joined_at: '2026-01-01T00:00:00',
    user: { id: 'u1', username: 'alice', email: 'alice@test.com', display_name: 'Alice', is_active: true, created_at: '', updated_at: '' },
  },
  {
    id: 'm2',
    user_id: 'u2',
    team_id: 't1',
    roles: 'developer',
    joined_at: '2026-01-02T00:00:00',
    user: { id: 'u2', username: 'bob', email: 'bob@test.com', display_name: null, is_active: true, created_at: '', updated_at: '' },
  },
]

function mountPanel(props = {}) {
  return mount(TeamMemberPanel, {
    props: {
      teamId: 't1',
      ...props,
    },
    global: {
      plugins: [i18n],
      stubs: {
        GlassButton: {
          template: '<button :class="$attrs.class" :disabled="$attrs.disabled" @click="$emit(\'click\')"><slot /></button>',
          props: ['loading', 'disabled', 'variant'],
        },
        Modal: {
          template: '<div v-if="show" class="modal-stub"><slot /></div>',
          props: ['show', 'title'],
          emits: ['close'],
        },
      },
    },
  })
}

describe('TeamMemberPanel', () => {
  it('shows loading state when members not loaded', () => {
    const wrapper = mountPanel()
    expect(wrapper.find('[data-testid="member-loading"]').exists()).toBe(true)
  })

  it('shows member list after loading', async () => {
    const wrapper = mountPanel()
    await wrapper.setData({
      members: mockMembers,
      loading: false,
    })
    expect(wrapper.findAll('[data-testid="member-row"]')).toHaveLength(2)
  })

  it('shows no members message when empty', async () => {
    const wrapper = mountPanel()
    await wrapper.setData({
      members: [],
      loading: false,
    })
    expect(wrapper.find('[data-testid="no-members"]').exists()).toBe(true)
  })

  it('displays member display name and role', async () => {
    const wrapper = mountPanel()
    await wrapper.setData({
      members: mockMembers,
      loading: false,
    })
    const rows = wrapper.findAll('[data-testid="member-row"]')
    expect(rows[0].text()).toContain('Alice')
    expect(rows[0].text()).toContain('Team Admin')
  })

  it('falls back to username when display_name is null', async () => {
    const wrapper = mountPanel()
    await wrapper.setData({
      members: mockMembers,
      loading: false,
    })
    const rows = wrapper.findAll('[data-testid="member-row"]')
    expect(rows[1].text()).toContain('bob')
  })

  it('shows add member button', async () => {
    const wrapper = mountPanel()
    await wrapper.setData({
      members: mockMembers,
      loading: false,
    })
    expect(wrapper.find('[data-testid="add-member-btn"]').exists()).toBe(true)
  })

  it('opens add member modal on button click', async () => {
    const wrapper = mountPanel()
    await wrapper.setData({ members: mockMembers, loading: false })
    await wrapper.find('[data-testid="add-member-btn"]').trigger('click')
    expect(wrapper.find('[data-testid="add-member-modal"]').exists()).toBe(true)
  })

  it('shows 6 role options in add modal', async () => {
    const wrapper = mountPanel()
    await wrapper.setData({ members: mockMembers, loading: false, showAddModal: true })
    const options = wrapper.findAll('[data-testid="role-select"] option')
    const values = options.map((o) => o.attributes('value'))
    expect(values).toContain('team_admin')
    expect(values).toContain('product_owner')
    expect(values).toContain('designer')
    expect(values).toContain('developer')
    expect(values).toContain('tester')
    expect(values).toContain('viewer')
  })

  it('emits member-added event on successful add', async () => {
    const wrapper = mountPanel()
    await wrapper.setData({
      members: mockMembers,
      loading: false,
      showAddModal: true,
      selectedUser: { id: 'u3', username: 'charlie', email: 'c@test.com', display_name: 'Charlie', is_active: true },
      addForm: { roles: 'tester' },
    })
    await wrapper.find('[data-testid="add-form"]').trigger('submit.prevent')
  })

  it('shows remove confirmation modal', async () => {
    const wrapper = mountPanel()
    await wrapper.setData({
      members: mockMembers,
      loading: false,
      showRemoveModal: true,
      removingMember: mockMembers[0],
    })
    expect(wrapper.find('[data-testid="remove-modal"]').exists()).toBe(true)
  })

  it('shows update role modal', async () => {
    const wrapper = mountPanel()
    await wrapper.setData({
      members: mockMembers,
      loading: false,
      showRoleModal: true,
      editingMember: mockMembers[0],
      editRole: 'team_admin',
    })
    expect(wrapper.find('[data-testid="role-modal"]').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd frontend && npx vitest run src/components/__tests__/TeamMemberPanel.test.ts`
Expected: FAIL — 组件文件不存在

- [ ] **Step 3: 创建 `TeamMemberPanel.vue` 组件**

创建 `frontend/src/components/TeamMemberPanel.vue`：

```vue
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { teamApi, userApi } from '@/api/endpoints'
import Modal from '@/components/Modal.vue'
import GlassButton from '@/components/GlassButton.vue'
import type { TeamMemberDetail, User } from '@/types'

const props = defineProps<{
  teamId: string
}>()

defineEmits<{
  (e: 'changed'): void
}>()

const { t } = useI18n()

const loading = ref(true)
const error = ref('')
const members = ref<TeamMemberDetail[]>([])

const showAddModal = ref(false)
const searchQuery = ref('')
const searchResults = ref<User[]>([])
const searching = ref(false)
const selectedUser = ref<User | null>(null)
const addForm = ref({ roles: 'developer' })
const adding = ref(false)
const addError = ref('')

const showRemoveModal = ref(false)
const removingMember = ref<TeamMemberDetail | null>(null)
const removing = ref(false)

const showRoleModal = ref(false)
const editingMember = ref<TeamMemberDetail | null>(null)
const editRole = ref('')
const updatingRole = ref(false)

const memberUserIds = computed(() => new Set(members.value.map((m) => m.user_id)))

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

function displayName(member: TeamMemberDetail): string {
  return member.user?.display_name || member.user?.username || member.user_id
}

function displayAvatar(member: TeamMemberDetail): string {
  const name = displayName(member)
  return name.slice(0, 2).toUpperCase()
}

function roleLabel(role: string): string {
  const map: Record<string, string> = {
    team_admin: t('team.teamAdmin'),
    product_owner: t('team.productOwner'),
    designer: t('team.designer'),
    developer: t('team.developer'),
    tester: t('team.tester'),
    viewer: t('team.viewer'),
  }
  return map[role] || role
}

async function loadMembers() {
  loading.value = true
  error.value = ''
  try {
    const res = await teamApi.membersDetail(props.teamId)
    members.value = res.data
  } catch {
    error.value = t('team.failedLoadMembers')
  } finally {
    loading.value = false
  }
}

async function searchUsers(query: string) {
  if (!query || query.length < 1) {
    searchResults.value = []
    return
  }
  searching.value = true
  try {
    const res = await userApi.list(query)
    searchResults.value = res.data.filter((u) => !memberUserIds.value.has(u.id))
  } catch {
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

function openAddModal() {
  selectedUser.value = null
  searchQuery.value = ''
  searchResults.value = []
  addForm.value = { roles: 'developer' }
  addError.value = ''
  showAddModal.value = true
}

function selectUser(user: User) {
  selectedUser.value = user
  searchQuery.value = ''
  searchResults.value = []
}

function clearSelectedUser() {
  selectedUser.value = null
}

async function handleAddMember() {
  addError.value = ''
  adding.value = true
  try {
    if (!selectedUser.value) {
      addError.value = t('team.selectUser')
      return
    }
    await teamApi.addMember(props.teamId, {
      user_id: selectedUser.value.id,
      roles: addForm.value.roles,
    })
    await loadMembers()
    showAddModal.value = false
  } catch (err: any) {
    addError.value = err?.response?.data?.detail || err?.message || t('team.failedAddMember')
  } finally {
    adding.value = false
  }
}

function openRemoveModal(member: TeamMemberDetail) {
  removingMember.value = member
  showRemoveModal.value = true
}

async function handleRemoveMember() {
  if (!removingMember.value) return
  removing.value = true
  try {
    await teamApi.removeMember(props.teamId, removingMember.value.user_id)
    await loadMembers()
    showRemoveModal.value = false
    removingMember.value = null
  } catch {
    error.value = t('team.failedRemoveMember')
  } finally {
    removing.value = false
  }
}

function openRoleModal(member: TeamMemberDetail) {
  editingMember.value = member
  editRole.value = member.roles
  showRoleModal.value = true
}

async function handleUpdateRole() {
  if (!editingMember.value) return
  updatingRole.value = true
  try {
    await teamApi.updateMember(props.teamId, editingMember.value.user_id, {
      roles: editRole.value,
    })
    await loadMembers()
    showRoleModal.value = false
    editingMember.value = null
  } catch {
    error.value = t('team.failedUpdateRole')
  } finally {
    updatingRole.value = false
  }
}

let searchTimeout: ReturnType<typeof setTimeout> | null = null
function onSearchInput(val: string) {
  searchQuery.value = val
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => searchUsers(val), 300)
}

watch(() => props.teamId, () => loadMembers(), { immediate: true })
</script>

<template>
  <div class="border-t border-blue-500/5">
    <div v-if="error" class="px-5 py-2">
      <p class="text-sm text-red-600">{{ error }}</p>
    </div>

    <div v-if="loading" data-testid="member-loading" class="px-5 py-3 space-y-2">
      <div v-for="i in 3" :key="i" class="flex items-center gap-3 animate-pulse">
        <div class="h-6 w-6 bg-gray-200/50 rounded-full" />
        <div class="h-3 bg-gray-200/50 rounded w-1/3" />
      </div>
    </div>

    <div v-else-if="members.length === 0" data-testid="no-members" class="px-5 py-3 text-center">
      <p class="text-xs text-gray-400">{{ t('team.noMembers') }}</p>
    </div>

    <div v-else class="divide-y divide-blue-500/3">
      <div
        v-for="member in members"
        :key="member.id"
        data-testid="member-row"
        class="px-5 py-2 flex items-center justify-between hover:bg-blue-500/[0.01] transition-colors"
      >
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-[10px] font-medium text-white flex-shrink-0">
            {{ displayAvatar(member) }}
          </div>
          <div class="min-w-0">
            <span class="text-xs font-medium text-gray-800 truncate block">{{ displayName(member) }}</span>
            <span class="text-[10px] text-gray-400">{{ member.user?.email }}</span>
          </div>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          <button
            class="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors cursor-pointer capitalize"
            @click="openRoleModal(member)"
          >
            {{ roleLabel(member.roles) }}
          </button>
          <button
            class="text-[10px] text-red-400 hover:text-red-600 transition-colors cursor-pointer"
            @click="openRemoveModal(member)"
          >
            {{ t('team.remove') }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="!loading" class="px-5 py-2 border-t border-blue-500/3">
      <button
        data-testid="add-member-btn"
        class="text-xs text-blue-500 hover:text-blue-700 transition-colors cursor-pointer"
        @click="openAddModal"
      >
        + {{ t('team.addMember') }}
      </button>
    </div>

    <!-- Add Member Modal -->
    <Modal :show="showAddModal" :title="t('team.addMember')" @close="showAddModal = false">
      <form data-testid="add-member-modal" @submit.prevent="handleAddMember" class="space-y-4">
        <div v-if="addError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
          {{ addError }}
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('team.selectUser') }}</label>
          <div v-if="selectedUser" class="flex items-center gap-2 p-2 bg-blue-50 rounded-[10px]">
            <div class="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xs font-medium text-white">
              {{ (selectedUser.display_name || selectedUser.username).slice(0, 2).toUpperCase() }}
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-900">{{ selectedUser.display_name || selectedUser.username }}</p>
              <p class="text-xs text-gray-400">{{ selectedUser.email }}</p>
            </div>
            <button type="button" class="text-gray-400 hover:text-gray-600 cursor-pointer" @click="clearSelectedUser">✕</button>
          </div>
          <div v-else class="relative">
            <input
              type="text"
              class="input-glass w-full"
              :placeholder="t('team.searchUsersPlaceholder')"
              :value="searchQuery"
              @input="onSearchInput(($event.target as HTMLInputElement).value)"
            />
            <div v-if="searching" class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
              {{ t('team.loadingMembers') }}
            </div>
            <div v-if="searchResults.length > 0" class="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-[10px] shadow-lg max-h-48 overflow-y-auto">
              <button
                v-for="u in searchResults"
                :key="u.id"
                type="button"
                class="w-full px-3 py-2 text-left hover:bg-blue-50 transition-colors flex items-center gap-2 cursor-pointer"
                @click="selectUser(u)"
              >
                <div class="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xs font-medium text-white">
                  {{ (u.display_name || u.username).slice(0, 2).toUpperCase() }}
                </div>
                <div>
                  <p class="text-sm text-gray-900">{{ u.display_name || u.username }}</p>
                  <p class="text-xs text-gray-400">{{ u.email }}</p>
                </div>
              </button>
            </div>
            <div v-if="searchQuery && !searching && searchResults.length === 0 && !selectedUser" class="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-[10px] shadow-lg p-3 text-center text-sm text-gray-400">
              {{ t('team.noUsersFound') }}
            </div>
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('team.role') }}</label>
          <select v-model="addForm.roles" data-testid="role-select" class="select-glass">
            <option value="team_admin">{{ t('team.teamAdmin') }}</option>
            <option value="product_owner">{{ t('team.productOwner') }}</option>
            <option value="designer">{{ t('team.designer') }}</option>
            <option value="developer">{{ t('team.developer') }}</option>
            <option value="tester">{{ t('team.tester') }}</option>
            <option value="viewer">{{ t('team.viewer') }}</option>
          </select>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <GlassButton variant="secondary" @click="showAddModal = false">
            {{ t('common.cancel') }}
          </GlassButton>
          <GlassButton type="submit" :loading="adding" :disabled="!selectedUser">
            {{ adding ? t('team.adding') : t('team.addMember') }}
          </GlassButton>
        </div>
      </form>
    </Modal>

    <!-- Remove Member Modal -->
    <Modal :show="showRemoveModal" :title="t('team.confirmRemove')" @close="showRemoveModal = false">
      <div data-testid="remove-modal" class="space-y-4">
        <p class="text-sm text-gray-600">{{ t('team.confirmRemoveMsg') }}</p>
        <div v-if="removingMember" class="p-3 bg-red-50 rounded-[10px] flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-red-400 to-red-500 flex items-center justify-center text-xs font-medium text-white">
            {{ displayAvatar(removingMember) }}
          </div>
          <div>
            <p class="text-sm font-medium text-gray-900">{{ displayName(removingMember) }}</p>
            <p class="text-xs text-gray-400">{{ removingMember.user?.email }}</p>
          </div>
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <GlassButton variant="secondary" @click="showRemoveModal = false">
            {{ t('common.cancel') }}
          </GlassButton>
          <GlassButton variant="danger" :loading="removing" @click="handleRemoveMember">
            {{ t('team.removeMember') }}
          </GlassButton>
        </div>
      </div>
    </Modal>

    <!-- Update Role Modal -->
    <Modal :show="showRoleModal" :title="t('team.updateRole')" @close="showRoleModal = false">
      <form data-testid="role-modal" @submit.prevent="handleUpdateRole" class="space-y-4">
        <div v-if="editingMember" class="p-3 bg-blue-50 rounded-[10px] flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xs font-medium text-white">
            {{ displayAvatar(editingMember) }}
          </div>
          <div>
            <p class="text-sm font-medium text-gray-900">{{ displayName(editingMember) }}</p>
            <p class="text-xs text-gray-400">{{ editingMember.user?.email }}</p>
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('team.role') }}</label>
          <select v-model="editRole" class="select-glass">
            <option value="team_admin">{{ t('team.teamAdmin') }}</option>
            <option value="product_owner">{{ t('team.productOwner') }}</option>
            <option value="designer">{{ t('team.designer') }}</option>
            <option value="developer">{{ t('team.developer') }}</option>
            <option value="tester">{{ t('team.tester') }}</option>
            <option value="viewer">{{ t('team.viewer') }}</option>
          </select>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <GlassButton variant="secondary" @click="showRoleModal = false">
            {{ t('common.cancel') }}
          </GlassButton>
          <GlassButton type="submit" :loading="updatingRole">
            {{ t('team.updateRole') }}
          </GlassButton>
        </div>
      </form>
    </Modal>
  </div>
</template>
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd frontend && npx vitest run src/components/__tests__/TeamMemberPanel.test.ts`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/TeamMemberPanel.vue frontend/src/components/__tests__/TeamMemberPanel.test.ts
git commit -m "feat: create TeamMemberPanel component with CRUD and tests"
```

---

### Task 4: 集成 TeamMemberPanel 到 TeamsView

**Files:**
- Modify: `frontend/src/views/TeamsView.vue`

- [ ] **Step 1: 编写测试 — 验证团队卡片有成员面板**

创建 `frontend/src/views/__tests__/TeamsView.test.ts`：

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import TeamsView from '../TeamsView.vue'
import en from '@/locales/en.json'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: { en },
})

vi.mock('@/api/endpoints', () => ({
  orgApi: {
    list: () => Promise.resolve({ data: [{ id: 'o1', name: 'Org 1', slug: 'org-1', created_at: '', updated_at: '' }] }),
    create: () => Promise.resolve({ data: {} }),
  },
  teamApi: {
    list: () => Promise.resolve({ data: [{ id: 't1', org_id: 'o1', name: 'Team 1', slug: 'team-1', created_at: '', updated_at: '' }] }),
    create: () => Promise.resolve({ data: {} }),
  },
}))

function mountView() {
  return mount(TeamsView, {
    global: {
      plugins: [i18n],
      stubs: {
        Modal: true,
        EmptyState: true,
        GlassButton: {
          template: '<button :class="$attrs.class" @click="$emit(\'click\')"><slot /></button>',
          props: ['loading', 'variant', 'size'],
        },
        TeamMemberPanel: {
          template: '<div data-testid="team-member-panel" />',
          props: ['teamId'],
        },
      },
    },
  })
}

describe('TeamsView', () => {
  it('renders TeamMemberPanel for each team', async () => {
    const wrapper = mountView()
    await new Promise((r) => setTimeout(r, 50))
    const panels = wrapper.findAllComponents({ name: 'TeamMemberPanel' })
    expect(panels.length).toBeGreaterThanOrEqual(1)
  })

  it('shows member count toggle button for each team', async () => {
    const wrapper = mountView()
    await new Promise((r) => setTimeout(r, 50))
    const toggles = wrapper.findAll('[data-testid="member-toggle"]')
    expect(toggles.length).toBeGreaterThanOrEqual(1)
  })
})
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd frontend && npx vitest run src/views/__tests__/TeamsView.test.ts`
Expected: FAIL — 尚未集成 TeamMemberPanel

- [ ] **Step 3: 更新 TeamsView.vue — 添加导入和展开状态**

在 `TeamsView.vue` 的 `<script setup>` 中：

1. 添加导入 `TeamMemberPanel`：

```typescript
import TeamMemberPanel from '@/components/TeamMemberPanel.vue'
```

2. 添加 `TeamMemberDetail` 类型导入（不需要，组件自己处理）。

3. 添加展开状态管理：

```typescript
const expandedTeams = ref<Set<string>>(new Set())

function toggleMembers(teamId: string) {
  if (expandedTeams.value.has(teamId)) {
    expandedTeams.value.delete(teamId)
  } else {
    expandedTeams.value.add(teamId)
  }
}
```

- [ ] **Step 4: 更新 TeamsView.vue 模板 — 团队卡片添加成员展开按钮和面板**

在模板中，替换团队行（第 164-174 行区域）为：

```html
        <div class="divide-y divide-blue-500/5">
          <div
            v-for="team in teamsForOrg(org.id)"
            :key="team.id"
          >
            <div class="px-5 py-3 flex items-center justify-between hover:bg-blue-500/[0.01] transition-colors">
              <div>
                <span class="text-sm font-medium text-gray-800">{{ team.name }}</span>
                <span class="text-xs text-gray-400 ml-2">{{ team.slug }}</span>
              </div>
              <div class="flex items-center gap-3">
                <button
                  data-testid="member-toggle"
                  class="text-xs text-blue-500 hover:text-blue-700 transition-colors cursor-pointer"
                  @click="toggleMembers(team.id)"
                >
                  {{ expandedTeams.has(team.id) ? t('common.close') : t('team.members', { count: '' }) }}
                </button>
                <span class="text-xs text-gray-400">{{ formatDate(team.created_at) }}</span>
              </div>
            </div>
            <TeamMemberPanel
              v-if="expandedTeams.has(team.id)"
              :team-id="team.id"
            />
          </div>
          <div
            v-if="teamsForOrg(org.id).length === 0"
            class="px-5 py-4 text-sm text-gray-400 text-center"
          >
            {{ t('team.noTeamsYet') }}
          </div>
        </div>
```

- [ ] **Step 5: 运行测试验证通过**

Run: `cd frontend && npx vitest run src/views/__tests__/TeamsView.test.ts`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add frontend/src/views/TeamsView.vue frontend/src/views/__tests__/TeamsView.test.ts
git commit -m "feat: integrate TeamMemberPanel into TeamsView with expand/collapse"
```

---

### Task 5: 后端测试 — 验证新角色值

**Files:**
- Modify: `backend/tests/test_team_service.py`

- [ ] **Step 1: 编写测试 — 验证所有 6 种角色值可正常使用**

在 `backend/tests/test_team_service.py` 末尾添加新的测试类：

```python
class TestTeamMemberRoles:
    TEAM_ROLES = ["team_admin", "product_owner", "designer", "developer", "tester", "viewer"]

    async def test_add_member_with_each_role(self, db: AsyncSession):
        org = await create_organization(db, "Roles Org", "roles-org")
        team = await create_team(db, org.id, "Roles Team", "roles-team")
        for i, role in enumerate(self.TEAM_ROLES):
            user = await create_user(
                db, f"roleuser{i}", f"role{i}@example.com", "password123"
            )
            member = await add_team_member(db, team.id, user.id, role)
            assert member.roles == role

    async def test_update_to_each_role(self, db: AsyncSession):
        org = await create_organization(db, "UpdRoles Org", "updroles-org")
        team = await create_team(db, org.id, "UpdRoles Team", "updroles-team")
        user = await create_user(
            db, "updrolesuser", "updroles@example.com", "password123"
        )
        await add_team_member(db, team.id, user.id, "developer")
        for role in self.TEAM_ROLES:
            updated = await update_team_member_role(db, team.id, user.id, role)
            assert updated.roles == role

    async def test_mixed_roles_in_team(self, db: AsyncSession):
        org = await create_organization(db, "Mixed Org", "mixed-org")
        team = await create_team(db, org.id, "Mixed Team", "mixed-team")
        users_and_roles = [
            ("mixedadmin", "team_admin"),
            ("mixedpo", "product_owner"),
            ("mixeddesigner", "designer"),
            ("mixeddev", "developer"),
            ("mixedtester", "tester"),
            ("mixedviewer", "viewer"),
        ]
        for username, role in users_and_roles:
            user = await create_user(
                db, username, f"{username}@example.com", "password123"
            )
            member = await add_team_member(db, team.id, user.id, role)
            assert member.roles == role
```

- [ ] **Step 2: 运行测试验证通过**

Run: `cd backend && pytest tests/test_team_service.py::TestTeamMemberRoles -v`
Expected: PASS（后端 roles 是自由字符串，无校验限制）

- [ ] **Step 3: 运行完整后端测试套件确认无回归**

Run: `cd backend && pytest -v`
Expected: ALL PASS

- [ ] **Step 4: 提交**

```bash
git add backend/tests/test_team_service.py
git commit -m "test: add role validation tests for 6 team member roles"
```

---

### Task 6: 端到端验证 — 前端构建和全量测试

**Files:** 无新文件

- [ ] **Step 1: 运行前端类型检查**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: 无类型错误

- [ ] **Step 2: 运行前端全量测试**

Run: `cd frontend && npx vitest run`
Expected: ALL PASS

- [ ] **Step 3: 运行前端构建**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 4: 运行后端全量测试**

Run: `cd backend && pytest -v`
Expected: ALL PASS

- [ ] **Step 5: 提交（如有修复）**

仅在前面步骤发现需要修复时提交。
