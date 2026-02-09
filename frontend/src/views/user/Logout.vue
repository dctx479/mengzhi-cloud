<template>
  <div class="logout-container">
    <div class="logout-content">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>正在退出登录...</p>
      </div>
      <div v-else-if="error" class="error">
        <p>退出登录失败: {{ error }}</p>
        <button @click="handleLogout" class="retry-btn">重试</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(true)
const error = ref<string | null>(null)

const handleLogout = async () => {
  loading.value = true
  error.value = null
  
  try {
    await userStore.logout()
    // 退出成功，跳转到登录页
    router.push('/login')
  } catch (err) {
    loading.value = false
    error.value = err instanceof Error ? err.message : '退出登录失败'
  }
}

// 组件挂载时自动执行退出
onMounted(() => {
  handleLogout()
})
</script>

<style scoped>
.logout-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  padding: 2rem;
}

.logout-content {
  text-align: center;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  color: #e74c3c;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.retry-btn:hover {
  background-color: #2980b9;
}
</style>
