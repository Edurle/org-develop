# Team Member Management Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix team member management — enable adding members via user search, show usernames, support removing members and updating roles.

**Architecture:** Backend adds 3 new endpoints (list users, remove member, update member role) + 2 service methods. Frontend rewrites ProjectMembersView to use user search dropdown, member detail display, and delete/role-change actions.

**Tech Stack:** FastAPI + SQLAlchemy async (backend), Vue 3 + TypeScript + UnoCSS (frontend)

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `backend/app/services/team.py` | Add `remove_team_member()`, `update_team_member_role()` |
| Modify | `backend/app/routers/users.py` | Add `GET /users` with optional `?search=` param |
| Modify | `backend/app/routers/teams.py` | Add `DELETE /teams/{team_id}/members/{member_id}`, `PATCH /teams/{team_id}/members/{member_id}` |
| Modify | `backend/tests/test_team_service.py` | Add tests for remove & update member |
| Modify | `backend/tests/test_user_service.py` | Add test for list users with search |
| Modify | `frontend/src/api/endpoints.ts` | Add `userApi`, `teamApi.removeMember`, `teamApi.updateMember` |
| Modify | `frontend/src/types/index.ts` | No change needed (types already exist) |
| Rewrite | `frontend/src/views/ProjectMembersView.vue` | User search dropdown, detail display, remove/role actions |
| Modify | `frontend/src/locales/zh-CN.json` | Add new translation keys |
| Modify | `frontend/src/locales/en.json` | Add new translation keys |

---

### Task 1: Add `GET /users` endpoint (list users with search)

**Files:**
- Modify: `backend/app/routers/users.py`

- [ ] **Step 1: Add list users endpoint to router**

Add the following endpoint to `backend/app/routers/users.py` after the existing `get_user` endpoint (after line 51):

```python
@router.get("/users", response_model=list[UserResponse])
async def list_users(
    search: str | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
    _user: Annotated[User, Depends(get_current_user)] = Depends(get_current_user),
):
    query = select(User).order_by(User.created_at)
    if search:
        term = f"%{search}%"
        query = query.where(
            (User.username.ilike(term)) | (User.display_name.ilike(term)) | (User.email.ilike(term))
        )
    query = query.limit(50)
    result = await db.execute(query)
    return [UserResponse.model_validate(u).model_dump() for u in result.scalars().all()]
```

**Note:** This endpoint must be placed BEFORE the `GET /users/{user_id}` route to avoid path conflicts in FastAPI.

- [ ] **Step 2: Run existing tests to verify no regression**

Run: `cd backend && pytest tests/test_user_service.py -v`
Expected: All existing tests PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/users.py
git commit -m "feat: add GET /users endpoint with search support"
```

---

### Task 2: Add `remove_team_member` and `update_team_member_role` service methods

**Files:**
- Modify: `backend/app/services/team.py`

- [ ] **Step 1: Add two new service functions**

Add the following functions to the end of `backend/app/services/team.py`:

```python
async def remove_team_member(
    db: AsyncSession, team_id: str, user_id: str
) -> None:
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
    )
    member = result.scalars().first()
    if member is None:
        raise ValueError(f"User '{user_id}' is not a member of team '{team_id}'")
    await db.delete(member)
    await db.flush()


