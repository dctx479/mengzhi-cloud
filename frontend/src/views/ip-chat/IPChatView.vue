<template>
  <div class="ip-chat-page">
    <el-card class="ip-header" shadow="never">
      <div class="ip-header-top">
        <div class="title-section">
          <h2 class="ip-title">🎭 IP 智能对话</h2>
          <el-tag size="small" type="success">草原文化特色 AI</el-tag>
        </div>
        <div class="control-section">
          <el-radio-group v-model="selectedIP" size="default" class="ip-selector">
            <el-radio-button label="auto">
              <el-icon><Connection /></el-icon>
              <span>自动路由</span>
            </el-radio-button>
            <el-radio-button label="xiaoshu">
              <el-icon><Cherry /></el-icon>
              <span>{{ ipInfo?.xiaoshu.name || '小数' }}</span>
            </el-radio-button>
            <el-radio-button label="xiaoshang">
              <el-icon><ShoppingCart /></el-icon>
              <span>{{ ipInfo?.xiaoshang.name || '小商' }}</span>
            </el-radio-button>
          </el-radio-group>
          <el-button
            v-if="messages.length > 0"
            size="small"
            @click="handleNewConversation"
            :disabled="streaming"
          >
            <el-icon><Plus /></el-icon>
            新对话
          </el-button>
        </div>
      </div>
      <div v-if="ipInfo" class="ip-personas">
        <div class="persona-card" :class="{ active: selectedIP === 'xiaoshu' }">
          <div class="persona-header">
            <el-icon class="persona-icon"><Cherry /></el-icon>
            <strong>{{ ipInfo.xiaoshu.name }}</strong>
          </div>
          <p class="persona-desc">{{ ipInfo.xiaoshu.description }}</p>
          <div class="persona-tags">
            <el-tag size="small" effect="plain">{{ ipInfo.xiaoshu.focus }}</el-tag>
          </div>
        </div>
        <div class="persona-card" :class="{ active: selectedIP === 'xiaoshang' }">
          <div class="persona-header">
            <el-icon class="persona-icon"><ShoppingCart /></el-icon>
            <strong>{{ ipInfo.xiaoshang.name }}</strong>
          </div>
          <p class="persona-desc">{{ ipInfo.xiaoshang.description }}</p>
          <div class="persona-tags">
            <el-tag size="small" effect="plain" type="warning">{{ ipInfo.xiaoshang.focus }}</el-tag>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="ip-body" shadow="never">
      <el-scrollbar ref="scrollbarRef" class="message-area">
        <div v-if="messages.length === 0" class="empty-state">
          <el-empty description="">
            <template #image>
              <el-icon :size="80" color="#0d9668"><ChatDotRound /></el-icon>
            </template>
            <template #description>
              <div class="empty-desc">
                <h3>开始与 AI IP 智能体对话</h3>
                <p>小数会带你了解草原文化与产品故事</p>
                <p>小商会为你提供营销策略与品牌建议</p>
              </div>
            </template>
          </el-empty>
          <div class="quick-questions">
            <p class="quick-title">💡 试试这些问题：</p>
            <div class="question-chips">
              <el-tag
                v-for="(q, i) in quickQuestions"
                :key="i"
                class="question-chip"
                size="large"
                @click="handleQuickQuestion(q)"
              >
                {{ q }}
              </el-tag>
            </div>
          </div>
        </div>
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="message-row"
          :class="msg.role"
        >
          <div v-if="msg.role === 'assistant'" class="avatar-box">
            <el-avatar :size="36" class="message-avatar">
              <el-icon><component :is="msg.ipName === '小数' ? Cherry : ShoppingCart" /></el-icon>
            </el-avatar>
          </div>
          <div class="message-bubble">
            <div v-if="msg.role === 'assistant' && msg.ipName" class="message-label">
              {{ msg.ipName }}
              <el-tag v-if="msg.culturalElements && msg.culturalElements.length > 0" size="small" type="success" effect="plain">
                文化元素 {{ msg.culturalElements.length }}
              </el-tag>
            </div>
            <div class="message-content" v-html="formatMessage(msg.content)"></div>
            <div v-if="msg.culturalElements && msg.culturalElements.length > 0" class="cultural-tags">
              <el-icon><CollectionTag /></el-icon>
              <span>文化关联：</span>
              <el-tag
                v-for="elem in msg.culturalElements"
                :key="elem"
                size="small"
                type="info"
                effect="light"
              >
                {{ elem }}
              </el-tag>
            </div>
            <div v-if="msg.role === 'assistant'" class="message-actions">
              <el-button text size="small" @click="handleCopy(msg.content)">
                <el-icon><DocumentCopy /></el-icon>
                复制
              </el-button>
            </div>
          </div>
          <div v-if="msg.role === 'user'" class="avatar-box">
            <el-avatar :size="36" class="message-avatar user-avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
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
          :disabled="streaming"
          @keydown.enter="handleKeydown"
        >
          <template #suffix>
            <el-tooltip content="清空输入" placement="top" v-if="inputText">
              <el-icon class="clear-icon" @click="inputText = ''"><CircleClose /></el-icon>
            </el-tooltip>
          </template>
        </el-input>
        <el-button
          type="primary"
          :loading="streaming"
          :disabled="!inputText.trim() || streaming"
          @click="handleSend"
          size="large"
        >
          <el-icon v-if="!streaming"><Promotion /></el-icon>
          <span>{{ streaming ? '发送中...' : '发送' }}</span>
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Promotion,
  Connection,
  Cherry,
  ShoppingCart,
  Plus,
  ChatDotRound,
  User,
  DocumentCopy,
  CircleClose,
  CollectionTag,
} from '@element-plus/icons-vue'
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
  culturalElements?: string[]
}

