<template>
  <div class="message-input-wrapper">
    <!-- 文件上传区域（可选） -->
    <div v-if="showFileUpload" class="upload-section">
      <FileUpload
        :chat-id="chatId"
        :drag="false"
        button-text="选择文件"
        @files-uploaded="handleFilesUploaded"
      />
    </div>

    <!-- 已选择的文件显示 -->
    <div v-if="selectedFiles.length > 0" class="selected-files">
      <div v-for="file in selectedFiles" :key="file.id" class="selected-file-item">
        <el-tag closable @close="removeSelectedFile(file.id)">
          {{ file.name }}
        </el-tag>
      </div>
    </div>

    <!-- 消息输入区域 -->
    <div class="input-container">
      <!-- 输入框 -->
      <el-input
        ref="inputRef"
        v-model="message"
        type="textarea"
        :rows="inputRows"
        :placeholder="placeholder"
        resize="none"
        :maxlength="maxLength"
        :show-word-limit="showWordLimit"
        :disabled="loading"
        @keydown="handleKeyDown"
        @input="handleInput"
      />

      <!-- 输入底部 -->
      <div class="input-footer">
        <div class="left-actions">
          <!-- 文件上传按钮 -->
          <el-tooltip content="上传文件" placement="top">
            <el-button
              type="primary"
              text
              size="small"
              icon="DocumentAdd"
              :disabled="loading"
              @click="toggleFileUpload"
            />
          </el-tooltip>

          <!-- 图片上传按钮 -->
          <el-tooltip content="上传图片" placement="top">
            <el-button
              type="primary"
              text
              size="small"
              icon="Picture"
              :disabled="loading"
              @click="uploadImage"
            />
          </el-tooltip>

          <!-- 设置按钮 -->
          <el-tooltip content="设置" placement="top">
            <el-button
              type="primary"
              text
              size="small"
              icon="Setting"
              :disabled="loading"
              @click="openSettings"
            />
          </el-tooltip>
        </div>

        <div class="right-actions">
          <!-- 发送按钮 -->
          <el-button
            type="primary"
            :loading="loading"
            :disabled="!canSend"
            icon="Promotion"
            @click="handleSend"
          >
            {{ loading ? '发送中...' : '发送' }}
          </el-button>
        </div>
      </div>

      <!-- 输入提示 -->
      <div class="input-hint">
        <span>Ctrl + Enter 发送，Enter 换行</span>
        <span v-if="selectedFiles.length > 0" class="files-count">
          已选择 {{ selectedFiles.length }} 个文件
        </span>
      </div>
    </div>

    <!-- 隐藏的图片输入 -->
    <input
      ref="imageInputRef"
      type="file"
      multiple
      accept="image/*"
      style="display: none"
      @change="handleImageSelect"
    />

    <!-- 设置对话框 -->
    <el-dialog
      v-model="settingsVisible"
      title="对话设置"
      width="50%"
      @close="closeSettings"
    >
      <div class="settings-form">
        <el-form :model="settings" label-width="100px">
          <el-form-item label="流式响应">
            <el-switch v-model="settings.streamEnabled" />
          </el-form-item>
          <el-form-item label="温度">
            <el-slider
              v-model="settings.temperature"
              :min="0"
              :max="2"
              :step="0.1"
              show-stops
            />
          </el-form-item>
          <el-form-item label="最大令牌">
            <el-input-number
              v-model="settings.maxTokens"
              :min="100"
              :max="4000"
              :step="100"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="settingsVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import type { FileUploadResponse } from '@/types/chat'
import FileUpload from './FileUpload.vue'

interface Props {
  loading?: boolean
  chatId?: string
  placeholder?: string
  maxLength?: number
  showWordLimit?: boolean
  inputRows?: number
}

interface Emits {
  (e: 'send', message: string, files?: FileUploadResponse[]): void
  (e: 'settings-change', settings: ChatSettings): void
}

interface ChatSettings {
  streamEnabled: boolean
  temperature: number
  maxTokens: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  placeholder: '输入消息... (Ctrl+Enter 发送，Enter 换行)',
  maxLength: 4000,
  showWordLimit: false,
  inputRows: 3,
})

const emit = defineEmits<Emits>()

const message = ref('')
const selectedFiles = ref<FileUploadResponse[]>([])
const showFileUpload = ref(false)
const settingsVisible = ref(false)
const inputRef = ref<any>()
const imageInputRef = ref<HTMLInputElement>()
const activeReaders = ref<Set<FileReader>>(new Set())

const settings = ref<ChatSettings>({
  streamEnabled: true,
  temperature: 0.7,
  maxTokens: 2000,
})

const canSend = computed(() => {
  return (message.value.trim().length > 0 || selectedFiles.value.length > 0) && !props.loading
})

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault()
    if (canSend.value) {
      handleSend()
    }
  }
}

