<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-box">
        <h1 class="register-title">注册账户</h1>
        <p class="register-subtitle">加入AI赋能云平台</p>

        <el-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          @keyup.enter="handleSubmit"
          class="register-form"
          aria-label="注册表单"
        >
          <el-form-item prop="username">
            <el-input
              v-model="formData.username"
              placeholder="用户名"
              clearable
              aria-label="用户名"
              aria-required="true"
              @input="debouncedCheckUsername"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
              <template #suffix>
                <el-icon v-if="checkingUsername" class="is-loading"><Loading /></el-icon>
                <el-icon v-else-if="usernameAvailable === true" style="color: #67c23a"><CircleCheck /></el-icon>
                <el-icon v-else-if="usernameAvailable === false" style="color: #f56c6c"><CircleClose /></el-icon>
              </template>
            </el-input>
            <div v-if="usernameAvailable === false" class="field-error">该用户名已被使用</div>
          </el-form-item>

          <el-form-item prop="email">
            <el-autocomplete
              v-model="formData.email"
              :fetch-suggestions="(_queryString: string, cb: (suggestions: { value: string }[]) => void) => cb(emailSuggestions.map(s => ({ value: s })))"
              placeholder="邮箱地址"
              clearable
              @input="() => { debouncedCheckEmail(); validateEmailField(); }" @blur="() => { debouncedCheckEmail(); validateEmailField() }"
            >
              <template #prefix>
                <el-icon><Message /></el-icon>
              </template>
              <template #suffix>
                <el-icon v-if="checkingEmail" class="is-loading"><Loading /></el-icon>
                <el-icon v-else-if="emailAvailable === true && !emailError" style="color: #67c23a"><CircleCheck /></el-icon>
                <el-icon v-else-if="emailAvailable === false || emailError" style="color: #f56c6c"><CircleClose /></el-icon>
              </template>
            </el-autocomplete>
            <div class="email-domains">
              <span style="font-size: 12px; color: #909399; margin-right: 8px;">常用域名：</span>
              <el-tag
                v-for="domain in ['@gmail.com', '@qq.com', '@163.com', '@126.com', '@outlook.com', '@sina.com', '@foxmail.com', '@hotmail.com']"
                :key="domain"
                size="small"
                style="margin-right: 4px; margin-bottom: 4px; cursor: pointer;"
                @click="selectDomain(domain)"
              >
                {{ domain }}
              </el-tag>
            </div>
            <div v-if="emailError" class="field-error">{{ emailError }}</div>
            <div v-else-if="emailAvailable === false" class="field-error">该邮箱已被注册</div>
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="formData.password"
              type="password"
              placeholder="密码（8-32位，需包含大小写字母、数字和特殊字符）"
              show-password
              aria-label="密码"
              aria-required="true"
              @input="validatePasswordField"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
            <div v-if="formData.password" class="password-strength">
              <span>密码强度: </span>
              <span :style="{ color: passwordStrength.color }">{{ passwordStrength.text }}</span>
            </div>
            <div v-if="passwordErrors.length > 0" class="password-requirements">
              <div v-for="(error, index) in passwordErrors" :key="index" class="requirement-item">{{ error }}</div>
            </div>
          </el-form-item>

          <el-form-item prop="confirmPassword">
            <el-input
              v-model="formData.confirmPassword"
              type="password"
              placeholder="确认密码"
              show-password
              aria-label="确认密码"
              aria-required="true"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item prop="agree">
            <el-checkbox v-model="formData.agree">
              我同意
              <a href="#" class="link">服务条款</a>
              和
              <a href="#" class="link">隐私政策</a>
            </el-checkbox>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="register-btn"
              :loading="loading"
              :disabled="loading"
              aria-label="注册"
              @click="handleSubmit"
            >
              {{ loading ? '注册中...' : '注册' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="register-footer">
          <span class="footer-text">已有账户？</span>
          <router-link to="/login" class="footer-link">立即登录</router-link>
        </div>
      </div>

      <div class="register-sidebar">
        <div class="sidebar-content">
          <h2>为什么选择我们</h2>
          <ul class="benefits">
            <li>
              <div class="benefit-icon">1</div>
              <span>安全可靠</span>
            </li>
            <li>
              <div class="benefit-icon">2</div>
              <span>高效便捷</span>
            </li>
            <li>
              <div class="benefit-icon">3</div>
              <span>智能推荐</span>
            </li>
            <li>
              <div class="benefit-icon">4</div>
              <span>7x24 服务</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElForm } from 'element-plus'
import type { FormRules } from 'element-plus'
import { User, Message, Lock } from '@element-plus/icons-vue'
import { Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { checkAvailability } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref<InstanceType<typeof ElForm>>()
const loading = ref(false)

const formData = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agree: false,
})