const ipInfo = ref<IPListResponse>()
const selectedIP = ref<'auto' | IPType>('auto')
const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const streaming = ref(false)
const conversationId = ref<number>()
const scrollbarRef = ref<ScrollbarInstance>()

const quickQuestions = [
  '推荐一款内蒙古特色羊肉产品',
  '如何讲好草原奶制品的品牌故事',
  '这款产品适合什么样的营销文案',
  '介绍一下蒙古族传统饮食文化',
]

const scrollToBottom = async () => {
  await nextTick()
  scrollbarRef.value?.setScrollTop(999999)
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.shiftKey) return
  e.preventDefault()
  handleSend()
}

const formatMessage = (content: string): string => {
  // 简单的 Markdown 渲染：换行、加粗
  return content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
}

const handleCopy = (text: string) => {
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const handleQuickQuestion = (question: string) => {
  inputText.value = question
  handleSend()
}

const handleNewConversation = () => {
  messages.value = []
  conversationId.value = undefined
  inputText.value = ''
  ElMessage.success('已开始新对话')
}

const handleSend = async () => {
  const content = inputText.value.trim()
  if (!content || streaming.value) return

  messages.value.push({ role: 'user', content })
  const assistant: ChatMessage = { role: 'assistant', content: '', culturalElements: [] }
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
          if (chunk.cultural_elements && chunk.cultural_elements.length > 0) {
            assistant.culturalElements = chunk.cultural_elements
          }
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

.title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ip-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
}

.control-section {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.ip-selector :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 4px;
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
  padding: 14px 16px;
  border-radius: 12px;
  background: #f7f8fa;
  border: 2px solid #eee;
  transition: all 0.3s;
  cursor: pointer;
}

.persona-card:hover {
  border-color: #0d9668;
  box-shadow: 0 2px 8px rgba(13, 150, 104, 0.1);
}

.persona-card.active {
  background: #e6f7f0;
  border-color: #0d9668;
}

.persona-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.persona-icon {
  font-size: 20px;
  color: #0d9668;
}

.persona-card strong {
  font-size: 16px;
  color: #0d9668;
}

.persona-desc {
  margin: 8px 0;
  font-size: 13px;
  color: #555;
  line-height: 1.6;
}

.persona-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
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
  padding: 16px;
}

.message-area {
  flex: 1;
  padding-right: 8px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 24px;
}

.empty-desc h3 {
  margin: 12px 0 8px;
  font-size: 18px;
  color: #1a1a1a;
}

.empty-desc p {
  margin: 4px 0;
  font-size: 14px;
  color: #666;
}

.quick-questions {
  width: 100%;
  max-width: 600px;
  text-align: center;
}

.quick-title {
  font-size: 14px;
  font-weight: 600;
  color: #666;
  margin-bottom: 12px;
}

.question-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.question-chip {
  cursor: pointer;
  transition: all 0.3s;
  padding: 8px 16px;
}

.question-chip:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(13, 150, 104, 0.2);
}

.message-row {
  display: flex;
  margin-bottom: 16px;
  gap: 10px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.avatar-box {
  flex-shrink: 0;
}

.message-avatar {
  background: linear-gradient(135deg, #0d9668 0%, #0c8257 100%);
  color: white;
}

.user-avatar {
  background: linear-gradient(135deg, #409eff 0%, #3a8ee6 100%);
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.7;
  word-break: break-word;
  position: relative;
}

.message-row.user .message-bubble {
  background: linear-gradient(135deg, #0d9668 0%, #0c8257 100%);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-row.assistant .message-bubble {
  background: #fff;
  color: #1a1a1a;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.message-label {
  font-size: 12px;
  font-weight: 600;
  color: #0d9668;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.message-content {
  white-space: pre-wrap;
}

.message-content :deep(strong) {
  font-weight: 600;
}

.message-content :deep(em) {
  font-style: italic;
  color: #666;
}

.cultural-tags {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 12px;
  color: #666;
}

.message-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.input-area {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.input-area :deep(.el-textarea__inner) {
  font-size: 14px;
  line-height: 1.6;
}

.clear-icon {
  cursor: pointer;
  color: #999;
  transition: color 0.3s;
}

.clear-icon:hover {
  color: #0d9668;
}

.input-area .el-button {
  height: 56px;
  padding: 0 24px;
  font-size: 15px;
}

@media (max-width: 768px) {
  .ip-chat-page {
    padding: 12px;
  }

  .ip-header-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .message-bubble {
    max-width: 85%;
  }
}
</style>