const handleInput = () => {
  if (inputRef.value) {
    const textarea = inputRef.value.$el.querySelector('textarea')
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
    }
  }
}

const handleSend = () => {
  if (!canSend.value) return

  const trimmedMessage = message.value.trim()
  if (!trimmedMessage && selectedFiles.value.length === 0) {
    ElMessage.warning('请输入消息或选择文件')
    return
  }

  emit('send', trimmedMessage || '（仅发送了文件）', selectedFiles.value)
  message.value = ''
  selectedFiles.value = []
  showFileUpload.value = false

  if (inputRef.value) {
    const textarea = inputRef.value.$el.querySelector('textarea')
    if (textarea) {
      textarea.style.height = 'auto'
    }
  }
}

const handleFilesUploaded = (files: FileUploadResponse[]) => {
  selectedFiles.value.push(...files)
  ElMessage.success(`成功上传 ${files.length} 个文件`)
}

const removeSelectedFile = (fileId: string) => {
  selectedFiles.value = selectedFiles.value.filter((f) => f.id !== fileId)
}

const toggleFileUpload = () => {
  showFileUpload.value = !showFileUpload.value
}

const uploadImage = () => {
  imageInputRef.value?.click()
}

const handleImageSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])

  if (files.length === 0) {
    target.value = ''
    return
  }

  files.forEach((file) => {
    const reader = new FileReader()
    activeReaders.value.add(reader)

    reader.onload = () => {
      if (!activeReaders.value.has(reader)) {
        return
      }
      const imageUpload: FileUploadResponse = {
        id: `img-${Date.now()}-${Math.random()}`,
        name: file.name,
        size: file.size,
        type: file.type,
        url: reader.result as string,
        uploadedAt: new Date().toISOString(),
      }
      selectedFiles.value.push(imageUpload)
      activeReaders.value.delete(reader)
    }
    reader.onerror = () => {
      console.error('Failed to read file:', file.name, reader.error)
      ElMessage.error(`读取图片失败: ${file.name}`)
      activeReaders.value.delete(reader)
    }
    reader.readAsDataURL(file)
  })

  target.value = ''
}

const openSettings = () => {
  settingsVisible.value = true
}

const closeSettings = () => {
  settingsVisible.value = false
}

const saveSettings = () => {
  emit('settings-change', settings.value)
  settingsVisible.value = false
  ElMessage.success('设置已保存')
}

onBeforeUnmount(() => {
  activeReaders.value.forEach(reader => {
    reader.abort?.()
  })
  activeReaders.value.clear()
})
</script>
<style scoped lang="scss">
.message-input-wrapper {
  padding: 16px 24px;
  background: #fff;
  border-top: none;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  gap: 12px;

  .upload-section {
    padding: 12px;
    background: #f5f7fa;
    border-radius: 8px;
    border: 1px solid #e4e7eb;
  }

  .selected-files {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;

    .selected-file-item {
      .el-tag {
        max-width: 200px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }

  .input-container {
    .el-textarea {
      :deep(.el-textarea__inner) {
        border-radius: 12px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 14px;
        resize: none;
        max-height: 200px;
        overflow-y: auto;
        padding: 12px 16px;
        background: #f5f7fa;
        border: 1px solid transparent;
        transition: all 0.2s;

        &:hover {
          border-color: #ddd;
        }

        &:focus {
          border-color: #0d9668;
          background: #fff;
          box-shadow: 0 0 0 2px rgba(13, 150, 104, 0.1);
        }
      }
    }

    .input-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 12px;
      gap: 12px;

      .left-actions,
      .right-actions {
        display: flex;
        gap: 8px;
        align-items: center;
      }

      .left-actions {
        flex: 1;

        .el-button {
          margin: 0;
          color: #999;
          &:hover {
            color: #0d9668;
          }
        }
      }

      .right-actions {
        .el-button {
          margin: 0;
          min-width: 80px;
          border-radius: 8px;
        }

        :deep(.el-button--primary) {
          background-color: #0d9668;
          border-color: #0d9668;

          &:hover {
            background-color: #0ba85e;
            border-color: #0ba85e;
          }
        }
      }
    }

    .input-hint {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 6px;
      font-size: 12px;
      color: #bbb;

      .files-count {
        color: #0d9668;
        font-weight: 500;
      }
    }
  }

  .settings-form {
    padding: 0 12px;

    .el-form-item {
      margin-bottom: 20px;
    }
  }
}

@media (max-width: 768px) {
  .message-input-wrapper {
    padding: 12px;

    .input-container {
      :deep(.el-textarea__inner) {
        font-size: 13px;
      }

      .input-footer {
        flex-wrap: wrap;

        .left-actions {
          width: 100%;
          justify-content: flex-start;
        }

        .right-actions {
          width: 100%;
          justify-content: flex-end;
        }
      }
    }
  }
}
</style>