// 常用邮箱域名列表
const emailDomains = [
  '@gmail.com',
  '@qq.com',
  '@163.com',
  '@126.com',
  '@outlook.com',
  '@hotmail.com',
  '@yahoo.com',
  '@foxmail.com',
  '@sina.com',
  '@sohu.com',
  '@139.com',
  '@wo.cn',
  '@189.cn',
  '@icloud.com',
  '@live.com',
  '@msn.com',
  '@yeah.net',
  '@aliyun.com',
  '@21cn.com',
  '@vip.qq.com',
]

// 邮箱建议列表
const emailSuggestions = computed(() => {
  const email = formData.email
  if (!email || !email.includes('@')) return []

  const [username, domain] = email.split('@')
  if (!username) return []

  return emailDomains
    .filter(d => d.toLowerCase().includes(domain?.toLowerCase() || ''))
    .map(d => username + d)
    .slice(0, 5)
})

// 防抖函数 — 返回带 cancel 方法的版本以便组件卸载时清理
const debounce = <T extends (...args: any[]) => any>(fn: T, delay: number) => {
  let timer: ReturnType<typeof setTimeout> | null = null
  const debounced = (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
  debounced.cancel = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }
  return debounced
}

// 验证结果缓存
const validationCache = new Map<string, boolean>()

// 检查用户名可用性
const checkingUsername = ref(false)
const usernameAvailable = ref<boolean | null>(null)

const checkUsernameAvailability = async () => {
  if (formData.username.length < 3) {
    usernameAvailable.value = null
    return
  }

  // 检查缓存
  const cacheKey = `username:${formData.username}`
  if (validationCache.has(cacheKey)) {
    usernameAvailable.value = validationCache.get(cacheKey)!
    return
  }

  checkingUsername.value = true
  try {
    const available = await checkAvailability('username', formData.username)
    usernameAvailable.value = available
    validationCache.set(cacheKey, available)
  } catch (error) {
    usernameAvailable.value = null
  } finally {
    checkingUsername.value = false
  }
}

const debouncedCheckUsername = debounce(checkUsernameAvailability, 500)

// 检查邮箱可用性
const checkingEmail = ref(false)
const emailAvailable = ref<boolean | null>(null)

const checkEmailAvailability = async () => {
  if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
    emailAvailable.value = null
    return
  }

  // 检查缓存
  const cacheKey = `email:${formData.email}`
  if (validationCache.has(cacheKey)) {
    emailAvailable.value = validationCache.get(cacheKey)!
    return
  }

  checkingEmail.value = true
  try {
    const available = await checkAvailability('email', formData.email)
    emailAvailable.value = available
    validationCache.set(cacheKey, available)
  } catch (error) {
    emailAvailable.value = null
  } finally {
    checkingEmail.value = false
  }
}

const debouncedCheckEmail = debounce(checkEmailAvailability, 500)

const validatePassword = (_rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请确认密码'))
  } else if (value !== formData.password) {
    callback(new Error('两次输入密码不一致!'))
  } else {
    callback()
  }
}

const checkPasswordStrength = (password: string): { level: number; text: string; color: string } => {
  if (!password) return { level: 0, text: '', color: '' }

  let strength = 0
  if (password.length >= 8) strength++
  if (/[a-z]/.test(password)) strength++
  if (/[A-Z]/.test(password)) strength++
  if (/[0-9]/.test(password)) strength++
  if (/[^a-zA-Z0-9]/.test(password)) strength++

  if (strength <= 2) return { level: 1, text: '弱', color: '#f56c6c' }
  if (strength <= 3) return { level: 2, text: '中', color: '#e6a23c' }
  return { level: 3, text: '强', color: '#67c23a' }
}

const passwordStrength = computed(() => checkPasswordStrength(formData.password))

// 密码错误提示
const passwordErrors = ref<string[]>([])

const validatePasswordField = () => {
  const errors: string[] = []
  const pwd = formData.password

  if (pwd && pwd.length > 0) {
    if (pwd.length < 8) errors.push('❌ 密码长度至少8位')
    if (pwd.length > 32) errors.push('❌ 密码长度最多32位')
    if (!/[A-Z]/.test(pwd)) errors.push('❌ 缺少大写字母（A-Z）')
    if (!/[a-z]/.test(pwd)) errors.push('❌ 缺少小写字母（a-z）')
    if (!/[0-9]/.test(pwd)) errors.push('❌ 缺少数字（0-9）')
    if (!/[^a-zA-Z0-9]/.test(pwd)) errors.push('❌ 缺少特殊字符（!@#$%^&*等）')
  }

  passwordErrors.value = errors
}

// 邮箱错误提示
const emailError = ref<string>('')

