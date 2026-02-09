<template>
  <div class="security-page">
    <!-- 密码管理 -->
    <el-card class="security-card">
      <template #header>
        <div class="card-header">
          <el-icon><Lock /></el-icon>
          <span>密码管理</span>
        </div>
      </template>

      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="120px"
        class="security-form"
        @submit.prevent="handleChangePassword"
      >
        <el-form-item label="当前密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            placeholder="请输入当前密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码（至少8位，包含大小写字母和数字）"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">
            修改密码
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 联系方式绑定 -->
    <el-card class="security-card">
      <template #header>
        <div class="card-header">
          <el-icon><PhoneFilled /></el-icon>
          <span>联系方式</span>
        </div>
      </template>

      <div class="contact-items">
        <!-- 绑定邮箱 -->
        <div class="contact-item">
          <div class="contact-info">
            <div class="contact-type">
              <el-icon><Message /></el-icon>
              <span>邮箱地址</span>
            </div>
            <div class="contact-value">{{ userStore.user?.email || '-' }}</div>
            <div class="contact-status">
              <el-tag type="success">已认证</el-tag>
            </div>
          </div>
          <div class="contact-actions">
            <el-button link type="primary" size="small" @click="handleChangeEmail">
              更改
            </el-button>
          </div>
        </div>

        <!-- 绑定手机 -->
        <el-divider />
        <div class="contact-item">
          <div class="contact-info">
            <div class="contact-type">
              <el-icon><Phone /></el-icon>
              <span>手机号</span>
            </div>
            <div class="contact-value">{{ userStore.user?.phone || '未绑定' }}</div>
            <div class="contact-status">
              <el-tag v-if="userStore.user?.phone" type="success">已认证</el-tag>
              <el-tag v-else type="danger">未绑定</el-tag>
            </div>
          </div>
          <div class="contact-actions">
            <el-button link type="primary" size="small" @click="handleBindPhone">
              {{ userStore.user?.phone ? '更改' : '绑定' }}
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 登录日志 -->
    <el-card class="security-card">
      <template #header>
        <div class="card-header">
          <el-icon><Document /></el-icon>
          <span>登录历史</span>
        </div>
      </template>

      <div v-if="loadingLogs" class="text-center">
        <el-empty description="加载中..."></el-empty>
      </div>

      <div v-else-if="securityLogs.length === 0" class="text-center">
        <el-empty description="暂无登录记录"></el-empty>
      </div>

      <el-table v-else :data="securityLogs" style="width: 100%">
        <el-table-column label="时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="事件" width="120">
          <template #default="{ row }">
            {{ getEventText(row.event_type) }}
          </template>
        </el-table-column>
        <el-table-column label="IP地址" width="150">
          {{ row.ip_address }}
        </el-table-column>
        <el-table-column label="设备" min-width="200">
          <template #default="{ row }">
            <div class="device-info">
              {{ parseUserAgent(row.user_agent) }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'">
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div v-if="logTotal > 0" class="pagination-container">
        <el-pagination
          v-model:current-page="logPage"
          v-model:page-size="logPageSize"
          :total="logTotal"
          :page-sizes="[5, 10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadSecurityLogs"
          @current-change="loadSecurityLogs"
        />
      </div>
    </el-card>

    <!-- 设备管理 -->
    <el-card class="security-card">
      <template #header>
        <div class="card-header">
          <el-icon><Monitor /></el-icon>
          <span>设备管理</span>
        </div>
      </template>

      <div v-if="loadingDevices" class="text-center">
        <el-empty description="加载中..."></el-empty>
      </div>

      <div v-else-if="devices.length === 0" class="text-center">
        <el-empty description="暂无设备信息"></el-empty>
      </div>

      <div v-else class="device-list">
        <el-card
          v-for="device in devices"
          :key="device.id"
          class="device-card"
          :body-style="{ padding: '16px' }"
        >
          <div class="device-content">
            <div class="device-info">
              <div class="device-name">
                <el-icon v-if="device.is_current" style="color: #67c23a">
                  <Check />
                </el-icon>
                {{ device.device_name }}
              </div>
              <div class="device-type">{{ device.device_type }}</div>
              <div class="device-details">
                <span>IP: {{ device.ip_address }}</span>
                <el-divider direction="vertical"></el-divider>
                <span>最后登录: {{ formatDateTime(device.last_login) }}</span>
              </div>
            </div>
            <div class="device-actions">
              <el-button
                v-if="!device.is_current"
                link
                type="danger"
                size="small"
                @click="handleRemoveDevice(device.id)"
              >
                移除
              </el-button>
              <el-tag v-else type="success">当前设备</el-tag>
            </div>
          </div>
        </el-card>
      </div>
    </el-card>

    <!-- 绑定手机对话框 -->
    <el-dialog
      v-model="bindPhoneDialogVisible"
      title="绑定手机号"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="phoneFormRef"
        :model="phoneForm"
        :rules="phoneRules"
        label-width="100px"
      >
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="phoneForm.phone" placeholder="请输入手机号" />
        </el-form-item>

        <el-form-item label="验证码" prop="verification_code">
          <el-row :gutter="10">
            <el-col :span="16">
              <el-input v-model="phoneForm.verification_code" placeholder="请输入验证码" />
            </el-col>
            <el-col :span="8">
              <el-button
                :disabled="!phoneForm.phone || sendingCode || countDown > 0"
                @click="handleSendCode('phone')"
              >
                {{ countDown > 0 ? `${countDown}s` : '发送验证码' }}
              </el-button>
            </el-col>
          </el-row>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="bindPhoneDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmitBindPhone">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 更改邮箱对话框 -->
    <el-dialog
      v-model="changeEmailDialogVisible"
      title="更改邮箱"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="emailFormRef"
        :model="emailForm"
        :rules="emailRules"
        label-width="100px"
      >
        <el-form-item label="新邮箱" prop="email">
          <el-input v-model="emailForm.email" placeholder="请输入新邮箱" type="email" />
        </el-form-item>

        <el-form-item label="验证码" prop="verification_code">
          <el-row :gutter="10">
            <el-col :span="16">
              <el-input v-model="emailForm.verification_code" placeholder="请输入验证码" />
            </el-col>
            <el-col :span="8">
              <el-button
                :disabled="!emailForm.email || sendingCode || countDown > 0"
                @click="handleSendCode('email')"
              >
                {{ countDown > 0 ? `${countDown}s` : '发送验证码' }}
              </el-button>
            </el-col>
          </el-row>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="changeEmailDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmitChangeEmail">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import {
  Lock,
  PhoneFilled,
  Phone,
  Message,
  Document,
  Monitor,
  Check,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { changePassword, getSecurityLogs, getDevices, removeDevice, bindPhone, bindEmail, sendVerificationCode } from '@/api/user'
import type { SecurityLog, ChangePasswordRequest } from '@/types/user'

const userStore = useUserStore()
const passwordFormRef = ref<InstanceType<typeof ElForm>>()
const phoneFormRef = ref<InstanceType<typeof ElForm>>()
const emailFormRef = ref<InstanceType<typeof ElForm>>()

// 密码修改
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const passwordRules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    {
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/,
      message: '密码至少8位，需包含大小写字母和数字',
      trigger: 'blur',
    },
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.value.new_password) {
          callback(new Error('两次密码输入不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 手机绑定
const bindPhoneDialogVisible = ref(false)
const phoneForm = ref({
  phone: '',
  verification_code: '',
})

const phoneRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入有效的手机号',
      trigger: 'blur',
    },
  ],
  verification_code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
}

// 邮箱更改
const changeEmailDialogVisible = ref(false)
const emailForm = ref({
  email: '',
  verification_code: '',
})

const emailRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱', trigger: 'blur' },
  ],
  verification_code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
}

