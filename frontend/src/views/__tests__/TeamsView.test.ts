// @vitest-environment jsdom
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
    const toggles = wrapper.findAll('[data-testid="member-toggle"]')
    for (const toggle of toggles) {
      await toggle.trigger('click')
    }
    await wrapper.vm.$nextTick()
    const panels = wrapper.findAll('[data-testid="team-member-panel"]')
    expect(panels.length).toBeGreaterThanOrEqual(1)
  })

  it('shows member count toggle button for each team', async () => {
    const wrapper = mountView()
    await new Promise((r) => setTimeout(r, 50))
    const toggles = wrapper.findAll('[data-testid="member-toggle"]')
    expect(toggles.length).toBeGreaterThanOrEqual(1)
  })
})
