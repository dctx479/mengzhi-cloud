import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import { testDataGenerators, waitForComponent } from '../../utils/test-utils'

/**
 * MessageBubble 组件测试
 * 测试消息气泡的样式、时间戳格式化和加载状态
 */

describe('MessageBubble Component', () => {
  it('renders user message correctly', () => {
    const message = testDataGenerators.createMessage({
      role: 'user',
      content: '你好，这是一条用户消息',
    })

    const wrapper = mount(MessageBubble, {
      props: {
        message,
        showTime: false,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    expect(wrapper.text()).toContain('你好，这是一条用户消息')
    expect(wrapper.classes()).toContain('user-message')
  })

  it('renders assistant message correctly', () => {
    const message = testDataGenerators.createMessage({
      role: 'assistant',
      content: '我是AI助手，很高兴认识你',
    })

    const wrapper = mount(MessageBubble, {
      props: {
        message,
        showTime: false,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    expect(wrapper.text()).toContain('我是AI助手，很高兴认识你')
    expect(wrapper.classes()).not.toContain('user-message')
  })

  it('displays formatted timestamp when showTime is true', () => {
    const timestamp = '2024-01-15T14:30:00Z'
    const message = testDataGenerators.createMessage({
      timestamp,
    })

    const wrapper = mount(MessageBubble, {
      props: {
        message,
        showTime: true,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    const timeElement = wrapper.find('.message-time')
    expect(timeElement.exists()).toBe(true)
    expect(timeElement.text()).toMatch(/\d{2}:\d{2}/)
  })

  it('hides timestamp when showTime is false', () => {
    const message = testDataGenerators.createMessage({
      timestamp: '2024-01-15T14:30:00Z',
    })

    const wrapper = mount(MessageBubble, {
      props: {
        message,
        showTime: false,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    const timeElement = wrapper.find('.message-time')
    expect(timeElement.exists()).toBe(false)
  })

  it('shows loading state when isLoading is true', () => {
    const message = testDataGenerators.createMessage()

    const wrapper = mount(MessageBubble, {
      props: {
        message,
        isLoading: true,
        showTime: false,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div class="loading-icon"></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    expect(wrapper.text()).toContain('AI 思考中...')
    const loadingDiv = wrapper.find('.message-loading')
    expect(loadingDiv.exists()).toBe(true)
  })

  it('shows message content when isLoading is false', () => {
    const message = testDataGenerators.createMessage({
      content: '这是一条普通消息',
    })

    const wrapper = mount(MessageBubble, {
      props: {
        message,
        isLoading: false,
        showTime: false,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    expect(wrapper.text()).toContain('这是一条普通消息')
    expect(wrapper.find('.message-loading').exists()).toBe(false)
  })

  it('has correct message bubble structure', () => {
    const message = testDataGenerators.createMessage()

    const wrapper = mount(MessageBubble, {
      props: {
        message,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    expect(wrapper.find('.message-bubble').exists()).toBe(true)
    expect(wrapper.find('.message-content').exists()).toBe(true)
  })

  it('applies different classes for user and assistant messages', () => {
    const userMessage = testDataGenerators.createMessage({ role: 'user' })
    const assistantMessage = testDataGenerators.createMessage({ role: 'assistant' })

    const userWrapper = mount(MessageBubble, {
      props: { message: userMessage, showTime: false },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    const assistantWrapper = mount(MessageBubble, {
      props: { message: assistantMessage, showTime: false },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    expect(userWrapper.classes()).toContain('user-message')
    expect(assistantWrapper.classes()).not.toContain('user-message')
  })

  it('formats different timestamps correctly', () => {
    const timestamps = [
      '2024-01-15T09:00:00Z',
      '2024-01-15T14:30:45Z',
      '2024-01-15T23:59:59Z',
    ]

    timestamps.forEach(timestamp => {
      const message = testDataGenerators.createMessage({ timestamp })

      const wrapper = mount(MessageBubble, {
        props: {
          message,
          showTime: true,
        },
        global: {
          stubs: {
            ElIcon: { template: '<div></div>' },
            Loading: { template: '<div></div>' },
          },
        },
      })

      const timeElement = wrapper.find('.message-time')
      expect(timeElement.exists()).toBe(true)
      // 验证时间格式为HH:mm
      expect(timeElement.text()).toMatch(/\d{2}:\d{2}/)
    })
  })

  it('handles long message content', () => {
    const longContent = '这是一条很长的消息，'.repeat(20)
    const message = testDataGenerators.createMessage({
      content: longContent,
    })

    const wrapper = mount(MessageBubble, {
      props: {
        message,
        showTime: false,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    expect(wrapper.text()).toContain(longContent)
  })

  it('handles special characters in message content', () => {
    const specialContent = '这是包含特殊字符的消息：@#$%^&*()_+-=[]{}|;:\'",.<>?/'
    const message = testDataGenerators.createMessage({
      content: specialContent,
    })

    const wrapper = mount(MessageBubble, {
      props: {
        message,
        showTime: false,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    expect(wrapper.text()).toContain(specialContent)
  })

  it('handles empty message content', () => {
    const message = testDataGenerators.createMessage({
      content: '',
    })

    const wrapper = mount(MessageBubble, {
      props: {
        message,
        showTime: false,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    const content = wrapper.find('.message-text')
    expect(content.exists()).toBe(true)
  })

  it('has correct message props with defaults', () => {
    const message = testDataGenerators.createMessage()

    const wrapper = mount(MessageBubble, {
      props: {
        message,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    // 验证默认 props 应用正确
    expect(wrapper.find('.message-bubble').exists()).toBe(true)
  })

  it('switches between loading and content states', async () => {
    const message = testDataGenerators.createMessage({
      content: '最终消息',
    })

    const wrapper = mount(MessageBubble, {
      props: {
        message,
        isLoading: true,
        showTime: false,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div class="loading-icon"></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    expect(wrapper.text()).toContain('AI 思考中...')

    // 更新为非加载状态
    await wrapper.setProps({ isLoading: false })
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('最终消息')
    expect(wrapper.text()).not.toContain('AI 思考中...')
  })

  it('updates message content reactively', async () => {
    const message = testDataGenerators.createMessage({
      content: '初始消息',
    })

    const wrapper = mount(MessageBubble, {
      props: {
        message,
        showTime: false,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    expect(wrapper.text()).toContain('初始消息')

    // 更新消息
    const newMessage = { ...message, content: '更新后的消息' }
    await wrapper.setProps({ message: newMessage })
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('更新后的消息')
    expect(wrapper.text()).not.toContain('初始消息')
  })

  it('maintains message role classification', () => {
    const message = testDataGenerators.createMessage({ role: 'user' })

    const wrapper = mount(MessageBubble, {
      props: {
        message,
        showTime: false,
      },
      global: {
        stubs: {
          ElIcon: { template: '<div></div>' },
          Loading: { template: '<div></div>' },
        },
      },
    })

    const bubble = wrapper.find('.message-bubble')
    expect(bubble.classes('user-message')).toBe(true)
  })
})