// 其他数据
const securityLogs = ref<SecurityLog[]>([])
const loadingLogs = ref(false)
const logPage = ref(1)
const logPageSize = ref(10)
const logTotal = ref(0)

const devices = ref<any[]>([])
const loadingDevices = ref(false)

const changingPassword = ref(false)
const sendingCode = ref(false)
const countDown = ref(0)

const formatDateTime = (dateStr: string): string => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getEventText = (eventType: string): string => {
  const eventMap: Record<string, string> = {
    login: '登录',
    logout: '登出',
    password_change: '修改密码',
    phone_bind: '绑定手机',
    email_change: '更改邮箱',
  }
  return eventMap[eventType] || eventType
}

const parseUserAgent = (userAgent: string): string => {
  if (userAgent.includes('Windows')) return 'Windows'
  if (userAgent.includes('Mac')) return 'macOS'
  if (userAgent.includes('Linux')) return 'Linux'
  if (userAgent.includes('iPhone')) return 'iPhone'
  if (userAgent.includes('Android')) return 'Android'
  return '未知设备'
}

const handleChangePassword = async () => {
  try {
    await passwordFormRef.value?.validate()
    changingPassword.value = true

    const data: ChangePasswordRequest = {
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password,
      confirm_password: passwordForm.value.confirm_password,
    }

    await changePassword(data)
    ElMessage.success('密码修改成功，请重新登录')

    // 重置表单
    passwordForm.value = {
      old_password: '',
      new_password: '',
      confirm_password: '',
    }

    // 登出用户
    setTimeout(() => {
      userStore.logout()
    }, 1500)
  } catch (error) {
    ElMessage.error('密码修改失败，请检查密码是否正确')
    console.error(error)
  } finally {
    changingPassword.value = false
  }
}

const handleBindPhone = () => {
  phoneForm.value = {
    phone: userStore.user?.phone || '',
    verification_code: '',
  }
  bindPhoneDialogVisible.value = true
}

