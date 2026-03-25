import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import FileUpload from '@/components/chat/FileUpload.vue'
import ElementPlus from 'element-plus'

describe('FileUpload.vue', () => {
  let wrapper: VueWrapper<InstanceType<typeof FileUpload>>

  beforeEach(() => {
    wrapper = mount(FileUpload, {
      global: {
        plugins: [ElementPlus]
      }
    })
  })

  it('renders upload component', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.file-upload-container').exists()).toBe(true)
  })

  it('displays upload area with correct text', () => {
    const uploadArea = wrapper.find('.upload-area')
    expect(uploadArea.exists()).toBe(true)
    expect(uploadArea.text()).toContain('点击或拖拽上传文件')
  })

  it('initializes with empty uploaded files', () => {
    expect(wrapper.vm.uploadedFiles).toEqual([])
  })

  it('formats file size correctly', () => {
    const result = wrapper.vm.formatFileSize(1024 * 1024) // 1MB
    expect(result).toContain('MB')
  })

  it('identifies images correctly', () => {
    expect(wrapper.vm.isImage('image/png')).toBe(true)
    expect(wrapper.vm.isImage('image/jpeg')).toBe(true)
    expect(wrapper.vm.isImage('application/pdf')).toBe(false)
  })

  it('validates file size before upload', () => {
    const largeFile = new File(['x'.repeat(30 * 1024 * 1024)], 'large.txt', { type: 'text/plain' })
    const result = wrapper.vm.beforeUpload(largeFile)
    expect(result).toBe(false)
  })

  it('validates file type before upload', () => {
    const invalidFile = new File(['content'], 'test.exe', { type: 'application/x-msdownload' })
    const result = wrapper.vm.beforeUpload(invalidFile)
    expect(result).toBe(false)
  })

  it('allows valid files', () => {
    const validFile = new File(['content'], 'test.txt', { type: 'text/plain' })
    const result = wrapper.vm.beforeUpload(validFile)
    expect(result).toBe(true)
  })

  it('removes files from uploaded list', async () => {
    const mockFile = {
      id: 'test-1',
      name: 'test.txt',
      size: 100,
      type: 'text/plain',
      url: 'http://example.com/test.txt',
      uploadedAt: new Date().toISOString()
    }

    wrapper.vm.uploadedFiles.push(mockFile)
    await wrapper.vm.$nextTick()

    wrapper.vm.removeFile('test-1')
    expect(wrapper.vm.uploadedFiles).toEqual([])
  })

  it('clears all files', async () => {
    wrapper.vm.uploadedFiles = [
      { id: '1', name: 'file1.txt', size: 100, type: 'text/plain', url: '', uploadedAt: '' },
      { id: '2', name: 'file2.txt', size: 200, type: 'text/plain', url: '', uploadedAt: '' }
    ]
    await wrapper.vm.$nextTick()

    wrapper.vm.clearAllFiles()
    expect(wrapper.vm.uploadedFiles).toEqual([])
  })

  it('exposes getUploadedFiles method', () => {
    const mockFile = {
      id: 'test-1',
      name: 'test.txt',
      size: 100,
      type: 'text/plain',
      url: 'http://example.com/test.txt',
      uploadedAt: new Date().toISOString()
    }

    wrapper.vm.uploadedFiles = [mockFile]
    const files = wrapper.vm.getUploadedFiles()
    expect(files).toEqual([mockFile])
  })

  it('formats time correctly', () => {
    const now = new Date().toISOString()
    const result = wrapper.vm.formatTime(now)
    expect(result).toBeTruthy()
  })

  it('handles upload success', async () => {
    const mockResponse = {
      id: 'upload-1',
      name: 'test.txt',
      size: 100,
      type: 'text/plain',
      url: 'http://example.com/test.txt',
      uploadedAt: new Date().toISOString()
    }

    wrapper.vm.handleUploadSuccess(mockResponse)
    expect(wrapper.vm.uploadedFiles).toContain(mockResponse)
  })

  it('emits files-uploaded event', async () => {
    const mockFile = {
      id: 'test-1',
      name: 'test.txt',
      size: 100,
      type: 'text/plain',
      url: 'http://example.com/test.txt',
      uploadedAt: new Date().toISOString()
    }

    wrapper.vm.handleUploadSuccess(mockFile)
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('files-uploaded')).toBeTruthy()
  })
})
