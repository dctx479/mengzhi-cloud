<template>
  <div class="chat-page">
    <el-row :gutter="20" class="chat-container">
      <!-- 左侧：对话列表 -->
      <el-col :xs="24" :md="6" class="chat-sidebar">
        <div class="sidebar-header">
          <h2>对话列表</h2>
          <el-button type="primary" size="small" @click="handleNewChat">
            新建对话
          </el-button>
        </div>

        <el-input
          v-model="searchKeyword"
          placeholder="搜索对话..."
          clearable
          size="small"
          class="search-input"
          aria-label="搜索对话"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-skeleton v-if="chatStore.loading" :rows="5" animated />

        <div v-else class="chats-list">
          <div
            v-if="chatStore.chats.length === 0"
            class="empty-chats"
          >
            <el-empty description="暂无对话" />
          </div>

          <div
            v-for="chat in filteredChats"
            :key="chat.id"
            class="chat-item"
            :class="{ active: currentChatId === chat.id }"
            role="button"
            tabindex="0"
            :aria-label="`对话：${chat.title}`"
            :aria-current="currentChatId === chat.id ? 'true' : undefined"
            @click="handleSelectChat(chat.id)"
            @keydown.enter.space.prevent="handleSelectChat(chat.id)"
          >
            <div class="chat-info">
              <p class="chat-title">{{ chat.title }}</p>
              <p class="chat-time">{{ formatDate(chat.updatedAt) }}</p>
            </div>
            <el-icon
              class="delete-icon"
              role="button"
              tabindex="0"
              :aria-label="`删除对话：${chat.title}`"
              @click.stop="handleDeleteChat(chat.id)"
              @keydown.enter.space.prevent.stop="handleDeleteChat(chat.id)"
            >
              <Delete />
            </el-icon>
          </div>

          <el-button
            v-if="chatStore.hasMoreChats"
            text
            size="small"
            class="load-more"
            @click="handleLoadMore"
          >
            加载更多
          </el-button>
        </div>
      </el-col>

      <!-- 右侧：对话窗口 -->
      <el-col :xs="24" :md="18" class="chat-main">
        <div v-if="!currentChatId" class="empty-chat">
          <Empty
            title="开始对话"
            description="选择一个对话或创建新对话来开始"
            type="empty"
          />
        </div>

        <div v-else class="chat-content">
          <!-- 对话信息 -->
          <div class="chat-header">
            <h2>{{ currentChat?.title }}</h2>
            <div class="header-actions">
              <el-button text size="small" @click="handleClearChat">
                清空
              </el-button>
              <el-popconfirm
                title="确定删除此对话吗？"
                confirm-button-text="是"
                cancel-button-text="否"
                @confirm="handleDeleteCurrentChat"
              >
                <template #reference>
                  <el-button text size="small" type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>

          <!-- 消息列表 -->
          <MessageList
            :messages="chatStore.messages"
            :is-loading="chatStore.messageLoading"
            @delete-message="handleDeleteMessage"
          />

          <!-- 消息输入 -->
          <MessageInput
            :loading="chatStore.messageLoading"
            @send="handleSendMessage"
          />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Delete } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import MessageList from '@/components/chat/MessageList.vue'
import MessageInput from '@/components/chat/MessageInput.vue'
import Empty from '@/components/Empty.vue'

const chatStore = useChatStore()
const currentChatId = ref<string>('')
const searchKeyword = ref('')

const currentChat = computed(() =>
  chatStore.chats.find((chat) => chat.id === currentChatId.value)
)

