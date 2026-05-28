<template>
  <div class="file-upload-container">
    <!-- 上传区域 -->
    <el-upload
      :action="uploadAction"
      :before-upload="beforeUpload"
      :on-success="handleUploadSuccess"
      :on-error="handleUploadError"
      :multiple="multiple"
      :auto-upload="false"
      :drag="drag"
      :show-file-list="false"
      :accept="acceptTypes"
    >
      <template #default>
        <div v-if="drag" class="upload-area">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">点击或拖拽上传文件</div>
          <div class="upload-hint">支持图片、文档、表格，点击可编辑</div>
        </div>
        <el-button v-else type="primary" size="small" icon="UploadFilled">
          {{ buttonText }}
        </el-button>
      </template>
    </el-upload>

    <!-- 已上传文件列表 -->
    <div v-if="uploadedFiles.length > 0" class="uploaded-files">
      <div class="files-header">
        <span class="files-title">已上传文件 ({{ uploadedFiles.length }})</span>
        <el-button
          v-if="uploadedFiles.length > 0"
          type="danger"
          text
          size="small"
          @click="clearAllFiles"
        >
          清空
        </el-button>
      </div>

      <div class="files-list">
        <div v-for="file in uploadedFiles" :key="file.id" class="file-item">
          <!-- 文件预览 -->
          <div v-if="isImage(file.type)" class="file-preview image-preview">
            <img :src="file.url" :alt="file.name" />
            <div class="image-overlay">
              <el-button
                type="primary"
                text
                size="small"
                icon="ZoomIn"
                @click="previewImage(file)"
              />
              <el-button
                type="danger"
                text
                size="small"
                icon="Delete"
                @click="removeFile(file.id)"
              />
            </div>
          </div>

          <!-- 文件图标 -->
          <div v-else class="file-preview file-icon">
            <el-icon :size="32">
              <component :is="getFileIcon(file.type)" />
            </el-icon>
          </div>

          <!-- 文件信息 -->
          <div class="file-info">
            <div class="file-name" :title="file.name">{{ file.name }}</div>
            <div class="file-meta">
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
              <span class="file-time">{{ formatTime(file.uploadedAt) }}</span>
            </div>
          </div>

          <!-- 删除按钮 -->
          <el-button
            v-if="!isImage(file.type)"
            type="danger"
            text
            size="small"
            icon="Delete"
            @click="removeFile(file.id)"
          />
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
        class="preview-image"
      />
      <div class="preview-info">{{ previewingImage?.name }}</div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import type { FileUploadResponse } from '@/types/chat'

interface Props {
  chatId?: string
  uploadAction?: string
  multiple?: boolean
  drag?: boolean
  buttonText?: string
  maxFileSize?: number
  allowedTypes?: string[]
}

interface Emits {
  (e: 'files-uploaded', files: FileUploadResponse[]): void
}

const props = withDefaults(defineProps<Props>(), {
  uploadAction: '/api/v1/media/upload',
  multiple: true,
  drag: true,
  buttonText: '上传文件',
  maxFileSize: 20 * 1024 * 1024, // 20MB
  allowedTypes: () => [
    'image/jpeg',
    'image/png',
    'image/webp',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
  ],
})

const emit = defineEmits<Emits>()

const uploadedFiles = ref<FileUploadResponse[]>([])
const imagePreviewVisible = ref(false)
const previewingImage = ref<FileUploadResponse | null>(null)

const acceptTypes = computed(() => {
  const typeMap: Record<string, string> = {
    'image/jpeg': '.jpg,.jpeg',
    'image/png': '.png',
    'image/webp': '.webp',
    'application/pdf': '.pdf',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/plain': '.txt',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'text/csv': '.csv',
  }
  return props.allowedTypes.map((type) => typeMap[type] || '').join(',')
})

const isImage = (fileType: string): boolean => {
  return fileType.startsWith('image/')
}

