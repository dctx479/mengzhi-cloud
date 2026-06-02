<template>
  <div class="message-bubble" :class="{ 'user-message': isUserMessage }">
    <div class="message-avatar">
      <div v-if="isUserMessage" class="user-avatar">
        <el-icon :size="18"><User /></el-icon>
      </div>
      <div v-else class="ai-avatar">
        <el-icon :size="18"><Monitor /></el-icon>
      </div>
    </div>

    <div class="message-wrapper">
      <!-- 消息内容 -->
      <div class="message-content">
        <!-- 纯文本或 Markdown 渲染 -->
        <MarkdownRenderer v-if="!isLoading && isMarkdownContent" :content="message.content" />
        <p v-else-if="!isLoading" class="message-text">{{ message.content }}</p>

        <!-- 加载状态 -->
        <div v-if="isLoading" class="message-loading">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span>AI 思考中...</span>
        </div>
      </div>

      <!-- 图片附件 -->
      <div v-if="message.images && message.images.length > 0" class="message-images">
        <div
          v-for="(image, idx) in message.images"
          :key="`img-${idx}`"
          class="image-item"
          @click="previewImage(image)"
        >
          <img :src="image.url" :alt="image.name" class="message-image" />
          <div class="image-overlay">
            <el-icon><ZoomIn /></el-icon>
          </div>
        </div>
      </div>

      <!-- 文件附件 -->
      <div v-if="message.files && message.files.length > 0" class="message-files">
        <div v-for="(file, idx) in message.files" :key="`file-${idx}`" class="file-item">
          <el-icon :size="16" class="file-icon"><Document /></el-icon>
          <span class="file-name">{{ file.name }}</span>
          <span class="file-size">({{ formatFileSize(file.size) }})</span>
        </div>
      </div>

      <!-- 消息元数据 -->
      <div class="message-meta">
        <span class="message-time">{{ formatTime(message.timestamp) }}</span>
        <div v-if="!isLoading" class="message-actions">
          <el-tooltip v-if="message.role === 'assistant'" content="复制">
            <el-button
              type="primary"
              text
              size="small"
              icon="DocumentCopy"
              @click="copyMessage"
            />
          </el-tooltip>
          <el-tooltip v-if="message.role === 'assistant'" content="重新生成">
            <el-button
              type="primary"
              text
              size="small"
              icon="Refresh"
              @click="regenerate"
            />
          </el-tooltip>
          <el-tooltip v-if="message.role === 'assistant'" content="收藏">
            <el-button
              type="primary"
              text
              size="small"
              :icon="isFavorited ? 'StarFilled' : 'Star'"
              @click="toggleFavorite"
            />
          </el-tooltip>
          <el-tooltip content="删除">
            <el-button
              type="danger"
              text
              size="small"
              icon="Delete"
              @click="deleteMessage"
            />
          </el-tooltip>
        </div>
      </div>
    </div>

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="imagePreviewVisible"
      width="70%"
      :close-on-click-modal="true"
      :show-close="true"
    >
      <img
        v-if="previewingImage"
        :src="previewingImage.url"
        :alt="previewingImage.name"
        class="preview-image-large"
      />
      <div class="preview-image-name">{{ previewingImage?.name }}</div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, ZoomIn, User, Monitor } from '@element-plus/icons-vue'
import type { Message, ImageAttachment } from '@/types/chat'
import MarkdownRenderer from './MarkdownRenderer.vue'

interface Props {
  message: Message
  isLoading?: boolean
  showTime?: boolean
}

interface Emits {
  (e: 'regenerate'): void
  (e: 'delete'): void
  (e: 'favorite'): void
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  showTime: true,
})

const emit = defineEmits<Emits>()

const imagePreviewVisible = ref(false)
const previewingImage = ref<ImageAttachment | null>(null)
const isFavorited = ref(false)

const isUserMessage = computed(() => props.message.role === 'user')

const isMarkdownContent = computed(() => {
  const content = props.message.content
  // 简单的 Markdown 检测逻辑
  return /[#\-\*\[\]`\|]|^\s*```|^>/.test(content) || props.message.content.includes('\n')
})

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) {
    return '刚刚'
  } else if (diffMins < 60) {
    return `${diffMins}分钟前`
  } else if (diffMins < 1440) {
    const hours = Math.floor(diffMins / 60)
    return `${hours}小时前`
  } else {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + sizes[i]
}

