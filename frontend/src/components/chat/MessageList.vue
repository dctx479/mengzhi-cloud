<template>
  <div class="message-list" ref="listContainer" @scroll.passive="handleScroll">
    <!-- 空状态 -->
    <div v-if="messages.length === 0" class="empty-state">
      <el-empty description="暂无消息，开始对话吧" />
    </div>

    <!-- 消息列表 -->
    <div v-else class="messages-container">
      <!-- 加载更多提示 -->
      <div v-if="hasMoreMessages" class="load-more-hint">
        <el-button text size="small" @click="loadMoreMessages">
          加载更多消息
        </el-button>
      </div>

      <!-- 消息项 -->
      <div
        v-for="message in displayMessages"
        :key="message.id"
        class="message-item"
      >
        <MessageBubble
          :message="message"
          :is-loading="isStreamingMessage(message.id)"
          :show-time="showTime"
          @regenerate="handleRegenerate(message)"
          @delete="handleDelete(message.id)"
          @favorite="handleFavorite(message.id)"
        />
      </div>

      <!-- 加载状态 -->
      <div v-if="isLoading" class="loading-indicator">
        <el-icon class="loading-icon">
          <Loading />
        </el-icon>
        <span>正在等待 AI 回应...</span>
      </div>

      <!-- 消息发送失败提示 -->
      <div v-if="failedMessageId" class="failed-message-hint">
        <el-alert
          type="error"
          title="消息发送失败"
          :description="error || '未知错误'"
          closable
          @close="failedMessageId = null"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import type { Message } from '@/types/chat'
import MessageBubble from './MessageBubble.vue'

interface Props {
  messages: Message[]
  isLoading?: boolean
  showTime?: boolean
  showActions?: boolean
  streamingMessageId?: string | null
  error?: string | null
}

interface Emits {
  (e: 'delete-message', messageId: string): void
  (e: 'regenerate', message: Message): void
  (e: 'favorite', messageId: string): void
  (e: 'load-more'): void
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  showTime: true,
  showActions: true,
  streamingMessageId: null,
  error: null,
})

const emit = defineEmits<Emits>()

const listContainer = ref<HTMLElement>()
const hasMoreMessages = ref(false)
const failedMessageId = ref<string | null>(null)
const currentScrollPosition = ref(0)

const displayMessages = computed(() => {
  return [...props.messages].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )
})

const isStreamingMessage = (messageId: string): boolean => {
  return messageId === props.streamingMessageId && props.isLoading
}

const scrollToBottom = () => {
  nextTick(() => {
    if (listContainer.value) {
      listContainer.value.scrollTop = listContainer.value.scrollHeight
      currentScrollPosition.value = listContainer.value.scrollHeight
    }
  })
}

const scrollToMessage = (messageId: string) => {
  nextTick(() => {
    const messageEl = listContainer.value?.querySelector(
      `[data-message-id="${messageId}"]`
    )
    if (messageEl) {
      messageEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  })
}

const handleScroll = () => {
  if (!listContainer.value) return

  const { scrollTop, scrollHeight } = listContainer.value
  currentScrollPosition.value = scrollTop

  // 检查是否滚动到顶部，加载更多消息
  if (scrollTop < scrollHeight * 0.2 && hasMoreMessages.value) {
    emit('load-more')
  }
}

const loadMoreMessages = () => {
  emit('load-more')
}

const handleDelete = (messageId: string) => {
  ElMessageBox.confirm('确定删除此消息吗？', '提示', {
    confirmButtonText: '是',
    cancelButtonText: '否',
    type: 'warning',
  })
    .then(() => {
      emit('delete-message', messageId)
      ElMessage.success('消息已删除')
    })
    .catch((error: any) => {
      // Only ignore cancel action, not errors
      if (error?.action !== 'cancel') {
        console.error('Delete message error:', error)
      }
    })
}

const handleRegenerate = (message: Message) => {
  ElMessageBox.confirm('确定重新生成此消息吗？', '提示', {
    confirmButtonText: '是',
    cancelButtonText: '否',
    type: 'warning',
  })
    .then(async () => {
      try {
        emit('regenerate', message)
        ElMessage.success('正在重新生成...')
      } catch (error) {
        ElMessage.error('重新生成失败')
      }
    })
    .catch((error: any) => {
      // Only ignore cancel action, not errors
      if (error?.action !== 'cancel') {
        console.error('Regenerate message error:', error)
      }
    })
}

const handleFavorite = (messageId: string) => {
  emit('favorite', messageId)
}

// 自动滚动到底部（当有新消息时）
watch(
  () => props.messages.length,
  async () => {
    if (props.isLoading || props.streamingMessageId) {
      // 如果正在加载或流式响应，持续滚动到底部
      scrollToBottom()
    }
  }
)

// 当流式响应消息更新时滚动
watch(
  () => props.streamingMessageId,
  () => {
    if (props.streamingMessageId && props.isLoading) {
      scrollToBottom()
    }
  }
)

// 当有错误时显示失败提示
watch(
  () => props.error,
  (newError) => {
    if (newError) {
      failedMessageId.value = props.streamingMessageId
    }
  }
)

// 初始化滚动
onMounted(() => {
  scrollToBottom()
})

// 暴露方法给父组件
defineExpose({
  scrollToBottom,
  scrollToMessage,
})
</script>

<style scoped lang="scss">
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: white;
  display: flex;
  flex-direction: column;
  scroll-behavior: smooth;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: #d9d9d9;
    border-radius: 3px;

    &:hover {
      background: #bfbfbf;
    }
  }

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
  }

  .messages-container {
    display: flex;
    flex-direction: column;
    gap: 8px;

    .load-more-hint {
      display: flex;
      justify-content: center;
      padding: 12px 0;
      margin-bottom: 8px;
      border-bottom: 1px solid #f0f0f0;

      .el-button {
        margin: 0;
      }
    }

    .message-item {
      display: flex;
      animation: fadeIn 0.3s ease-out;

      &:hover {
        .message-bubble {
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
          border-radius: 12px;
          padding: 4px;
        }
      }
    }
  }

  .loading-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: #999;
    font-size: 14px;
    padding: 20px 0;
    margin-top: 12px;

    .loading-icon {
      animation: spin 1s linear infinite;
    }
  }

  .failed-message-hint {
    margin-top: 12px;
    padding: 0 4px;

    :deep(.el-alert) {
      border-radius: 4px;
    }
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .message-list {
    padding: 12px;

    .messages-container {
      gap: 4px;
    }
  }
}
</style>