const getFileIcon = (fileType: string) => {
  if (fileType.startsWith('image/')) return 'Picture'
  if (fileType === 'application/pdf') return 'Document'
  if (fileType.includes('word') || fileType.includes('document')) return 'Document'
  if (fileType.includes('sheet') || fileType.includes('excel') || fileType === 'text/csv')
    return 'Table'
  if (fileType.includes('zip') || fileType.includes('compressed')) return 'FileZip'
  return 'DocumentCopy'
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatTime = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const beforeUpload = (file: File): boolean => {
  // 检查文件大小
  if (file.size > props.maxFileSize) {
    ElMessage.error(`文件大小不能超过 ${formatFileSize(props.maxFileSize)}`)
    return false
  }

  // 检查文件类型
  if (!props.allowedTypes.includes(file.type)) {
    ElMessage.error(
      `不支持此文件类型。支持的类型：${props.allowedTypes.join(', ')}`
    )
    return false
  }

  return true
}

const handleUploadSuccess = (response: FileUploadResponse) => {
  uploadedFiles.value.push(response)
  ElMessage.success('文件上传成功')
  emit('files-uploaded', [response])
}

const handleUploadError = (error: any) => {
  ElMessage.error('文件上传失败')
  console.error('Upload error:', error)
}

const removeFile = (fileId: string) => {
  uploadedFiles.value = uploadedFiles.value.filter((f) => f.id !== fileId)
}

const clearAllFiles = () => {
  uploadedFiles.value = []
  ElMessage.success('已清空所有文件')
}

const previewImage = (file: FileUploadResponse) => {
  previewingImage.value = file
  imagePreviewVisible.value = true
}

const getUploadedFiles = (): FileUploadResponse[] => {
  return uploadedFiles.value
}

const clearFiles = () => {
  uploadedFiles.value = []
}

// 暴露方法给父组件
defineExpose({
  getUploadedFiles,
  clearFiles,
})
</script>

<style scoped lang="scss">
.file-upload-container {
  width: 100%;

  .upload-area {
    padding: 40px 20px;
    text-align: center;
    background: #fafafa;
    border: 2px dashed #dcdfe6;
    border-radius: 6px;
    transition: all 0.3s;
    cursor: pointer;

    &:hover {
      border-color: $color-primary;
      background: #f5f7fa;
    }

    .upload-icon {
      font-size: 48px;
      color: $color-primary;
      margin-bottom: 8px;
    }

    .upload-text {
      font-size: 14px;
      color: #333;
      margin-bottom: 4px;
      font-weight: 500;
    }

    .upload-hint {
      font-size: 12px;
      color: #999;
    }
  }

  .uploaded-files {
    margin-top: 16px;
    padding: 12px;
    background: #f5f7fa;
    border-radius: 6px;

    .files-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid #dcdfe6;

      .files-title {
        font-size: 14px;
        font-weight: 500;
        color: #333;
      }
    }

    .files-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-height: 300px;
      overflow-y: auto;

      .file-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px;
        background: white;
        border-radius: 4px;
        transition: all 0.3s;

        &:hover {
          background: #f0f2f5;
        }

        .file-preview {
          flex-shrink: 0;
          width: 60px;
          height: 60px;
          border-radius: 4px;
          overflow: hidden;
          background: #f5f7fa;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;

          &.image-preview {
            padding: 0;

            img {
              width: 100%;
              height: 100%;
              object-fit: cover;
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
              gap: 8px;
              opacity: 0;
              transition: opacity 0.3s;

              &:hover {
                opacity: 1;
              }
            }
          }

          &.file-icon {
            color: $color-primary;
          }
        }

        .file-info {
          flex: 1;
          min-width: 0;

          .file-name {
            font-size: 13px;
            color: #333;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 4px;
          }

          .file-meta {
            display: flex;
            gap: 12px;
            font-size: 12px;
            color: #999;

            .file-size,
            .file-time {
              white-space: nowrap;
            }
          }
        }
      }
    }
  }

  .preview-image {
    width: 100%;
    height: auto;
    max-height: 70vh;
    border-radius: 4px;
  }

  .preview-info {
    margin-top: 12px;
    font-size: 12px;
    color: #999;
    text-align: center;
  }
}

@media (max-width: 768px) {
  .file-upload-container {
    .upload-area {
      padding: 20px 10px;

      .upload-icon {
        font-size: 32px;
      }

      .upload-text {
        font-size: 12px;
      }
    }

    .uploaded-files {
      .files-list {
        .file-item {
          flex-wrap: wrap;

          .file-info {
            flex: 1 0 100%;
          }
        }
      }
    }
  }
}
</style>