const previewImage = (image: ImageAttachment) => {
  previewingImage.value = image
  imagePreviewVisible.value = true
}

const copyMessage = () => {
  navigator.clipboard.writeText(props.message.content).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch((error) => {
    console.error('Copy to clipboard failed:', error)
    ElMessage.error('复制失败，请重试')
  })
}

const regenerate = () => {
  emit('regenerate')
}

const toggleFavorite = () => {
  isFavorited.value = !isFavorited.value
  emit('favorite')
  ElMessage.success(isFavorited.value ? '已收藏' : '已取消收藏')
}

const deleteMessage = () => {
  emit('delete')
}
</script>

<style scoped lang="scss">
.message-bubble {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  animation: slideIn 0.3s ease-out;

  &.user-message {
    flex-direction: row-reverse;

    .message-wrapper {
      align-items: flex-end;
    }

    .message-content {
      background: #0d9668;
      color: white;
      border-radius: 18px 18px 4px 18px;

      :deep(a) {
        color: #b3f0d9;
      }
    }

    .message-avatar {
      .user-avatar {
        background: #e8f5f0;
        color: #0d9668;
      }
    }

    .message-meta {
      flex-direction: row-reverse;
    }
  }

  .message-avatar {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;

    .user-avatar {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #e8f5f0;
      color: #0d9668;
    }

    .ai-avatar {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f0f3f8;
      color: #5b6c8a;
    }
  }

  .message-wrapper {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    max-width: 70%;
    flex: 1;

    .message-content {
      background: #fff;
      color: #333;
      padding: 12px 16px;
      border-radius: 18px 18px 18px 4px;
      word-break: break-word;
      line-height: 1.6;
      min-width: 60px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);

      .message-text {
        margin: 0;
        font-size: 14px;
      }

      .message-loading {
        display: flex;
        align-items: center;
        gap: 8px;

        .typing-indicator {
          display: flex;
          gap: 3px;

          span {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: currentColor;
            animation: typing 1.4s infinite;

            &:nth-child(1) {
              animation-delay: 0s;
            }

            &:nth-child(2) {
              animation-delay: 0.2s;
            }

            &:nth-child(3) {
              animation-delay: 0.4s;
            }
          }
        }
      }
    }

    .message-images {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
      gap: 8px;
      margin-top: 8px;

      .image-item {
        position: relative;
        cursor: pointer;
        border-radius: 8px;
        overflow: hidden;
        height: 120px;

        .message-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
          transition: transform 0.3s;

          &:hover {
            transform: scale(1.05);
          }
        }

        .image-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.6);
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0;
          transition: opacity 0.3s;

          &:hover {
            opacity: 1;
          }

          :deep(.el-icon) {
            color: white;
            font-size: 24px;
          }
        }
      }
    }

    .message-files {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-top: 8px;

      .file-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: #f0faf5;
        border-radius: 8px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s;

        &:hover {
          background: #e0f5eb;
        }

        .file-icon {
          color: #0d9668;
        }

        .file-name {
          flex: 1;
          min-width: 0;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          color: #0d9668;
        }

        .file-size {
          color: #999;
          white-space: nowrap;
        }
      }
    }

    .message-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 4px;
      width: 100%;

      .message-time {
        font-size: 11px;
        color: #bbb;
      }

      .message-actions {
        display: flex;
        gap: 2px;
        margin-left: auto;
        opacity: 0;
        transition: opacity 0.2s;
      }
    }
  }

  &:hover .message-meta .message-actions {
    opacity: 1;
  }

  .preview-image-large {
    width: 100%;
    height: auto;
    max-height: 70vh;
    border-radius: 8px;
  }

  .preview-image-name {
    margin-top: 12px;
    font-size: 12px;
    color: #999;
    text-align: center;
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes typing {
  0%,
  60%,
  100% {
    opacity: 0.5;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-8px);
  }
}

@media (max-width: 768px) {
  .message-bubble {
    .message-wrapper {
      max-width: 85%;

      .message-images {
        grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));

        .image-item {
          height: 80px;
        }
      }
    }
  }
}
</style>

