<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-box">
        <h1 class="login-title">登录</h1>
        <p class="login-subtitle">蒙智云</p>

        <el-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          @keyup.enter="handleSubmit"
          class="login-form"
          aria-label="登录表单"
        >
          <el-form-item prop="username">
            <el-input
              v-model="formData.username"
              placeholder="用户名 / 邮箱"
              clearable
              aria-label="用户名或邮箱"
              aria-required="true"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="formData.password"
              type="password"
              placeholder="密码"
              show-password
              aria-label="密码"
              aria-required="true"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="loading"
              :disabled="loading"
              aria-label="登录"
              @click="handleSubmit"
            >
              {{ loading ? '登录中...' : '登录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          <router-link to="/register" class="footer-link">注册新账户</router-link>
          <span class="divider">|</span>
          <a href="#" class="footer-link">忘记密码？</a>
        </div>
      </div>

      <div class="login-sidebar">
        <div class="sidebar-content">
          <h2>欢迎使用蒙智云</h2>
          <ul class="features">
            <li>内蒙古优质农畜产品</li>
            <li>AI 智能推荐系统</li>
            <li>产地直供 品质保障</li>
            <li>一站式云服务平台</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElForm } from 'element-plus'
import type { FormRules } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import { User } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const formRef = ref<InstanceType<typeof ElForm>>()
const loading = ref(false)

const formData = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不少于6位', trigger: 'blur' },
  ],
}

const handleSubmit = async () => {
  if (loading.value) return
  // validate() rejects with false on validation failure — not an Error
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(formData.username, formData.password)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect as string
    router.push(redirect && redirect.startsWith('/') ? redirect : '/')
  } catch {
    // http interceptor already shows ElMessage.error for API errors
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, $color-primary-dark 0%, $color-primary 60%, #2ec4a0 100%);
}

.login-container {
  display: flex;
  width: 900px;
  height: 500px;
  background: white;
  border-radius: $radius-lg;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.login-box {
  flex: 1;
  padding: 60px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;

  .login-title {
    font-size: 28px;
    font-weight: 600;
    color: $color-text-primary;
    margin: 0 0 $spacing-sm 0;
  }

  .login-subtitle {
    font-size: 14px;
    color: $color-text-secondary;
    margin: 0 0 40px 0;
  }

  .login-form {
    :deep(.el-form-item) {
      margin-bottom: 20px;

      &:last-of-type {
        margin-bottom: 24px;
      }

      .el-input {
        height: 40px;

        :deep(input) {
          font-size: 14px;
        }
      }
    }

    .login-btn {
      width: 100%;
      height: 40px;
      font-size: 16px;
    }
  }

  .login-footer {
    text-align: center;
    font-size: 14px;
    color: $color-text-regular;

    .footer-link {
      color: $color-primary;
      text-decoration: none;
      cursor: pointer;
      transition: color 0.3s;

      &:hover {
        color: $color-primary-dark;
      }
    }

    .divider {
      margin: 0 $spacing-sm;
      color: $color-border;
    }
  }
}

.login-sidebar {
  flex: 1;
  background: linear-gradient(135deg, $color-primary-dark 0%, $color-primary 60%, #2ec4a0 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;

  .sidebar-content {
    h2 {
      font-size: 24px;
      margin-bottom: $spacing-xl;
      text-align: center;
    }

    .features {
      list-style: none;
      padding: 0;
      margin: 0;

      li {
        padding: 12px 0;
        font-size: 16px;
        opacity: 0.9;

        &:before {
          content: '\2713  ';
          margin-right: $spacing-sm;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .login-container {
    width: 100%;
    height: auto;
    flex-direction: column;
    border-radius: 0;
  }

  .login-box {
    padding: 40px 20px;
  }

  .login-sidebar {
    display: none;
  }
}
</style>
