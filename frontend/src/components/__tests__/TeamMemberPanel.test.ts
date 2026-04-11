import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import TeamMemberPanel from '../TeamMemberPanel.vue'
import en from '@/locales/en.json'

vi.mock('@/api/endpoints', () => ({
  teamApi: {
    membersDetail: vi.fn(),
    addMember: vi.fn(),
    removeMember: vi.fn(),
    updateMember: vi.fn(),
  },
  userApi: {
    list: vi.fn(),
  },
}))

import { teamApi } from '@/api/endpoints'

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
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state when members not loaded', () => {
    (teamApi.membersDetail as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}))
    const wrapper = mountPanel()
    expect(wrapper.find('[data-testid="member-loading"]').exists()).toBe(true)
  })

  it('shows member list after loading', async () => {
    ;(teamApi.membersDetail as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockMembers })
    const wrapper = mountPanel()
    await vi.dynamicImportSettled()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('[data-testid="member-row"]')).toHaveLength(2)
  })

  it('shows no members message when empty', async () => {
    ;(teamApi.membersDetail as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] })
    const wrapper = mountPanel()
    await vi.dynamicImportSettled()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="no-members"]').exists()).toBe(true)
  })

  it('displays member display name and role', async () => {
    ;(teamApi.membersDetail as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockMembers })
    const wrapper = mountPanel()
    await vi.dynamicImportSettled()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    const rows = wrapper.findAll('[data-testid="member-row"]')
    expect(rows[0]!.text()).toContain('Alice')
    expect(rows[0]!.text()).toContain('Team Admin')
  })

  it('falls back to username when display_name is null', async () => {
    ;(teamApi.membersDetail as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockMembers })
    const wrapper = mountPanel()
    await vi.dynamicImportSettled()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    const rows = wrapper.findAll('[data-testid="member-row"]')
    expect(rows[1]!.text()).toContain('bob')
  })

  it('shows add member button', async () => {
    ;(teamApi.membersDetail as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockMembers })
    const wrapper = mountPanel()
    await vi.dynamicImportSettled()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="add-member-btn"]').exists()).toBe(true)
  })

  it('opens add member modal on button click', async () => {
    ;(teamApi.membersDetail as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockMembers })
    const wrapper = mountPanel()
    await vi.dynamicImportSettled()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    await wrapper.find('[data-testid="add-member-btn"]').trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="add-member-modal"]').exists()).toBe(true)
  })

  it('shows 6 role options in add modal', async () => {
    ;(teamApi.membersDetail as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockMembers })
    const wrapper = mountPanel()
    await vi.dynamicImportSettled()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    const toggleBtn = wrapper.find('[data-testid="add-member-btn"]')
    await toggleBtn.trigger('click')
    await wrapper.vm.$nextTick()
    const options = wrapper.findAll('[data-testid="role-select"] option')
    const values = options.map((o) => o.attributes('value'))
    expect(values).toContain('team_admin')
    expect(values).toContain('product_owner')
    expect(values).toContain('designer')
    expect(values).toContain('developer')
    expect(values).toContain('tester')
    expect(values).toContain('viewer')
  })

  it('shows remove confirmation modal', async () => {
    ;(teamApi.membersDetail as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockMembers })
    const wrapper = mountPanel()
    await vi.dynamicImportSettled()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    const removeBtns = wrapper.findAll('[data-testid="member-row"] button')
    const removeBtn = removeBtns.find((b) => b.text().includes('Remove'))
    if (removeBtn) {
      await removeBtn.trigger('click')
    }
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="remove-modal"]').exists()).toBe(true)
  })

  it('shows update role modal', async () => {
    ;(teamApi.membersDetail as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockMembers })
    const wrapper = mountPanel()
    await vi.dynamicImportSettled()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    const rows = wrapper.findAll('[data-testid="member-row"]')
    const roleBtn = rows[0]!.find('button')
    await roleBtn.trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[data-testid="role-modal"]').exists()).toBe(true)
  })
})
