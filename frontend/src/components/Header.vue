<template>
  <div class="header">
    <div class="header-container">
      <!-- Logo -->
      <div class="header-logo">
        <router-link to="/" class="logo-link">
          <span class="logo-text">AI赋能云平台</span>
        </router-link>
      </div>

      <!-- Navigation Menu -->
      <nav class="header-nav">
        <router-link to="/" class="nav-item">首页</router-link>
        <router-link to="/products" class="nav-item">产品</router-link>
        <router-link to="/chat" class="nav-item">AI助手</router-link>
      </nav>

      <!-- User Menu -->
      <div class="header-user">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索产品..."
          clearable
          @keyup.enter="handleSearch"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <div v-if="userStore.isLoggedIn" class="user-menu">
          <el-dropdown trigger="click">
            <div class="user-avatar">
              <el-avatar :src="userStore.user?.avatar" :size="32" />
              <span class="user-name">{{ userStore.username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>
                  <router-link to="/user/profile" class="dropdown-link">个人中心</router-link>
                </el-dropdown-item>
                <el-dropdown-item>
                  <router-link to="/user/settings" class="dropdown-link">设置</router-link>
                </el-dropdown-item>
                <el-dropdown-divider />
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div v-else class="auth-buttons">
          <router-link to="/login" class="btn-text">登录</router-link>
          <router-link to="/register" class="btn-primary">注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const searchKeyword = ref('')

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push({
      path: '/products',
      query: { keyword: searchKeyword.value },
    })
  }
}

const handleLogout = async () => {
  try {
    await userStore.logout()
    ElMessage.success('退出成功')
    router.push('/login')
  } catch (err) {
    ElMessage.error('退出失败')
  }
}
</script>

<style scoped lang="scss">
.header {
  background: white;
  border-bottom: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  position: sticky;
  top: 0;
  z-index: 100;

  .header-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
  }

  .header-logo {
    .logo-link {
      display: flex;
      align-items: center;
      gap: 8px;
      text-decoration: none;
      color: inherit;

      .logo-image {
        width: 32px;
        height: 32px;
      }

      .logo-text {
        font-size: 16px;
        font-weight: 600;
        color: #333;
      }
    }
  }

  .header-nav {
    flex: 1;
    display: flex;
    gap: 32px;
    margin-left: 60px;

    .nav-item {
      color: #666;
      text-decoration: none;
      transition: color 0.3s;

      &:hover,
      &.router-link-active {
        color: #409eff;
      }
    }
  }

  .header-user {
    display: flex;
    align-items: center;
    gap: 16px;

    .search-input {
      width: 240px;
    }

    .user-menu {
      .user-avatar {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;

        .user-name {
          font-size: 14px;
          color: #666;
        }
      }

      .dropdown-link {
        text-decoration: none;
        color: inherit;
      }
    }

    .auth-buttons {
      display: flex;
      gap: 12px;

      a {
        text-decoration: none;
        padding: 6px 16px;
        border-radius: 4px;
        font-size: 14px;
        transition: all 0.3s;

        &.btn-text {
          color: #409eff;

          &:hover {
            background: #f0f9ff;
          }
        }

        &.btn-primary {
          background: #409eff;
          color: white;

          &:hover {
            background: #66b1ff;
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .header {
    .header-container {
      padding: 0 12px;
      gap: 12px;
    }

    .header-logo .logo-text {
      display: none;
    }

    .header-nav {
      display: none;
    }

    .header-user {
      .search-input {
        width: 150px;
      }
    }
  }
}
</style>