const validateEmailField = () => {
  const email = formData.email
  if (email && email.endsWith('.test')) {
    emailError.value = '❌ 请使用真实的邮箱域名（如 @gmail.com、@qq.com）'
  } else {
    emailError.value = ''
  }
}

// 选择邮箱域名
const selectDomain = (domain: string) => {
  const email = formData.email
  if (email && email.includes('@')) {
    formData.email = email.split('@')[0] + domain
  } else if (email) {
    formData.email = email + domain
  }
  validateEmailField()
  debouncedCheckEmail()
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度 3-50 位', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_-]+$/,
      message: '用户名只能包含字母、数字、下划线和连字符',
      trigger: 'blur'
    },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
    {
      validator: (_rule: any, value: any, callback: any) => {
        if (value && value.endsWith('.test')) {
          callback(new Error('请使用真实的邮箱域名（如 @gmail.com）'))
        } else {
          callback()
        }
      },
      trigger: ['blur', 'change']
    },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 32, message: '密码长度 8-32 位', trigger: 'blur' },
    {
      validator: (_rule: any, value: any, callback: any) => {
        if (!value) {
          callback()
          return
        }
        if (!/[A-Z]/.test(value)) {
          callback(new Error('密码必须包含至少一个大写字母'))
        } else if (!/[a-z]/.test(value)) {
          callback(new Error('密码必须包含至少一个小写字母'))
        } else if (!/[0-9]/.test(value)) {
          callback(new Error('密码必须包含至少一个数字'))
        } else if (!/[^a-zA-Z0-9]/.test(value)) {
          callback(new Error('密码必须包含至少一个特殊字符（如 !@#$%^&* 等）'))
        } else {
          callback()
        }
      },
      trigger: ['blur', 'change']
    },
  ],
  confirmPassword: [{ validator: validatePassword, trigger: 'blur' }],
  agree: [
    {
      validator: (_rule: any, value: any, callback: any) => {
        if (value) {
          callback()
        } else {
          callback(new Error('请同意服务条款'))
        }
      },
      trigger: 'change',
    },
  ],
}

onUnmounted(() => {
  debouncedCheckUsername.cancel()
  debouncedCheckEmail.cancel()
})

const handleSubmit = async () => {
  if (loading.value) return
  // validate() rejects with false on validation failure — not an Error
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.register(formData.username, formData.email, formData.password)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch {
    // http interceptor already shows ElMessage.error for API errors
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, $color-primary-dark 0%, $color-primary 60%, #2ec4a0 100%);
}

.register-container {
  display: flex;
  width: 900px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.register-box {
  flex: 1;
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;

  .register-title {
    font-size: 24px;
    font-weight: 600;
    color: #333;
    margin: 0 0 8px 0;
  }

  .register-subtitle {
    font-size: 14px;
    color: #999;
    margin: 0 0 32px 0;
  }

  .register-form {
    :deep(.el-form-item) {
      margin-bottom: 16px;

      &:last-of-type {
        margin-bottom: 20px;
      }

      .el-input {
        height: 40px;
      }

      .el-checkbox {
        font-size: 12px;

        .link {
          color: $color-primary;
          text-decoration: none;
          margin: 0 4px;

          &:hover {
            text-decoration: underline;
          }
        }
      }
    }

    .register-btn {
      width: 100%;
      height: 40px;
      font-size: 16px;
    }
  }

  .register-footer {
    text-align: center;
    font-size: 14px;

    .footer-text {
      color: #606266;
      margin-right: 8px;
    }

    .footer-link {
      color: $color-primary;
      text-decoration: none;
      cursor: pointer;
      transition: color 0.3s;

      &:hover {
        color: $color-primary-dark;
      }
    }
  }
}

.register-sidebar {
  flex: 1;
  background: linear-gradient(135deg, $color-primary-dark 0%, $color-primary 60%, #2ec4a0 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;

  .sidebar-content {
    h2 {
      font-size: 20px;
      margin-bottom: 32px;
      text-align: center;
    }

    .benefits {
      list-style: none;
      padding: 0;
      margin: 0;

      li {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 0;
        font-size: 14px;

        .benefit-icon {
          width: 32px;
          height: 32px;
          background: rgba(255, 255, 255, 0.2);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          flex-shrink: 0;
        }
      }
    }
  }
}

.password-strength {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.field-error {
  margin-top: 4px;
  font-size: 12px;
  color: #f56c6c;
}

.password-requirements {
  margin-top: 4px;
  font-size: 12px;
  color: #f56c6c;
  line-height: 1.6;
}

.requirement-item {
  margin: 2px 0;
}

.email-domains {
  margin-top: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .register-container {
    width: 100%;
    flex-direction: column;
    border-radius: 0;
  }

  .register-box {
    padding: 30px 20px;
  }

  .register-sidebar {
    display: none;
  }
}
</style>