async def update_team_member_role(
    db: AsyncSession, team_id: str, user_id: str, roles: str
) -> TeamMember:
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
    )
    member = result.scalars().first()
    if member is None:
        raise ValueError(f"User '{user_id}' is not a member of team '{team_id}'")
    member.roles = roles
    await db.flush()
    return member
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/team.py
git commit -m "feat: add remove_team_member and update_team_member_role services"
```

---

### Task 3: Add DELETE and PATCH member endpoints to router

**Files:**
- Modify: `backend/app/routers/teams.py`

- [ ] **Step 1: Update imports and add endpoints**

In `backend/app/routers/teams.py`, add `TeamMemberUpdate` to the import from `app.schemas.user` (line 19-23). Change:

```python
from app.schemas.user import (
    TeamMemberCreate,
    TeamMemberDetailResponse,
    TeamMemberResponse,
)
```

to:

```python
from app.schemas.user import (
    TeamMemberCreate,
    TeamMemberDetailResponse,
    TeamMemberResponse,
    TeamMemberUpdate,
)
```

Then add these two endpoints after the `list_team_members_detail` endpoint (after line 162):

```python
@router.delete(
    "/teams/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_team_member(
    team_id: str,
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        await team_svc.remove_team_member(db, team_id=team_id, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="team.member.remove",
        resource_type="team_member", resource_id=user_id,
        detail=f"Removed user '{user_id}' from team '{team_id}'",
    )


@router.patch(
    "/teams/{team_id}/members/{user_id}",
    response_model=TeamMemberResponse,
)
async def update_team_member(
    team_id: str,
    user_id: str,
    body: TeamMemberUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        member = await team_svc.update_team_member_role(
            db, team_id=team_id, user_id=user_id, roles=body.roles
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    await log_action(
        db, user_id=user.id, action="team.member.update",
        resource_type="team_member", resource_id=member.id,
        detail=f"Updated member '{user_id}' roles to '{body.roles}' in team '{team_id}'",
    )
    return TeamMemberResponse.model_validate(member).model_dump()
```

- [ ] **Step 2: Run existing tests to verify no regression**

Run: `cd backend && pytest tests/test_team_service.py -v`
Expected: All existing tests PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/teams.py
git commit -m "feat: add DELETE and PATCH endpoints for team members"
```

---

### Task 4: Add backend tests for new functionality

**Files:**
- Modify: `backend/tests/test_team_service.py`

- [ ] **Step 1: Add tests for remove and update member**

Add the following test methods to `TestTeamMember` class in `backend/tests/test_team_service.py`, and add `remove_team_member, update_team_member_role` to the imports:

Update import (line 16-19):

```python
from app.services.team import (
    create_organization,
    create_team,
    add_team_member,
    remove_team_member,
    update_team_member_role,
)
```

Append to `TestTeamMember` class (after line 124):

```python
    async def test_remove_member(self, db: AsyncSession):
        org = await create_organization(db, "Remove Org", "remove-org")
        team = await create_team(db, org.id, "Remove Team", "remove-team")
        user = await create_user(
            db, "removeuser", "remove@example.com", "password123"
        )
        await add_team_member(db, team.id, user.id, "developer")
        await remove_team_member(db, team.id, user.id)
        result = await db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team.id,
                TeamMember.user_id == user.id,
            )
        )
        assert result.scalars().first() is None

    async def test_remove_member_not_found(self, db: AsyncSession):
        with pytest.raises(ValueError, match="not a member"):
            await remove_team_member(db, "any-team", "any-user")

    async def test_update_member_role(self, db: AsyncSession):
        org = await create_organization(db, "Update Org", "update-org")
        team = await create_team(db, org.id, "Update Team", "update-team")
        user = await create_user(
            db, "updateuser", "update@example.com", "password123"
        )
        await add_team_member(db, team.id, user.id, "developer")
        updated = await update_team_member_role(db, team.id, user.id, "admin")
        assert updated.roles == "admin"

    async def test_update_member_role_not_found(self, db: AsyncSession):
        with pytest.raises(ValueError, match="not a member"):
            await update_team_member_role(db, "any-team", "any-user", "admin")
```

- [ ] **Step 2: Run all team service tests**

Run: `cd backend && pytest tests/test_team_service.py -v`
Expected: All tests PASS (including new ones)

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_team_service.py
git commit -m "test: add tests for remove and update team member"
```

---

### Task 5: Update frontend API layer

**Files:**
- Modify: `frontend/src/api/endpoints.ts`

- [ ] **Step 1: Add userApi and extend teamApi**

In `frontend/src/api/endpoints.ts`:

Add `userApi` after the `authApi` block (after line 34), before the `// ── Organizations ──` comment:

```typescript
// ── Users ──

export const userApi = {
  list: (search?: string) =>
    api.get<User[]>('/users', { params: { search } }),
}
```

Extend `teamApi` by adding `removeMember` and `updateMember` methods. Change the `teamApi` object (lines 46-54):

```typescript
export const teamApi = {
  list: () => api.get<Team[]>('/teams'),
  create: (data: { org_id: string; name: string; slug: string }) =>
    api.post<Team>('/teams', data),
  members: (teamId: string) => api.get<TeamMember[]>(`/teams/${teamId}/members`),
  membersDetail: (teamId: string) => api.get<TeamMemberDetail[]>(`/teams/${teamId}/members/detail`),
  addMember: (teamId: string, data: { user_id: string; roles: string }) =>
    api.post<TeamMember>(`/teams/${teamId}/members`, data),
  removeMember: (teamId: string, userId: string) =>
    api.delete(`/teams/${teamId}/members/${userId}`),
  updateMember: (teamId: string, userId: string, data: { roles: string }) =>
    api.patch<TeamMember>(`/teams/${teamId}/members/${userId}`, data),
}
```

- [ ] **Step 2: Run type check**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: No type errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/endpoints.ts
git commit -m "feat: add userApi and extend teamApi with remove/update member"
```

---

### Task 6: Update locales

**Files:**
- Modify: `frontend/src/locales/zh-CN.json`
- Modify: `frontend/src/locales/en.json`

- [ ] **Step 1: Add new translation keys**

In `frontend/src/locales/zh-CN.json`, add the following keys inside the `"project"` section (after `"describeProject"` line 153):

```json
    "searchUsers": "搜索用户",
    "searchUsersPlaceholder": "输入用户名搜索...",
    "noUsersFound": "未找到用户",
    "removeMember": "移除成员",
    "confirmRemove": "确认移除",
    "confirmRemoveMsg": "确认从团队中移除该成员？",
    "updateRole": "更新角色",
    "failedRemoveMember": "移除成员失败。",
    "failedUpdateRole": "更新角色失败。",
    "memberRemoved": "成员已移除。",
    "roleUpdated": "角色已更新。",
    "developer": "开发者",
    "username": "用户名",
    "displayName": "显示名",
    "selectUser": "选择用户",
    "loadingUsers": "加载用户中...",
    "alreadyMember": "该用户已是团队成员。",
    "remove": "移除"
```

In `frontend/src/locales/en.json`, add the same keys (after `"describeProject"` line 153):

```json
    "searchUsers": "Search Users",
    "searchUsersPlaceholder": "Type username to search...",
    "noUsersFound": "No users found",
    "removeMember": "Remove Member",
    "confirmRemove": "Confirm Remove",
    "confirmRemoveMsg": "Are you sure you want to remove this member from the team?",
    "updateRole": "Update Role",
    "failedRemoveMember": "Failed to remove member.",
    "failedUpdateRole": "Failed to update role.",
    "memberRemoved": "Member removed.",
    "roleUpdated": "Role updated.",
    "developer": "Developer",
    "username": "Username",
    "displayName": "Display Name",
    "selectUser": "Select User",
    "loadingUsers": "Loading users...",
    "alreadyMember": "This user is already a team member.",
    "remove": "Remove"
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/locales/zh-CN.json frontend/src/locales/en.json
git commit -m "feat: add team member management translation keys"
```

---

### Task 7: Rewrite ProjectMembersView

**Files:**
- Rewrite: `frontend/src/views/ProjectMembersView.vue`

- [ ] **Step 1: Rewrite the component**

Replace the entire content of `frontend/src/views/ProjectMembersView.vue` with:

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useProjectStore } from '@/stores/project'
import { teamApi, userApi } from '@/api/endpoints'
import Modal from '@/components/Modal.vue'
import GlassButton from '@/components/GlassButton.vue'
import type { TeamMemberDetail, User } from '@/types'

const { t } = useI18n()
const route = useRoute()
const projectId = route.params.id as string

const projectStore = useProjectStore()

const loading = ref(true)
const error = ref('')
const members = ref<TeamMemberDetail[]>([])

const showAddModal = ref(false)
const searchQuery = ref('')
const searchResults = ref<User[]>([])
const searching = ref(false)
const selectedUser = ref<User | null>(null)
const addForm = ref({ roles: 'member' })
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

async function loadMembers() {
  loading.value = true
  error.value = ''
  try {
    if (!projectStore.currentProject) {
      await projectStore.fetchOne(projectId)
    }
    const teamId = projectStore.currentProject?.team_id
    if (teamId) {
      const res = await teamApi.membersDetail(teamId)
      members.value = res.data
    }
  } catch (err: any) {
    error.value = err?.response?.data?.detail || t('project.failedLoadMembers')
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
  addForm.value = { roles: 'member' }
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
      addError.value = t('project.selectUser')
      return
    }
    const teamId = projectStore.currentProject?.team_id
    if (!teamId) {
      addError.value = t('project.projectTeamNotFound')
      return
    }
    await teamApi.addMember(teamId, {
      user_id: selectedUser.value.id,
      roles: addForm.value.roles,
    })
    await loadMembers()
    showAddModal.value = false
  } catch (err: any) {
    addError.value = err?.response?.data?.detail || err?.message || t('project.failedAddMember')
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
    const teamId = projectStore.currentProject?.team_id
    if (!teamId) return
    await teamApi.removeMember(teamId, removingMember.value.user_id)
    await loadMembers()
    showRemoveModal.value = false
    removingMember.value = null
  } catch (err: any) {
    error.value = err?.response?.data?.detail || t('project.failedRemoveMember')
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
    const teamId = projectStore.currentProject?.team_id
    if (!teamId) return
    await teamApi.updateMember(teamId, editingMember.value.user_id, {
      roles: editRole.value,
    })
    await loadMembers()
    showRoleModal.value = false
    editingMember.value = null
  } catch (err: any) {
    error.value = err?.response?.data?.detail || t('project.failedUpdateRole')
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

onMounted(loadMembers)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">{{ t('project.members') }}</h1>
        <p class="mt-1 text-sm text-gray-500">{{ t('project.manageMembers') }}</p>
      </div>
      <GlassButton size="large" @click="openAddModal">
        {{ t('project.addMember') }}
      </GlassButton>
    </div>

    <div v-if="error" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
      {{ error }}
    </div>

    <div v-if="loading" class="glass-card overflow-hidden">
      <div class="divide-y divide-blue-500/5">
        <div v-for="i in 4" :key="i" class="px-5 py-4 animate-pulse flex items-center gap-4">
          <div class="h-8 w-8 bg-gray-200/50 rounded-full" />
          <div class="flex-1 space-y-2">
            <div class="h-4 bg-gray-200/50 rounded w-1/4" />
            <div class="h-3 bg-gray-100/50 rounded w-1/3" />
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="members.length === 0" class="glass-card px-5 py-12 text-center">
      <p class="text-sm text-gray-500">{{ t('project.noMembers') }}</p>
    </div>

    <div v-else class="glass-card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-blue-500/5 bg-blue-500/[0.02]">
            <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('project.userId') }}</th>
            <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('project.role') }}</th>
            <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('project.joined') }}</th>
            <th class="px-5 py-3 text-right text-xs font-semibold text-gray-500"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-blue-500/5">
          <tr v-for="member in members" :key="member.id" class="hover:bg-blue-500/[0.01] transition-colors">
            <td class="px-5 py-3">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xs font-medium text-white">
                  {{ displayAvatar(member) }}
                </div>
                <div>
                  <span class="text-gray-900 font-medium">{{ displayName(member) }}</span>
                  <p v-if="member.user?.email" class="text-xs text-gray-400">{{ member.user.email }}</p>
                </div>
              </div>
            </td>
            <td class="px-5 py-3">
              <button
                class="capitalize text-gray-600 hover:text-blue-600 transition-colors cursor-pointer"
                @click="openRoleModal(member)"
              >
                {{ member.roles }}
              </button>
            </td>
            <td class="px-5 py-3 text-gray-400">{{ formatDate(member.joined_at) }}</td>
            <td class="px-5 py-3 text-right">
              <button
                class="text-xs text-red-400 hover:text-red-600 transition-colors cursor-pointer"
                @click="openRemoveModal(member)"
              >
                {{ t('project.remove') }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Member Modal -->
    <Modal :show="showAddModal" :title="t('project.addMember')" @close="showAddModal = false">
      <form @submit.prevent="handleAddMember" class="space-y-4">
        <div v-if="addError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
          {{ addError }}
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('project.selectUser') }}</label>
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
              :placeholder="t('project.searchUsersPlaceholder')"
              :value="searchQuery"
              @input="onSearchInput(($event.target as HTMLInputElement).value)"
            />
            <div v-if="searching" class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
              {{ t('project.loadingUsers') }}
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
              {{ t('project.noUsersFound') }}
            </div>
          </div>
        </div>

        <div>
          <label for="add-member-role" class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('project.role') }}</label>
          <select id="add-member-role" v-model="addForm.roles" class="select-glass">
            <option value="admin">{{ t('project.admin') }}</option>
            <option value="member">{{ t('project.memberRole') }}</option>
            <option value="viewer">{{ t('project.viewer') }}</option>
            <option value="developer">{{ t('project.developer') }}</option>
          </select>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <GlassButton variant="secondary" @click="showAddModal = false">
            {{ t('common.cancel') }}
          </GlassButton>
          <GlassButton type="submit" :loading="adding" :disabled="!selectedUser">
            {{ adding ? t('project.adding') : t('project.addMember') }}
          </GlassButton>
        </div>
      </form>
    </Modal>

    <!-- Remove Member Modal -->
    <Modal :show="showRemoveModal" :title="t('project.confirmRemove')" @close="showRemoveModal = false">
      <div class="space-y-4">
        <p class="text-sm text-gray-600">
          {{ t('project.confirmRemoveMsg') }}
        </p>
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
            {{ t('project.removeMember') }}
          </GlassButton>
        </div>
      </div>
    </Modal>

    <!-- Update Role Modal -->
    <Modal :show="showRoleModal" :title="t('project.updateRole')" @close="showRoleModal = false">
      <form @submit.prevent="handleUpdateRole" class="space-y-4">
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
          <label for="edit-role" class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('project.role') }}</label>
          <select id="edit-role" v-model="editRole" class="select-glass">
            <option value="admin">{{ t('project.admin') }}</option>
            <option value="member">{{ t('project.memberRole') }}</option>
            <option value="viewer">{{ t('project.viewer') }}</option>
            <option value="developer">{{ t('project.developer') }}</option>
          </select>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <GlassButton variant="secondary" @click="showRoleModal = false">
            {{ t('common.cancel') }}
          </GlassButton>
          <GlassButton type="submit" :loading="updatingRole">
            {{ t('project.updateRole') }}
          </GlassButton>
        </div>
      </form>
    </Modal>
  </div>
</template>
```

**Note:** This uses `GlassButton variant="danger"` for the remove button. If `GlassButton` doesn't support `danger` variant, we need to add it. Let's check.

- [ ] **Step 2: Check if GlassButton supports `danger` variant. If not, add it.**

Read `frontend/src/components/GlassButton.vue`. If it doesn't have a `danger` variant, add support for it (a red-colored button style). The implementation depends on the existing code.

- [ ] **Step 3: Run type check**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: No type errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/ProjectMembersView.vue
git commit -m "feat: rewrite ProjectMembersView with user search, remove, role update"
```

---

### Task 8: Run full verification

- [ ] **Step 1: Run all backend tests**

Run: `cd backend && pytest -v`
Expected: All tests PASS

- [ ] **Step 2: Run frontend type check**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: No type errors

- [ ] **Step 3: Run frontend build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Final commit if any lint fixes needed**

```bash
git add -A
git commit -m "fix: lint and type fixes for team member management"
```