const handleChangeEmail = () => {
  emailForm.value = {
    email: userStore.user?.email || '',
    verification_code: '',
  }
  changeEmailDialogVisible.value = true
}

const handleSendCode = async (type: 'phone' | 'email') => {
  try {
    if (type === 'phone') {
      if (!phoneForm.value.phone) {
        ElMessage.error('请输入手机号')
        return
      }
      sendingCode.value = true
      await sendVerificationCode({
        type: 'phone',
        target: phoneForm.value.phone,
      })
    } else {
      if (!emailForm.value.email) {
        ElMessage.error('请输入邮箱')
        return
      }
      sendingCode.value = true
      await sendVerificationCode({
        type: 'email',
        target: emailForm.value.email,
      })
    }

    ElMessage.success('验证码已发送，请查收')
    countDown.value = 60

    const interval = setInterval(() => {
      countDown.value--
      if (countDown.value <= 0) {
        clearInterval(interval)
      }
    }, 1000)
  } catch (error) {
    ElMessage.error('发送验证码失败')
    console.error(error)
  } finally {
    sendingCode.value = false
  }
}

const handleSubmitBindPhone = async () => {
  try {
    await phoneFormRef.value?.validate()
    await bindPhone({
      phone: phoneForm.value.phone,
      verification_code: phoneForm.value.verification_code,
    })
    ElMessage.success('手机号绑定成功')
    bindPhoneDialogVisible.value = false
    await userStore.fetchCurrentUser()
  } catch (error) {
    ElMessage.error('绑定失败，请检查验证码')
    console.error(error)
  }
}

const handleSubmitChangeEmail = async () => {
  try {
    await emailFormRef.value?.validate()
    await bindEmail({
      email: emailForm.value.email,
      verification_code: emailForm.value.verification_code,
    })
    ElMessage.success('邮箱更改成功')
    changeEmailDialogVisible.value = false
    await userStore.fetchCurrentUser()
  } catch (error) {
    ElMessage.error('更改失败，请检查验证码')
    console.error(error)
  }
}

const handleRemoveDevice = async (deviceId: string) => {
  try {
    await ElMessageBox.confirm('确定要移除这个设备吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    await removeDevice(deviceId)
    ElMessage.success('设备已移除')
    await loadDevices()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
      console.error(error)
    }
  }
}

const loadSecurityLogs = async () => {
  try {
    loadingLogs.value = true
    const response = await getSecurityLogs({
      page: logPage.value,
      page_size: logPageSize.value,
    })
    securityLogs.value = response.items
    logTotal.value = response.total
  } catch (error) {
    ElMessage.error('加载登录日志失败')
    console.error(error)
  } finally {
    loadingLogs.value = false
  }
}

const loadDevices = async () => {
  try {
    loadingDevices.value = true
    const data = await getDevices()
    devices.value = data
  } catch (error) {
    ElMessage.error('加载设备列表失败')
    console.error(error)
  } finally {
    loadingDevices.value = false
  }
}

onMounted(() => {
  loadSecurityLogs()
  loadDevices()
})
</script>

<style scoped lang="scss">
.security-page {
  max-width: 1000px;

  .security-card {
    margin-bottom: 24px;

    .card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
    }
  }

  .security-form {
    :deep(.el-form-item) {
      margin-bottom: 16px;
    }
  }

  .contact-items {
    .contact-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;

      .contact-info {
        flex: 1;

        .contact-type {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 500;
          color: #333;
          margin-bottom: 4px;
        }

        .contact-value {
          font-size: 14px;
          color: #666;
          margin-bottom: 4px;
        }

        .contact-status {
          .el-tag {
            font-size: 12px;
          }
        }
      }

      .contact-actions {
        flex-shrink: 0;
        margin-left: 16px;
      }
    }
  }

  .device-list {
    display: flex;
    flex-direction: column;
    gap: 12px;

    .device-card {
      .device-content {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;

        .device-info {
          flex: 1;

          .device-name {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 500;
            color: #333;
            margin-bottom: 4px;
          }

          .device-type {
            font-size: 12px;
            color: #909399;
            margin-bottom: 8px;
          }

          .device-details {
            font-size: 12px;
            color: #606266;
            display: flex;
            align-items: center;
            gap: 4px;
          }
        }

        .device-actions {
          flex-shrink: 0;
          margin-left: 16px;
        }
      }
    }
  }

  .pagination-container {
    display: flex;
    justify-content: center;
    padding: 20px 0;
  }

  .text-center {
    padding: 40px 20px;
    text-align: center;
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }
}

@media (max-width: 768px) {
  .security-page {
    .contact-items {
      .contact-item {
        flex-direction: column;
        align-items: flex-start;

        .contact-actions {
          margin-left: 0;
          margin-top: 8px;
        }
      }
    }

    .device-list {
      .device-card {
        .device-content {
          flex-direction: column;

          .device-actions {
            margin-left: 0;
            margin-top: 12px;
          }
        }
      }
    }
  }
}
</style>
