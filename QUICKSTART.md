# 智能对话界面优化 - 快速启动指南

## 功能概览

本指南帮助开发者快速了解和使用优化后的智能对话界面新功能。

## 1. 文件上传功能

### 组件位置
```
/frontend/src/components/chat/FileUpload.vue
```

### 基本使用
```vue
<template>
  <FileUpload
    :chat-id="currentChatId"
    :multiple="true"
    :drag="true"
    button-text="上传文件"
    @files-uploaded="handleFilesUploaded"
  />
</template>

<script setup>
import FileUpload from '@/components/chat/FileUpload.vue'

const handleFilesUploaded = (files) => {
  console.log('已上传文件:', files)
  // 发送带文件的消息
  chatStore.sendMessage(message, files)
}
</script>
```

### 配置选项
```typescript
interface Props {
  chatId?: string                    // 对话ID
  multiple?: boolean                 // 支持多文件 (默认: true)
  drag?: boolean                     // 启用拖拽 (默认: true)
  buttonText?: string                // 按钮文本
  maxFileSize?: number               // 最大文件大小 (默认: 20MB)
  allowedTypes?: string[]            // 允许的文件类型
}
```

### 支持的文件类型
- **图片**: JPG, PNG, WebP (最大10MB)
- **文档**: PDF, DOCX, TXT (最大20MB)
- **表格**: XLSX, CSV (最大5MB)

### 暴露的方法
```typescript
// 获取已上传文件列表
const files = fileUploadRef.getUploadedFiles()

// 清空所有文件
fileUploadRef.clearFiles()
```

## 2. Markdown渲染

### 组件位置
```
/frontend/src/components/chat/MarkdownRenderer.vue
```

### 基本使用
```vue
<template>
  <MarkdownRenderer :content="messageContent" />
</template>

<script setup>
import MarkdownRenderer from '@/components/chat/MarkdownRenderer.vue'

const messageContent = `
# 标题
**加粗**和*斜体*文本

## 代码示例
\`\`\`javascript
const x = 1;
\`\`\`

- 列表项1
- 列表项2

[链接](https://example.com)
`
</script>
```

### 支持的格式
- 标题 (H1-H6)
- **加粗** *斜体* ~~删除线~~
- `行内代码` 和代码块 (支持语法高亮)
- 有序和无序列表
- 表格
- 引用块
- 链接 (自动新窗口打开)
- 图片
- 水平线

## 3. 消息气泡增强功能

### 新增特性
```vue
<template>
  <MessageBubble
    :message="message"
    :is-loading="isLoading"
    :show-time="true"
    @regenerate="handleRegenerate"
    @delete="handleDelete"
    @favorite="handleFavorite"
  />
</template>
```

### 消息对象扩展
```typescript
interface Message {
  // ... 原有字段
  files?: FileAttachment[]        // 附件文件
  images?: ImageAttachment[]      // 图片附件
  isStreaming?: boolean           // 是否流式传输中
}
```

### 事件处理
```typescript
const handleRegenerate = async () => {
  // 重新生成AI回复
  await chatStore.regenerateMessage(messageId)
}

const handleDelete = async () => {
  // 删除消息
  await chatStore.deleteMessage(messageId)
}

const handleFavorite = async () => {
  // 收藏/取消收藏
  await chatStore.toggleMessageFavorite(messageId)
}
```

## 4. 流式响应功能

### 启用流式响应
```typescript
// 在MessageInput中设置
const settings = {
  streamEnabled: true,
  temperature: 0.7,
  maxTokens: 2000
}

// 发送流式消息
await chatStore.sendMessage(
  'Your message',
  undefined,
  true  // useStream = true
)
```

### 监听流式响应
```typescript
// Store中自动处理流式更新
watch(() => chatStore.messages, (messages) => {
  const lastMessage = messages[messages.length - 1]
  if (lastMessage?.isStreaming) {
    console.log('正在流式传输:', lastMessage.content)
  }
})
```

### 错误处理
```typescript
watch(() => chatStore.error, (error) => {
  if (error) {
    ElMessage.error(`错误: ${error}`)
  }
})
```

## 5. 消息输入优化

### 新增功能
```vue
<template>
  <MessageInput
    :chat-id="currentChatId"
    :loading="chatStore.messageLoading"
    placeholder="输入消息..."
    @send="handleSend"
    @settings-change="handleSettingsChange"
  />
</template>

<script setup>
const handleSend = async (message, files) => {
  // 发送消息和文件
  await chatStore.sendMessage(message, files, settings.streamEnabled)
}

const handleSettingsChange = (newSettings) => {
  // 更新对话设置
  settings.value = newSettings
  console.log('新设置:', newSettings)
}
</script>
```

### 快捷键
- `Enter`: 发送消息
- `Shift + Enter`: 换行
- 点击"上传文件": 打开文件选择
- 点击"上传图片": 快速上传图片

## 6. 消息列表高级功能

### 使用MessageList
```vue
<template>
  <MessageList
    :messages="chatStore.messages"
    :is-loading="chatStore.messageLoading"
    :streaming-message-id="chatStore.streamingMessageId"
    :error="chatStore.error"
    @delete-message="handleDelete"
    @regenerate="handleRegenerate"
    @favorite="handleFavorite"
    @load-more="handleLoadMore"
  />
