import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '../src/App.vue'
import StatusBadge from '../src/components/StatusBadge.vue'

// Mock global fetch for health check
global.fetch = vi.fn().mockImplementation(() =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        status: 'ok',
        environment: 'test',
        project_name: 'Casa Afeto',
      }),
  })
)

describe('M0 Frontend Foundation', () => {
  it('renders application title and M0 badge', () => {
    const wrapper = mount(App)
    expect(wrapper.text()).toContain('Casa Afeto')
    expect(wrapper.text()).toContain('Milestone M0')
    expect(wrapper.text()).toContain('Technical Foundation Active')
  })

  it('renders StatusBadge component correctly', () => {
    const wrapper = mount(StatusBadge, {
      props: {
        status: 'online',
        label: 'Ready',
      },
    })
    expect(wrapper.classes()).toContain('online')
    expect(wrapper.text()).toContain('Ready')
  })
})
