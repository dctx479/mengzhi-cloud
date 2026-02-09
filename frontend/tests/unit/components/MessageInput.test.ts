import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageInput from '@/components/chat/MessageInput.vue'
import FileUpload from '@/components/chat/FileUpload.vue'
import ElementPlus from 'element-plus'

describe('MessageInput.vue', () => {
  let wrapper: any

  beforeEach(() => {
    wrapper = mount(MessageInput, {
      global: {
        plugins: [ElementPlus],
        components: {
          FileUpload
        }
      }
    })
  })

  it('renders input component', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.message-input-wrapper').exists()).toBe(true)
  })

  it('initializes with empty message', () => {
    expect(wrapper.vm.message).toBe('')
  })

  it('initializes with empty selected files', () => {
    expect(wrapper.vm.selectedFiles).toEqual([])
  })

  it('enables send button only when message is not empty', async () => {
    expect(wrapper.vm.canSend).toBe(false)

    wrapper.vm.message = 'Hello'
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.canSend).toBe(true)
  })

  it('enables send button when files are selected', async () => {
    wrapper.vm.selectedFiles = [
      { id: '1', name: 'test.txt', size: 100, type: 'text/plain', url: '', uploadedAt: '' }
    ]
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.canSend).toBe(true)
  })

  it('handles Enter key for sending', async () => {
    wrapper.vm.message = 'Test message'
    await wrapper.vm.$nextTick()

    const event = new KeyboardEvent('keydown', { key: 'Enter', shiftKey: false })
    wrapper.vm.handleKeyDown(event)

    // Check that send was called
    expect(wrapper.emitted('send')).toBeTruthy()
  })

  it('allows Shift+Enter for line break', async () => {
    const event = new KeyboardEvent('keydown', { key: 'Enter', shiftKey: true })
    wrapper.vm.handleKeyDown(event)

    // Should not send
    expect(wrapper.emitted('send')).toBeFalsy()
  })

  it('sends message with correct payload', async () => {
    wrapper.vm.message = 'Test message'
    wrapper.vm.selectedFiles = [
      { id: '1', name: 'test.txt', size: 100, type: 'text/plain', url: '', uploadedAt: '' }
    ]
    await wrapper.vm.$nextTick()

    wrapper.vm.handleSend()

    expect(wrapper.emitted('send')).toBeTruthy()
    const sendEvent = wrapper.emitted('send')[0]
    expect(sendEvent[0]).toBe('Test message')
  })

  it('clears message after sending', async () => {
    wrapper.vm.message = 'Test message'
    await wrapper.vm.$nextTick()

    wrapper.vm.handleSend()
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.message).toBe('')
  })

  it('clears selected files after sending', async () => {
    wrapper.vm.message = 'Test'
    wrapper.vm.selectedFiles = [
      { id: '1', name: 'test.txt', size: 100, type: 'text/plain', url: '', uploadedAt: '' }
    ]
    await wrapper.vm.$nextTick()

    wrapper.vm.handleSend()
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.selectedFiles).toEqual([])
  })

  it('removes selected file', async () => {
    wrapper.vm.selectedFiles = [
      { id: '1', name: 'test.txt', size: 100, type: 'text/plain', url: '', uploadedAt: '' },
      { id: '2', name: 'file.pdf', size: 200, type: 'application/pdf', url: '', uploadedAt: '' }
    ]
    await wrapper.vm.$nextTick()

    wrapper.vm.removeSelectedFile('1')

    expect(wrapper.vm.selectedFiles.length).toBe(1)
    expect(wrapper.vm.selectedFiles[0].id).toBe('2')
  })

  it('toggles file upload section', async () => {
    expect(wrapper.vm.showFileUpload).toBe(false)

    wrapper.vm.toggleFileUpload()
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.showFileUpload).toBe(true)
  })

  it('opens settings dialog', async () => {
    wrapper.vm.openSettings()
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.settingsVisible).toBe(true)
  })

  it('saves settings and emits event', async () => {
    wrapper.vm.settings = {
      streamEnabled: false,
      temperature: 0.5,
      maxTokens: 1000
    }
    await wrapper.vm.$nextTick()

    wrapper.vm.saveSettings()

    expect(wrapper.emitted('settings-change')).toBeTruthy()
    const settingsEvent = wrapper.emitted('settings-change')[0]
    expect(settingsEvent[0].streamEnabled).toBe(false)
  })

  it('handles file selection from input', async () => {
    const file = new File(['content'], 'image.png', { type: 'image/png' })
    const dataTransfer = { files: [file] }

    // Simulate file selection
    wrapper.vm.handleImageSelect({
      target: { files: [file] }
    })

    // Should have uploaded the file
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.selectedFiles.length).toBeGreaterThan(0)
  })

  it('shows files count in hint', async () => {
    wrapper.vm.selectedFiles = [
      { id: '1', name: 'test.txt', size: 100, type: 'text/plain', url: '', uploadedAt: '' },
      { id: '2', name: 'file.pdf', size: 200, type: 'application/pdf', url: '', uploadedAt: '' }
    ]
    await wrapper.vm.$nextTick()

    const hint = wrapper.find('.files-count')
    expect(hint.text()).toContain('2')
  })

  it('respects loading prop', async () => {
    await wrapper.setProps({ loading: true })

    expect(wrapper.vm.canSend).toBe(false)
  })
})
