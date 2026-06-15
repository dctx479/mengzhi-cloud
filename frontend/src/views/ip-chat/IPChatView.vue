<template>
  <div class="ip-chat-page">
    <el-card class="ip-header" shadow="never">
      <div class="ip-header-top">
        <h2 class="ip-title">IP 智能对话</h2>
        <el-radio-group v-model="selectedIP" size="default">
          <el-radio-button label="auto">自动路由</el-radio-button>
          <el-radio-button label="xiaoshu">{{ ipInfo?.xiaoshu.name || '小数' }}</el-radio-button>
          <el-radio-button label="xiaoshang">{{ ipInfo?.xiaoshang.name || '小商' }}</el-radio-button>
        </el-radio-group>
      </div>
      <div v-if="ipInfo" class="ip-personas">
        <div class="persona-card">
          <strong>{{ ipInfo.xiaoshu.name }}</strong>
          <p class="persona-desc">{{ ipInfo.xiaoshu.description }}</p>
          <span class="persona-focus">{{ ipInfo.xiaoshu.focus }}</span>
        </div>
        <div class="persona-card">
          <strong>{{ ipInfo.xiaoshang.name }}</strong>
          <p class="persona-desc">{{ ipInfo.xiaoshang.description }}</p>
          <span class="persona-focus">{{ ipInfo.xiaoshang.focus }}</span>
        </div>
      </div>
    </el-card>

    <el-card class="ip-body" shadow="never">
      <el-scrollbar ref="scrollbarRef" class="message-area">
        <el-empty v-if="messages.length === 0" description="开始与小数 / 小商对话" />
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="message-row"
          :class="msg.role"
        >
          <div class="message-bubble">
            <div v-if="msg.role === 'assistant' && msg.ipName" class="message-label">{{ msg.ipName }}</div>
            <div class="message-content">{{ msg.content }}</div>
          </div>
        </div>
      </el-scrollbar>

      <div class="input-area">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          :autosize="{ minRows: 2, maxRows: 5 }"
          placeholder="输入消息，Enter 发送，Shift+Enter 换行"
          resize="none"
          @keydown.enter="handleKeydown"
        />
        <el-button
          type="primary"
          :loading="streaming"
          :disabled="streaming"
          @click="handleSend"
        >
          <el-icon v-if="!streaming"><Promotion /></el-icon>
          <span>发送</span>
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'
import type { ScrollbarInstance } from 'element-plus'
import {
  getIPInfo,
  sendIPMessageStream,
  type IPListResponse,
  type IPType,
  type IPStreamChunk,
} from '@/api/ipChat'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  ipName?: string
}

const ipInfo = ref<IPListResponse>()
const selectedIP = ref<'auto' | IPType>('auto')
const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const streaming = ref(false)
const conversationId = ref<number>()
const scrollbarRef = ref<ScrollbarInstance>()

const scrollToBottom = async () => {
  await nextTick()
  scrollbarRef.value?.setScrollTop(999999)
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.shiftKey) return
  e.preventDefault()
  handleSend()
}

const handleSend = async () => {
  const content = inputText.value.trim()
  if (!content || streaming.value) return

  messages.value.push({ role: 'user', content })
  const assistant: ChatMessage = { role: 'assistant', content: '' }
  messages.value.push(assistant)
  inputText.value = ''
  streaming.value = true
  await scrollToBottom()

  const ipType = selectedIP.value === 'auto' ? undefined : selectedIP.value

  try {
    await sendIPMessageStream(
      {
        content,
        conversation_id: conversationId.value,
        ip_type: ipType,
        temperature: 0.7,
      },
      (chunk: IPStreamChunk) => {
        if (chunk.type === 'chunk') {
          assistant.content += chunk.content
          scrollToBottom()
        } else if (chunk.type === 'done') {
          if (chunk.ip_name) assistant.ipName = chunk.ip_name
        } else if (chunk.type === 'error') {
          ElMessage.error(chunk.message)
        }
      },
      (error: Error) => {
        ElMessage.error(error.message || '发送失败')
      }
    )
  } catch {
    // onError 已处理提示
  } finally {
    streaming.value = false
    await scrollToBottom()
  }
}

onMounted(async () => {
  try {
    ipInfo.value = await getIPInfo()
  } catch {
    ElMessage.error('加载 IP 人格信息失败')
  }
})
</script>

<style scoped>
.ip-chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 84px);
  padding: 16px;
  gap: 16px;
  box-sizing: border-box;
  background: #f0f2f5;
}

.ip-header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.ip-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #1a1a1a;
}

.ip-personas {
  display: flex;
  gap: 16px;
  margin-top: 14px;
  flex-wrap: wrap;
}

.persona-card {
  flex: 1;
  min-width: 200px;
  padding: 12px 14px;
  border-radius: 10px;
  background: #f7f8fa;
  border: 1px solid #eee;
}

.persona-card strong {
  font-size: 15px;
  color: #0d9668;
}

.persona-desc {
  margin: 6px 0;
  font-size: 13px;
  color: #555;
  line-height: 1.5;
}

.persona-focus {
  font-size: 12px;
  color: #999;
}

.ip-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ip-body :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.message-area {
  flex: 1;
  padding-right: 8px;
}

.message-row {
  display: flex;
  margin-bottom: 14px;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.message-row.user .message-bubble {
  background: #0d9668;
  color: #fff;
  border-bottom-right-radius: 2px;
}

.message-row.assistant .message-bubble {
  background: #f0f2f5;
  color: #1a1a1a;
  border-bottom-left-radius: 2px;
}

.message-label {
  font-size: 12px;
  font-weight: 600;
  color: #0d9668;
  margin-bottom: 4px;
}

.input-area {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.input-area .el-button {
  height: 56px;
}
</style>
