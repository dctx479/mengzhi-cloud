<template>
  <div class="header">
    <div class="header-container">
      <!-- Logo -->
      <div class="header-logo">
        <router-link to="/" class="logo-link">
          <span class="logo-mark"></span>
          <span class="logo-text">蒙智云</span>
        </router-link>
      </div>

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
  background: $color-bg-card;
  border-bottom: 1px solid $color-border-light;
  box-shadow: $shadow-sm;
  position: sticky;
  top: 0;
  z-index: 100;

  .header-container {
    padding: 0 $spacing-lg;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: $header-height;
  }

  .header-logo {
    .logo-link {
      display: flex;
      align-items: center;
      gap: 10px;
      text-decoration: none;
      color: inherit;

      .logo-mark {
        width: 28px;
        height: 28px;
        background: linear-gradient(135deg, $color-primary, $color-primary-dark);
        border-radius: $radius-sm;
        flex-shrink: 0;
      }

      .logo-text {
        font-size: 18px;
        font-weight: 700;
        color: $color-primary;
        letter-spacing: 1px;
      }
    }
  }

  .header-user {
    display: flex;
    align-items: center;
    gap: $spacing-md;

    .search-input {
      width: 240px;

      :deep(.el-input__wrapper) {
        border-radius: 20px;
        background: $color-bg-page;
      }
    }

    .user-menu {
      .user-avatar {
        display: flex;
        align-items: center;
        gap: $spacing-sm;
        cursor: pointer;

        .user-name {
          font-size: 14px;
          color: $color-text-regular;
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
        border-radius: 20px;
        font-size: 14px;
        transition: all 0.3s;

        &.btn-text {
          color: $color-primary;

          &:hover {
            background: $color-primary-light;
          }
        }

        &.btn-primary {
          background: $color-primary;
          color: white;

          &:hover {
            background: $color-primary-dark;
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

    .header-user {
      .search-input {
        width: 150px;
      }
    }
  }
}
</style>
