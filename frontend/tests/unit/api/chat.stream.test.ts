import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import * as chatAPI from '@/api/chat'

describe('Chat API - Streaming', () => {
  let eventSourceMock: any

  beforeEach(() => {
    // Mock EventSource
    const mockEventSource = {
      addEventListener: vi.fn(),
      close: vi.fn()
    }

    eventSourceMock = mockEventSource

    // @ts-ignore
    global.EventSource = vi.fn((url, config) => mockEventSource)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('creates EventSource with correct URL', async () => {
    const onChunk = vi.fn()
    const promise = chatAPI.sendMessageStream('chat-123', 'test message', onChunk)

    expect(global.EventSource).toHaveBeenCalledWith(
      expect.stringContaining('chat-123'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: expect.stringContaining('Bearer')
        })
      })
    )

    // Simulate completion
    const doneHandler = eventSourceMock.addEventListener.mock.calls.find(
      (call: any) => call[0] === 'done'
    )?.[1]
    doneHandler?.()

    await promise

    expect(eventSourceMock.close).toHaveBeenCalled()
  })

  it('handles stream chunks correctly', async () => {
    const onChunk = vi.fn()
    const promise = chatAPI.sendMessageStream('chat-123', 'test', onChunk)

    // Get the chunk handler
    const chunkHandler = eventSourceMock.addEventListener.mock.calls.find(
      (call: any) => call[0] === 'chunk'
    )?.[1]

    // Simulate chunk event
    const mockEvent = {
      data: JSON.stringify({ type: 'chunk', content: 'Hello' })
    }
    chunkHandler?.(mockEvent)

    expect(onChunk).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'chunk',
        content: 'Hello'
      })
    )

    // Complete stream
    const doneHandler = eventSourceMock.addEventListener.mock.calls.find(
      (call: any) => call[0] === 'done'
    )?.[1]
    doneHandler?.()

    await promise
  })

  it('handles stream errors correctly', async () => {
    const onChunk = vi.fn()
    const onError = vi.fn()
    const promise = chatAPI.sendMessageStream('chat-123', 'test', onChunk, onError)

    // Get the error handler
    const errorHandler = eventSourceMock.addEventListener.mock.calls.find(
      (call: any) => call[0] === 'error'
    )?.[1]

    // Simulate error event
    errorHandler?.({})

    await expect(promise).rejects.toThrow()
    expect(onError).toHaveBeenCalled()
    expect(eventSourceMock.close).toHaveBeenCalled()
  })

  it('handles multiple chunks in stream', async () => {
    const onChunk = vi.fn()
    const promise = chatAPI.sendMessageStream('chat-123', 'test', onChunk)

    const chunkHandler = eventSourceMock.addEventListener.mock.calls.find(
      (call: any) => call[0] === 'chunk'
    )?.[1]

    // Simulate multiple chunks
    chunkHandler?.({ data: JSON.stringify({ type: 'chunk', content: 'Hello' }) })
    chunkHandler?.({ data: JSON.stringify({ type: 'chunk', content: ' ' }) })
    chunkHandler?.({ data: JSON.stringify({ type: 'chunk', content: 'World' }) })

    expect(onChunk).toHaveBeenCalledTimes(3)

    // Complete
    const doneHandler = eventSourceMock.addEventListener.mock.calls.find(
      (call: any) => call[0] === 'done'
    )?.[1]
    doneHandler?.()

    await promise
  })

  it('handles malformed chunk data gracefully', async () => {
    const onChunk = vi.fn()
    const promise = chatAPI.sendMessageStream('chat-123', 'test', onChunk)

    const chunkHandler = eventSourceMock.addEventListener.mock.calls.find(
      (call: any) => call[0] === 'chunk'
    )?.[1]

    // Simulate invalid JSON
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    chunkHandler?.({ data: 'invalid json' })

    expect(consoleSpy).toHaveBeenCalled()

    consoleSpy.mockRestore()

    // Complete
    const doneHandler = eventSourceMock.addEventListener.mock.calls.find(
      (call: any) => call[0] === 'done'
    )?.[1]
    doneHandler?.()

    await promise
  })

  it('closes connection on done event', async () => {
    const onChunk = vi.fn()
    const promise = chatAPI.sendMessageStream('chat-123', 'test', onChunk)

    const doneHandler = eventSourceMock.addEventListener.mock.calls.find(
      (call: any) => call[0] === 'done'
    )?.[1]

    doneHandler?.()

    await promise

    expect(eventSourceMock.close).toHaveBeenCalled()
  })

  it('passes authentication token in headers', async () => {
    localStorage.setItem('token', 'test-token-123')

    const onChunk = vi.fn()
    const promise = chatAPI.sendMessageStream('chat-123', 'test', onChunk)

    expect(global.EventSource).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token-123'
        })
      })
    )

    const doneHandler = eventSourceMock.addEventListener.mock.calls.find(
      (call: any) => call[0] === 'done'
    )?.[1]
    doneHandler?.()

    await promise

    localStorage.removeItem('token')
  })
})