</template>
```

### 暴露的方法
```typescript
const messageListRef = ref()

// 滚动到底部
messageListRef.value.scrollToBottom()

// 滚动到指定消息
messageListRef.value.scrollToMessage(messageId)
```

## 7. Store API

### 新增方法

#### 发送消息 (支持流式)
```typescript
await chatStore.sendMessage(
  content: string,
  files?: FileUploadResponse[],
  useStream?: boolean
)
```

#### 重新生成消息
```typescript
const newMessage = await chatStore.regenerateMessage(messageId)
```

#### 导出对话
```typescript
// JSON格式
const data = await chatStore.exportConversation('json')

// Markdown格式
const markdown = await chatStore.exportConversation('markdown')
```

#### 收藏消息
```typescript
await chatStore.toggleMessageFavorite(messageId)
```

#### 重命名对话
```typescript
await chatStore.renameChat(chatId, newTitle)
```

## 8. 完整示例

### ChatPage集成示例
```vue
<template>
  <div class="chat-page">
    <!-- 消息列表 -->
    <MessageList
      ref="messageListRef"
      :messages="chatStore.messages"
      :is-loading="chatStore.messageLoading"
      :streaming-message-id="chatStore.streamingMessageId"
      :error="chatStore.error"
      @delete-message="handleDeleteMessage"
      @regenerate="handleRegenerate"
      @favorite="handleFavorite"
      @load-more="handleLoadMore"
    />

    <!-- 消息输入 -->
    <MessageInput
      :chat-id="currentChat?.id"
      :loading="chatStore.messageLoading"
      @send="handleSendMessage"
      @settings-change="handleSettingsChange"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import MessageList from '@/components/chat/MessageList.vue'
import MessageInput from '@/components/chat/MessageInput.vue'

const chatStore = useChatStore()
const messageListRef = ref()
const settings = ref({
  streamEnabled: true,
  temperature: 0.7,
  maxTokens: 2000
})

const handleSendMessage = async (message, files) => {
  try {
    await chatStore.sendMessage(message, files, settings.value.streamEnabled)
    messageListRef.value?.scrollToBottom()
  } catch (error) {
    console.error('发送失败:', error)
  }
}

const handleDeleteMessage = async (messageId) => {
  await chatStore.deleteMessage(messageId)
}

const handleRegenerate = async (message) => {
  await chatStore.regenerateMessage(message.id)
}

const handleFavorite = async (messageId) => {
  await chatStore.toggleMessageFavorite(messageId)
}

const handleLoadMore = async () => {
  // 实现消息历史加载
}

const handleSettingsChange = (newSettings) => {
  settings.value = newSettings
}
</script>
```

## 9. 环境变量配置

### .env 文件
```env
# API配置
VITE_API_BASE=http://localhost:3000/api

# 可选的功能开关
VITE_ENABLE_STREAM=true
VITE_ENABLE_FILE_UPLOAD=true
VITE_MAX_FILE_SIZE=20971520
```

## 10. 测试运行

### 运行所有测试
```bash
cd frontend
npm run test
```

### 运行特定测试文件
```bash
npm run test MarkdownRenderer.test.ts
npm run test FileUpload.test.ts
npm run test MessageInput.test.ts
npm run test chat.stream.test.ts
```

### 查看测试覆盖率
```bash
npm run test:coverage
```

## 11. 性能优化建议

### 长对话列表
```typescript
// 对于超过100条消息，考虑虚拟化
// 未来可实现VirtualList组件
```

### 大文件上传
```typescript
// 当前支持单个20MB文件
// 建议用户上传前压缩大文件
```

### Markdown性能
```typescript
// 避免在一条消息中包含过多Markdown元素
// 对于超过10000字符的内容，考虑分割
```

## 12. 常见问题

### Q: 如何自定义允许的文件类型？
A: 在FileUpload组件中传入allowedTypes prop:
```typescript
:allowed-types="['image/png', 'application/pdf']"
```

### Q: 流式响应在弱网环境下表现如何？
A: EventSource会自动重连。建议添加超时处理:
```typescript
const timeout = setTimeout(() => {
  // 用户手动取消或超时处理
}, 30000)
```

### Q: 如何实现消息编辑功能？
A: 使用 `renameChat` 方式可扩展到消息编辑:
```typescript
// 需要后端支持
await api.updateMessage(messageId, newContent)
```

### Q: 支持哪些Markdown扩展？
A: 当前支持标准Markdown。可通过markdown-it插件扩展:
```typescript
import plugin from 'markdown-it-plugin'
md.use(plugin)
```

## 13. 调试技巧

### 启用详细日志
```typescript
// 在api/chat.ts中
const DEBUG = true

if (DEBUG) {
  console.log('消息流:', chunk)
}
```

### 网络监视
```
浏览器DevTools → Network → 过滤SSE事件
查看Event Stream的数据流
```

### 性能分析
```
DevTools → Performance → 录制消息发送过程
分析瓶颈位置
```

---

**更多帮助**
- 项目文档: `OPTIMIZATION_REPORT.md`
- 类型定义: `types/chat.ts`
- API文档: `api/chat.ts`
- Store文档: `stores/chat.ts`
