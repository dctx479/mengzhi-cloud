<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  sendChat,
  sendChatStream,
  getSessions,
  createSession,
  getSession,
  deleteSession,
  getTickets,
  createTicket,
  getUserProfile,
  distillSession,
  recordCorrection,
  type KefuChatRequest,
  type KefuChatResponse,
  type KefuSession,
  type KefuTicket,
  type KefuTicketMessage,
  type UserProfile,
} from '@/api/kefu'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// ============================================================
// State
// ============================================================
const sessions = ref<KefuSession[]>([])
const currentSessionId = ref<string | null>(null)
const currentSessionMessages = ref<Array<{
  id: string
  role: 'user' | 'agent'
  content: string
  emotion?: string
  intent?: string
  ticketId?: string
  action?: string
}>>([])
const inputMessage = ref('')
const loading = ref(false)
const streaming = ref(false)
const streamedReply = ref('')

// 情绪配置
const emotionMap: Record<string, { label: string; color: string }> = {
  positive: { label: '😊 满意', color: '#67c23a' },
  neutral: { label: '😐 中性', color: '#909399' },
  confused: { label: '🤔 疑惑', color: '#e6a23c' },
  frustrated: { label: '😤 烦躁', color: '#f56c6c' },
  angry: { label: '😡 愤怒', color: '#f56c6c' },
  anxious: { label: '😰 着急', color: '#e6a23c' },
  sad: { label: '😢 难过', color: '#909399' },
}

const intentLabelMap: Record<string, string> = {
  greeting: '问候',
  product_inquiry: '产品咨询',
  price_inquiry: '价格咨询',
  refund: '退款',
  return: '退货',
  exchange: '换货',
  warranty: '保修',
  delivery: '配送',
  tracking: '物流查询',
  complaint: '投诉',
  escalation: '转人工',
  order_inquiry: '订单查询',
  quality_feedback: '质量反馈',
  brand_story: '品牌故事',
  unknown: '其他',
}

// ============================================================
// Methods
// ============================================================
async function loadSessions() {
  try {
    const data = await getSessions(50)
    sessions.value = data.sessions || []
  } catch (e) {
    console.error('加载会话列表失败', e)
    ElMessage.error('加载客服会话失败')
  }
}

const userProfile = ref<UserProfile | null>(null)

async function loadProfile() {
  if (!userStore.isLoggedIn) return
  try {
    userProfile.value = await getUserProfile()
  } catch {
    // ignore - profile is optional
  }
}

async function startNewSession() {
  try {
    const data = await createSession()
    const newId = data.session_id
    currentSessionId.value = newId
    currentSessionMessages.value = []
    sessions.value.unshift({
      id: 0, session_id: newId, user_id: 0, status: 'active',
      title: '新会话', user_name: userStore.user?.username || '',
      message_count: 0, created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
  } catch (e) {
    ElMessage.error('创建会话失败')
  }
}

async function selectSession(session: KefuSession) {
  currentSessionId.value = session.session_id
  try {
    const data = await getSession(session.session_id)
    const msgs = data.messages || []
    currentSessionMessages.value = msgs.map((m: KefuTicketMessage, i: number) => ({
      id: `${session.session_id}-${i}`,
      role: m.role as 'user' | 'agent',
      content: m.content,
      emotion: m.emotion,
      intent: m.intent,
    }))
  } catch {
    currentSessionMessages.value = []
  }
}

async function handleSendMessage() {
  if (!inputMessage.value.trim()) return
  if (!currentSessionId.value) {
    await startNewSession()
  }

  const message = inputMessage.value.trim()
  const sessionId = currentSessionId.value!
  inputMessage.value = ''

  // 添加用户消息到列表
  const userMsgId = `${sessionId}-${Date.now()}`
  currentSessionMessages.value.push({ id: userMsgId, role: 'user', content: message })
  scrollToBottom()

  const request: KefuChatRequest = { session_id: sessionId, message }

  // 非流式
  loading.value = true
  try {
    const result = await sendChat(request)
    appendAgentMessage(result)
  } catch (e: unknown) {
    const err = e as { message?: string }
    ElMessage.error(err.message || '发送失败')
  } finally {
    loading.value = false
  }
}

async function handleSendMessageStream() {
  if (!inputMessage.value.trim()) return
  if (!currentSessionId.value) {
    await startNewSession()
  }

  const message = inputMessage.value.trim()
  const sessionId = currentSessionId.value!
  inputMessage.value = ''

  const userMsgId = `${sessionId}-${Date.now()}`
  currentSessionMessages.value.push({ id: userMsgId, role: 'user', content: message })
  scrollToBottom()

  streaming.value = true
  streamedReply.value = ''
  const agentMsgId = `${sessionId}-${Date.now()}-agent`
  const agentMsgIndex = currentSessionMessages.value.push({
    id: agentMsgId, role: 'agent', content: '',
  }) - 1

  try {
    const request: KefuChatRequest = { session_id: sessionId, message }
    await sendChatStream(
      request,
      (chunk) => {
        streamedReply.value += chunk
        currentSessionMessages.value[agentMsgIndex].content = streamedReply.value
        scrollToBottom()
      },
      (meta) => {
        // 路由元数据
        Object.assign(currentSessionMessages.value[agentMsgIndex], {
          emotion: meta.emotion as string,
          intent: meta.intent as string,
          action: meta.action as string,
          ticketId: meta.ticket_id as string | undefined,
        })
      },
      () => {
        streaming.value = false
      }
    )
  } catch (e: unknown) {
    const err = e as { message?: string }
    ElMessage.error(err.message || '发送失败')
    streaming.value = false
  }
}

function appendAgentMessage(result: KefuChatResponse) {
  const sessionId = result.session_id || currentSessionId.value || ''
  currentSessionMessages.value.push({
    id: `${sessionId}-${Date.now()}-agent`,
    role: 'agent',
    content: result.reply,
    emotion: result.emotion,
    intent: result.intent,
    ticketId: result.ticket_id,
    action: result.action,
  })
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    const el = document.querySelector('.message-list')
    if (el) el.scrollTop = el.scrollHeight
  })
}

