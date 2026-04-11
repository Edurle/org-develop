// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import ProjectMembersView from '../ProjectMembersView.vue'
import en from '@/locales/en.json'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: 'test-project-id' } }),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}))

vi.mock('@/api/endpoints', () => ({
  teamApi: {
    membersDetail: vi.fn().mockResolvedValue({ data: [] }),
    addMember: vi.fn(),
    removeMember: vi.fn(),
    updateMember: vi.fn(),
  },
  userApi: {
    list: vi.fn().mockResolvedValue({ data: [] }),
  },
}))

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: { en },
})

const roleValues = ['team_admin', 'product_owner', 'designer', 'developer', 'tester', 'viewer']

function mountComponent() {
  setActivePinia(createPinia())
  return mount(ProjectMembersView, {
    global: {
      plugins: [i18n],
      stubs: {
        Modal: {
          props: ['show', 'title'],
          template: '<div><slot /></div>',
        },
        GlassButton: {
          props: ['variant', 'loading', 'disabled'],
          template: '<button :disabled="disabled"><slot /></button>',
        },
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
