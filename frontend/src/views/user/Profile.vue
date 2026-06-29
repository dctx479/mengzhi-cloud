<template>
  <div class="profile-page">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <span>个人资料</span>
        </div>
      </template>

      <el-row :gutter="32">
        <!-- 左侧头像信息 -->
        <el-col :xs="24" :sm="6" class="profile-left">
          <div class="profile-avatar">
            <el-avatar :src="userStore.user?.avatar" :size="120" />
            <p class="profile-username">{{ userStore.username }}</p>
            <p class="profile-email">{{ userStore.user?.email }}</p>
            <el-tag :type="userStatusType" class="profile-status">
              {{ userStatusText }}
            </el-tag>
          </div>
        </el-col>

        <!-- 右侧编辑表单 -->
        <el-col :xs="24" :sm="18">
          <el-form
            v-if="isEditing"
            ref="formRef"
            :model="editForm"
            :rules="rules"
            label-width="100px"
            class="profile-form"
          >
            <el-form-item label="用户名">
              <el-input :model-value="editForm.username" disabled />
            </el-form-item>

            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="editForm.nickname" />
            </el-form-item>

            <el-form-item label="邮箱">
              <el-input v-model="editForm.email" disabled />
            </el-form-item>

            <el-form-item label="手机">
              <el-input :model-value="editForm.phone" disabled placeholder="请前往安全中心绑定或修改" />
            </el-form-item>

            <el-form-item label="个人简介" prop="bio">
              <el-input
                v-model="editForm.bio"
                type="textarea"
                :rows="4"
                placeholder="输入你的个人简介"
              />
            </el-form-item>

            <el-form-item label="所在地" prop="location">
              <el-input v-model="editForm.location" placeholder="可选" />
            </el-form-item>

            <el-form-item label="个人网站" prop="website">
              <el-input v-model="editForm.website" placeholder="可选" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSave" :loading="saving">
                保存
              </el-button>
              <el-button @click="handleCancel">取消</el-button>
            </el-form-item>
          </el-form>

          <div v-else class="profile-info">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="用户名">
                {{ userStore.user?.username }}
              </el-descriptions-item>

              <el-descriptions-item label="昵称">
                {{ userStore.user?.nickname || '-' }}
              </el-descriptions-item>

              <el-descriptions-item label="邮箱">
                {{ userStore.user?.email }}
              </el-descriptions-item>

              <el-descriptions-item label="手机">
                {{ userStore.user?.phone || '-' }}
              </el-descriptions-item>

              <el-descriptions-item label="个人简介" :span="2">
                {{ userStore.user?.bio || '-' }}
              </el-descriptions-item>

              <el-descriptions-item label="所在地">
                {{ userStore.user?.location || '-' }}
              </el-descriptions-item>

              <el-descriptions-item label="个人网站">
                {{ userStore.user?.website || '-' }}
              </el-descriptions-item>

              <el-descriptions-item label="注册时间" :span="2">
                {{ formatDate(userStore.user?.createdAt) }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="profile-actions">
              <el-button type="primary" @click="handleEdit">编辑资料</el-button>
              <router-link to="/user/settings">
                <el-button>账号设置</el-button>
              </router-link>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ userStore.userProfile?.totalChats ?? 0 }}</div>
            <div class="stat-label">AI对话次数</div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ userStore.userProfile?.totalProducts ?? 0 }}</div>
            <div class="stat-label">浏览产品</div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ userStore.userProfile?.totalFavorites ?? 0 }}</div>
            <div class="stat-label">收藏数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const formRef = ref<InstanceType<typeof ElForm>>()
const isEditing = ref(false)
const saving = ref(false)

const editForm = reactive({
  username: '',
  nickname: '',
  email: '',
  phone: '',
  bio: '',
  location: '',
  website: '',
})

const rules = {
  nickname: [
    { max: 30, message: '昵称最多 30 个字符', trigger: 'blur' },
  ],
  website: [
    {
      pattern: /^(https?:\/\/)[\w\-]+(\.[\w\-]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?$/,
      message: '请输入有效的网址（以 http:// 或 https:// 开头）',
      trigger: 'blur',
    },
  ],
}

const userStatusText = computed(() => {
  const status = userStore.user?.status
  const statusMap: Record<string, string> = {
    active: '正常',
    inactive: '未激活',
    banned: '禁用',
  }
  return statusMap[status || 'active'] || '未知'
})

const userStatusType = computed(() => {
  const status = userStore.user?.status
  const typeMap: Record<string, string> = {
    active: 'success',
    inactive: 'warning',
    banned: 'danger',
  }
  return typeMap[status || 'active'] || 'info'
})

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const handleEdit = () => {
  if (userStore.user) {
    editForm.username = userStore.user.username
    editForm.nickname = userStore.user.nickname || ''
    editForm.email = userStore.user.email
    editForm.phone = userStore.user.phone || ''
    editForm.bio = userStore.user?.bio || ''
    editForm.location = userStore.user?.location || ''
    editForm.website = userStore.user?.website || ''
  }
  isEditing.value = true
}

const handleCancel = () => {
  isEditing.value = false
}

const handleSave = async () => {
  try {
    await formRef.value?.validate()
    saving.value = true

    await userStore.updateProfile({
      nickname: editForm.nickname,
      bio: editForm.bio,
      location: editForm.location,
      website: editForm.website,
    })

    ElMessage.success('资料更新成功')
    isEditing.value = false
  } catch (error) {
    ElMessage.error('更新失败，请重试')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  if (!userStore.user) {
    try {
      await userStore.fetchCurrentUser()
    } catch {
      ElMessage.error('加载用户信息失败')
    }
  }
})
</script>

<style scoped lang="scss">
.profile-page {
  max-width: 1000px;

  .profile-card {
    margin-bottom: $spacing-lg;
    border-radius: $radius-md;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 18px;
      font-weight: 600;
    }
  }

  .profile-left {
    display: flex;
    flex-direction: column;
    align-items: center;

    .profile-avatar {
      text-align: center;
      width: 100%;

      .el-avatar {
        margin-bottom: $spacing-md;
        border: 2px solid $color-primary;
      }

      .profile-username {
        font-size: 18px;
        font-weight: 600;
        color: $color-text-primary;
        margin: 0 0 $spacing-xs 0;
      }

      .profile-email {
        font-size: 14px;
        color: $color-text-secondary;
        margin: 0 0 12px 0;
      }

      .profile-status {
        margin-top: $spacing-sm;
      }
    }
  }

  .profile-form {
    :deep(.el-form-item) {
      margin-bottom: 20px;
    }
  }

  .profile-info {
    :deep(.el-descriptions) {
      margin-bottom: 20px;
    }

    .profile-actions {
      display: flex;
      gap: 12px;
      justify-content: flex-start;

      a {
        text-decoration: none;
      }
    }
  }

  .stats-row {
    margin-top: $spacing-lg;

    .stat-card {
      border-radius: $radius-md;
      transition: transform 0.2s, box-shadow 0.2s;

      &:hover {
        transform: translateY(-2px);
        box-shadow: $shadow-md;
      }

      :deep(.el-card__body) {
        padding: 20px;
      }

      .stat-content {
        text-align: center;

        .stat-value {
          font-size: 32px;
          font-weight: 600;
          color: $color-primary;
          margin-bottom: $spacing-sm;
        }

        .stat-label {
          font-size: 14px;
          color: $color-text-secondary;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .profile-page {
    .profile-left {
      margin-bottom: $spacing-lg;
    }
  }
}
</style>