// 纠正机制
const correctionDialogVisible = ref(false)
const correctionTarget = ref<{ intent?: string; content?: string }>({})
const correctionForm = ref({ type: 'answer' as 'emotion' | 'intent' | 'answer' | 'profile', corrected: '' })

function openCorrectionDialog(msg: { intent?: string; content: string }) {
  correctionTarget.value = msg
  correctionForm.value = { type: 'answer', corrected: '' }
  correctionDialogVisible.value = true
}

async function submitCorrection() {
  if (!currentSessionId.value || !correctionForm.value.corrected.trim()) return
  try {
    await recordCorrection({
      session_id: currentSessionId.value,
      correction_type: correctionForm.value.type,
      original: correctionTarget.value.content || '',
      corrected: correctionForm.value.corrected.trim(),
    })
    ElMessage.success('已记录您的反馈')
    correctionDialogVisible.value = false
  } catch {
    ElMessage.error('反馈提交失败')
  }
}

// ============================================================
// Lifecycle
// ============================================================
onMounted(() => {
  loadSessions()
  loadProfile()
})

const messages = computed(() => currentSessionMessages.value)
</script>

<template>
  <div class="kefu-chat-page">
    <!-- 左侧会话列表 -->
    <div class="sidebar-panel">
      <div class="sidebar-header">
        <span>客服会话</span>
        <el-button type="primary" size="small" @click="startNewSession">+ 新会话</el-button>
      </div>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.session_id"
          class="session-item"
          :class="{ active: s.session_id === currentSessionId }"
          @click="selectSession(s)"
        >
          <div class="session-title">{{ s.title || '新会话' }}</div>
          <div class="session-meta">
            <span v-if="s.emotion_type" :style="{ color: emotionMap[s.emotion_type]?.color }">
              {{ emotionMap[s.emotion_type]?.label }}
            </span>
            <span class="msg-count">{{ s.message_count }}条消息</span>
          </div>
        </div>
        <el-empty v-if="sessions.length === 0" description="暂无会话" />
      </div>
    </div>

    <!-- 右侧对话区 -->
    <div class="chat-panel">
      <!-- 消息列表 -->
      <div class="message-list">
        <div v-if="messages.length === 0" class="empty-chat">
          <!-- 用户画像标签（已登录用户显示） -->
          <div v-if="userProfile" class="profile-badge">
            <el-tag size="small" :type="(userProfile.engagement_score?.score ?? 0) >= 60 ? 'success' : 'info'">
              {{ userProfile.engagement_score?.level || '普通用户' }}
            </el-tag>
            <el-tag size="small" type="warning">
              {{ userProfile.layer_1_purchase?.recency || '未知' }}
            </el-tag>
            <el-tag v-if="userProfile.layer_3_emotion?.dominant_emotion && userProfile.layer_3_emotion.dominant_emotion !== 'neutral'"
              size="small" :type="userProfile.layer_3_emotion.negative_ratio > 0.3 ? 'danger' : 'info'">
              {{ emotionMap[userProfile.layer_3_emotion.dominant_emotion]?.label || userProfile.layer_3_emotion.dominant_emotion }}
            </el-tag>
            <span class="profile-orders">{{ userProfile.layer_1_purchase?.total_orders || 0 }} 笔订单</span>
          </div>
          <div class="welcome-card">
            <h3>您好！我是内蒙古农畜产品平台的智能客服</h3>
            <p>我可以帮您：</p>
            <ul>
              <li>产品咨询（牛羊肉、奶制品、藜麦等）</li>
              <li>查询订单状态和物流信息</li>
              <li>了解配送政策和退换货流程</li>
              <li>处理投诉和转人工服务</li>
            </ul>
            <p class="tips">试试问我："你们有哪些产品？" 或 "怎么退货？"</p>
          </div>
        </div>

        <div
          v-for="msg in messages"
          :key="msg.id"
          class="message-item"
          :class="msg.role"
        >
          <div class="message-avatar">
            <el-avatar :icon="msg.role === 'user' ? 'User' : 'ChatDotRound'" size="small" />
          </div>
          <div class="message-body">
            <div class="message-tags" v-if="msg.role === 'agent'">
              <el-tag v-if="msg.emotion" size="small" :type="msg.emotion === 'positive' ? 'success' : 'warning'">
                {{ emotionMap[msg.emotion]?.label || msg.emotion }}
              </el-tag>
              <el-tag v-if="msg.intent" size="small" type="info">
                {{ intentLabelMap[msg.intent] || msg.intent }}
              </el-tag>
              <el-tag v-if="msg.ticketId" size="small" type="success">
                工单 #{{ msg.ticketId?.slice(0, 8) }}
              </el-tag>
            </div>
            <div class="message-content"><template v-for="(line, idx) in msg.content.split('\n')" :key="idx"><br v-if="idx > 0" />{{ line }}</template></div>
            <div class="message-feedback" v-if="msg.role === 'agent' && !loading && !streaming">
              <el-button link size="small" @click="openCorrectionDialog(msg)">
                回答不准？反馈
              </el-button>
            </div>
          </div>
        </div>

        <div v-if="loading || streaming" class="message-item agent">
          <div class="message-avatar">
            <el-avatar icon="ChatDotRound" size="small" />
          </div>
          <div class="message-body">
            <div class="message-content typing">
              <span v-if="streaming">{{ streamedReply }}</span>
              <span v-else>思考中...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          placeholder="输入您的问题，按 Enter 发送..."
          :disabled="loading"
          @keydown.enter.exact.prevent="handleSendMessage"
        />
        <div class="input-actions">
          <el-button @click="handleSendMessage" :loading="loading" :disabled="!inputMessage.trim()">
            发送
          </el-button>
          <el-button @click="handleSendMessageStream" :disabled="loading || !inputMessage.trim()">
            流式发送
          </el-button>
        </div>
      </div>
    </div>

    <!-- 纠正反馈对话框 -->
    <el-dialog v-model="correctionDialogVisible" title="反馈纠正" width="400px">
      <el-form label-position="top">
        <el-form-item label="纠正类型">
          <el-select v-model="correctionForm.type" style="width: 100%">
            <el-option label="回答内容不准确" value="answer" />
            <el-option label="意图识别错误" value="intent" />
            <el-option label="情绪识别错误" value="emotion" />
            <el-option label="用户画像不准确" value="profile" />
          </el-select>
        </el-form-item>
        <el-form-item label="正确的内容应该是">
          <el-input v-model="correctionForm.corrected" type="textarea" :rows="3" placeholder="请描述正确的情况..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="correctionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCorrection" :disabled="!correctionForm.corrected.trim()">提交反馈</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.kefu-chat-page {
  display: flex;
  height: calc(100vh - 120px);
  gap: 12px;
  padding: 16px;
}