const filteredChats = computed(() => {
  if (!searchKeyword.value) {
    return chatStore.chats
  }
  return chatStore.chats.filter((chat) =>
    chat.title.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffTime = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

const handleNewChat = async () => {
  try {
    const chat = await chatStore.createNewChat('新对话')
    currentChatId.value = chat.id
  } catch (error) {
    ElMessage.error('创建对话失败')
  }
}

const handleSelectChat = async (chatId: string) => {
  currentChatId.value = chatId
  try {
    await chatStore.fetchChatDetail(chatId)
  } catch (error) {
    ElMessage.error('加载对话失败')
  }
}

const handleDeleteChat = (chatId: string) => {
  ElMessageBox.confirm('确定删除此对话吗？', '提示', {
    confirmButtonText: '是',
    cancelButtonText: '否',
    type: 'warning',
  })
    .then(async () => {
      try {
        await chatStore.deleteChat(chatId)
        if (currentChatId.value === chatId) {
          currentChatId.value = ''
        }
        ElMessage.success('删除成功')
      } catch (error) {
        ElMessage.error('删除失败')
      }
    })
    .catch(() => {
      // User cancelled — no action needed
    })
}

const handleDeleteCurrentChat = async () => {
  if (!currentChatId.value) return
  try {
    await chatStore.deleteChat(currentChatId.value)
    currentChatId.value = ''
    ElMessage.success('删除成功')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const handleClearChat = async () => {
  ElMessageBox.confirm('确定清空此对话中的所有消息吗？', '提示', {
    confirmButtonText: '是',
    cancelButtonText: '否',
    type: 'warning',
  })
    .then(async () => {
      try {
        await chatStore.clearChat()
        ElMessage.success('清空成功')
      } catch (error) {
        ElMessage.error('清空失败')
      }
    })
    .catch(() => {
      // User cancelled — no action needed
    })
}

const handleDeleteMessage = async (messageId: string) => {
  try {
    await chatStore.deleteMessage(messageId)
    ElMessage.success('消息已删除')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const handleSendMessage = async (message: string) => {
  if (!currentChatId.value) {
    ElMessage.error('请先选择或创建对话')
    return
  }

  try {
    await chatStore.sendMessage(message)
  } catch (error) {
    ElMessage.error('发送失败，请重试')
  }
}

const handleLoadMore = async () => {
  try {
    await chatStore.fetchChats(chatStore.currentPage + 1)
  } catch (error) {
    ElMessage.error('加载失败')
  }
}

onMounted(async () => {
  try {
    if (chatStore.chats.length === 0) {
      await chatStore.fetchChats()
    }
  } catch (error) {
    ElMessage.error('加载对话列表失败')
  }
})

onUnmounted(() => {
  chatStore.resetState()
})
</script>

<style scoped lang="scss">
.chat-page {
  height: calc(100vh - 84px);
  background: #f0f2f5;

  .chat-container {
    height: 100%;
    margin: 0;

    .chat-sidebar {
      background: #fff;
      border-right: 1px solid #e8e8e8;
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;

      .sidebar-header {
        padding: 20px 16px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;

        h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 700;
          color: #1a1a1a;
        }

        :deep(.el-button) {
          border-radius: 8px;
          font-weight: 500;
        }
      }

      .search-input {
        margin: 0 16px 12px;

        :deep(.el-input__wrapper) {
          border-radius: 8px;
          background: #f5f7fa;
          box-shadow: none;
          border: 1px solid transparent;

          &:hover, &.is-focus {
            border-color: #0d9668;
          }
        }
      }

      .chats-list {
        flex: 1;
        overflow-y: auto;
        padding: 0 8px 8px;

        &::-webkit-scrollbar {
          width: 4px;
        }
        &::-webkit-scrollbar-thumb {
          background: #d9d9d9;
          border-radius: 4px;
        }

        .empty-chats {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 200px;
        }

        .chat-item {
          padding: 12px 14px;
          margin: 2px 0;
          border-radius: 10px;
          cursor: pointer;
          display: flex;
          justify-content: space-between;
          align-items: center;
          transition: all 0.2s ease;
          border: 1px solid transparent;

          &:hover {
            background: #f0f7f4;

            .delete-icon {
              visibility: visible;
            }
          }

          &.active {
            background: rgba(13, 150, 104, 0.08);
            border-color: rgba(13, 150, 104, 0.2);
            border-left: 3px solid #0d9668;
            padding-left: 11px;
          }

          .chat-info {
            flex: 1;
            min-width: 0;

            .chat-title {
              font-size: 14px;
              font-weight: 500;
              margin: 0 0 4px 0;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
              color: #333;
            }

            .chat-time {
              font-size: 12px;
              color: #aaa;
              margin: 0;
            }
          }

          .delete-icon {
            visibility: hidden;
            margin-left: 8px;
            color: #ccc;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;

            &:hover {
              color: #f56c6c;
            }
          }
        }

        .load-more {
          width: 100%;
          margin-top: 8px;
        }
      }
    }

    .chat-main {
      background: #f7f8fa;
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;

      .empty-chat {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        background: #f7f8fa;
      }

      .chat-content {
        display: flex;
        flex-direction: column;
        height: 100%;

        .chat-header {
          padding: 14px 24px;
          background: #fff;
          border-bottom: 1px solid #eee;
          box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
          display: flex;
          justify-content: space-between;
          align-items: center;
          z-index: 1;

          h2 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: #1a1a1a;
          }

          .header-actions {
            display: flex;
            gap: 4px;
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .chat-page {
    .chat-container {
      .chat-sidebar {
        position: fixed;
        left: 0;
        top: 64px;
        width: 240px;
        height: calc(100vh - 64px);
        z-index: 100;
        background: white;
        box-shadow: 2px 0 12px rgba(0, 0, 0, 0.08);
      }

      .chat-main {
        margin-left: 0;
      }
    }
  }
}
</style>
