<template>
  <div class="settings-page">
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <span>偏好设置</span>
        </div>
      </template>

      <el-form
        :model="settings"
        label-width="120px"
        class="settings-form"
        @submit.prevent="handleSaveSettings"
      >
        <!-- 通知设置 -->
        <el-divider content-position="left">
          <span class="divider-title">通知设置</span>
        </el-divider>

        <el-form-item label="邮件通知">
          <el-switch v-model="settings.email_notifications" />
          <span class="form-hint">接收系统邮件通知和重要提醒</span>
        </el-form-item>

        <el-form-item label="短信通知">
          <el-switch v-model="settings.sms_notifications" />
          <span class="form-hint">接收重要短信提醒（仅限重要事项）</span>
        </el-form-item>

        <!-- 隐私设置 -->
        <el-divider content-position="left">
          <span class="divider-title">隐私设置</span>
        </el-divider>

        <el-form-item label="个人资料公开">
          <el-switch v-model="settings.profile_public" />
          <span class="form-hint">允许其他用户查看您的公开信息</span>
        </el-form-item>

        <!-- 偏好设置 -->
        <el-divider content-position="left">
          <span class="divider-title">偏好设置</span>
        </el-divider>

        <el-form-item label="语言">
          <el-select v-model="settings.language" style="width: 200px">
            <el-option label="简体中文" value="zh-CN" />
            <el-option label="繁体中文" value="zh-TW" />
            <el-option label="English" value="en-US" />
            <el-option label="日本語" value="ja-JP" />
          </el-select>
          <span class="form-hint">选择系统界面语言</span>
        </el-form-item>

        <el-form-item label="主题">
          <el-radio-group v-model="settings.theme">
            <el-radio label="light">
              <el-icon style="margin-right: 4px"><Sunny /></el-icon>
              浅色
            </el-radio>
            <el-radio label="dark">
              <el-icon style="margin-right: 4px"><Moon /></el-icon>
              深色
            </el-radio>
            <el-radio label="auto">
              <el-icon style="margin-right: 4px"><Setting /></el-icon>
              跟随系统
            </el-radio>
          </el-radio-group>
          <span class="form-hint">选择应用主题偏好</span>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button type="primary" @click="handleSaveSettings" :loading="savingSettings">
            保存设置
          </el-button>
          <el-button @click="handleResetSettings">重置为默认</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 高级选项 -->
    <el-card class="advanced-section mt-4">
      <template #header>
        <div class="card-header">
          <span>高级选项</span>
        </div>
      </template>

      <el-form label-width="120px" class="settings-form">
        <el-form-item label="数据导出">
          <el-button @click="handleExportData">导出我的数据</el-button>
          <span class="form-hint">导出您的所有个人数据为 ZIP 文件</span>
        </el-form-item>

        <el-form-item label="清空缓存">
          <el-button @click="handleClearCache">清空缓存</el-button>
          <span class="form-hint">清空浏览器本地缓存数据</span>
        </el-form-item>

        <el-form-item label="账户注销">
          <el-button type="danger" @click="handleDeleteAccount">注销账户</el-button>
          <span class="form-hint">
            <span style="color: #f56c6c; font-weight: bold">此操作无法撤销，请谨慎操作</span>
          </span>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Sunny, Moon, Setting } from '@element-plus/icons-vue'
import { getSettings, updateSettings } from '@/api/user'
import type { UserSettings } from '@/types/user'

const settings = ref<UserSettings>({
  email_notifications: true,
  sms_notifications: false,
  profile_public: false,
  language: 'zh-CN',
  theme: 'light',
})

const defaultSettings: UserSettings = {
  email_notifications: true,
  sms_notifications: false,
  profile_public: false,
  language: 'zh-CN',
  theme: 'auto',
}

const savingSettings = ref(false)

const loadSettings = async () => {
  try {
    const data = await getSettings()
    settings.value = data
  } catch (error) {
    // 如果获取失败，使用默认设置
    console.error('加载设置失败，使用默认值:', error)
    settings.value = { ...defaultSettings }
  }
}

const handleSaveSettings = async () => {
  try {
    savingSettings.value = true
    await updateSettings(settings.value)
    ElMessage.success('设置已保存')
    // 应用语言和主题设置
    applySettings()
  } catch (error) {
    ElMessage.error('保存设置失败，请重试')
    console.error(error)
  } finally {
    savingSettings.value = false
  }
}

const handleResetSettings = async () => {
  try {
    await ElMessageBox.confirm('确定要重置为默认设置吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    if (savingSettings.value) return
    settings.value = { ...defaultSettings }
    await handleSaveSettings()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleExportData = async () => {
  try {
    ElMessage.info('数据导出功能开发中，敬请期待')
    // TODO: 实现数据导出功能
  } catch (error) {
    ElMessage.error('导出失败，请重试')
    console.error(error)
  }
}

const handleClearCache = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有缓存吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    // 清空 localStorage
    localStorage.clear()
    // 清空 sessionStorage
    sessionStorage.clear()

    ElMessage.success('缓存已清空，页面将刷新')
    setTimeout(() => {
      window.location.reload()
    }, 1000)
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleDeleteAccount = async () => {
  try {
    await ElMessageBox.prompt(
      '注销账户是一项严肃的决定。您的所有数据将被永久删除，此操作无法撤销。',
      '注销账户',
      {
        confirmButtonText: '注销',
        cancelButtonText: '取消',
        type: 'warning',
        
        inputPlaceholder: '请输入您的用户名',
      }
    )

    ElMessage.info('账户注销功能开发中，敬请期待')
    // TODO: 实现账户注销功能
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const applySettings = () => {
  // 应用语言设置
  if (settings.value.language) {
    localStorage.setItem('language', settings.value.language)
  }

  // 应用主题设置
  if (settings.value.theme) {
    localStorage.setItem('theme', settings.value.theme)
    applyTheme(settings.value.theme)
  }
}

const applyTheme = (theme: string) => {
  const html = document.documentElement
  if (theme === 'dark') {
    html.classList.add('dark')
  } else if (theme === 'light') {
    html.classList.remove('dark')
  } else {
    // auto - 跟随系统
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    if (prefersDark) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped lang="scss">
.settings-page {
  max-width: 800px;

  .page-header {
    margin-bottom: 24px;

    .card-header {
      font-size: 18px;
      font-weight: 600;
    }
  }

  .settings-form {
    :deep(.el-form-item) {
      margin-bottom: 20px;

      &:last-child {
        margin-bottom: 0;
      }
    }

    .el-switch {
      margin-right: 12px;
    }

    .el-radio {
      margin-right: 20px;
    }
  }

  .divider-title {
    font-weight: 600;
    color: #333;
  }

  .form-hint {
    display: block;
    margin-top: 8px;
    font-size: 12px;
    color: #909399;
    line-height: 1.5;
  }

  .advanced-section {
    background-color: #fafafa;
    border-color: #f0f0f0;

    .card-header {
      font-size: 16px;
      font-weight: 600;
      color: #f56c6c;
    }
  }

  .mt-4 {
    margin-top: 24px;
  }
}

@media (max-width: 768px) {
  .settings-page {
    .settings-form {
      :deep(.el-form-item__label) {
        width: auto !important;
        margin-bottom: 8px;
      }

      :deep(.el-form-item__content) {
        margin-left: 0 !important;
      }
    }
  }
}
</style>