.sidebar-panel {
  width: 240px;
  flex-shrink: 0;
  background: var(--el-bg-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.2s;
}
.session-item:hover { background: var(--el-fill-color-light); }
.session-item.active { background: var(--el-color-primary-light-9); }
.session-title { font-size: 13px; font-weight: 500; }
.session-meta { display: flex; gap: 6px; margin-top: 4px; font-size: 11px; color: var(--el-text-color-secondary); }

.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
  border-radius: 8px;
  overflow: hidden;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-chat {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
.welcome-card {
  max-width: 400px;
  padding: 24px;
  background: var(--el-fill-color-light);
  border-radius: 12px;
  text-align: left;
}
.welcome-card h3 { margin: 0 0 12px; }
.welcome-card ul { padding-left: 20px; }
.welcome-card li { margin: 6px 0; }
.tips { color: var(--el-text-color-secondary); font-size: 13px; margin-top: 12px; }

.profile-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.profile-orders {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.message-item {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  align-items: flex-start;
}
.message-item.user { flex-direction: row-reverse; }
.message-body { max-width: 70%; }
.message-content {
  padding: 10px 14px;
  border-radius: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.message-item.user .message-content { background: var(--el-color-primary); color: #fff; }
.message-item.agent .message-content { background: var(--el-fill-color); }
.message-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 4px; }
.message-feedback { margin-top: 4px; opacity: 0; transition: opacity 0.2s; }
.message-item:hover .message-feedback { opacity: 1; }
.typing { color: var(--el-text-color-secondary); font-style: italic; }

.input-area {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.input-actions { display: flex; gap: 8px; justify-content: flex-end; }
</style>