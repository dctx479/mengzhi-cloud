<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-box">
        <h1 class="login-title">登录</h1>
        <p class="login-subtitle">AI赋能云平台</p>

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
          <h2>欢迎使用</h2>
          <ul class="features">
            <li>智能AI助手</li>
            <li>产品推荐系统</li>
            <li>实时数据分析</li>
            <li>一站式云服务</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElForm } from 'element-plus'
import type { FormRules } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import { User } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
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
  try {
    await formRef.value?.validate()
    loading.value = true

    await userStore.login(formData.username, formData.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '登录失败')
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-container {
  display: flex;
  width: 900px;
  height: 500px;
  background: white;
  border-radius: 8px;
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
    color: #333;
    margin: 0 0 8px 0;
  }

  .login-subtitle {
    font-size: 14px;
    color: #999;
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
    color: #606266;

    .footer-link {
      color: #409eff;
      text-decoration: none;
      cursor: pointer;
      transition: color 0.3s;

      &:hover {
        color: #66b1ff;
      }
    }

    .divider {
      margin: 0 8px;
      color: #ddd;
    }
  }
}

.login-sidebar {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;

  .sidebar-content {
    h2 {
      font-size: 24px;
      margin-bottom: 32px;
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
          content: '✓ ';
          margin-right: 8px;
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
