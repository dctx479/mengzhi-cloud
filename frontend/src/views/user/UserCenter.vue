<template>
  <div class="user-center">
    <!-- 侧边栏导航 -->
    <el-aside class="user-sidebar" width="200px">
      <div class="sidebar-header">
        <div class="user-avatar">
          <el-avatar :src="userStore.user?.avatar" :size="64" />
        </div>
        <div class="user-info">
          <div class="username">{{ userStore.user?.username }}</div>
          <div class="user-role">{{ getRoleName(userStore.user?.role) }}</div>
        </div>
      </div>

      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        @select="handleMenuSelect"
        router
      >
        <el-menu-item index="/user/profile">
          <el-icon><User /></el-icon>
          <span>个人资料</span>
        </el-menu-item>

        <el-menu-item index="/user/orders">
          <el-icon><ShoppingCart /></el-icon>
          <span>订单历史</span>
        </el-menu-item>

        <el-menu-item index="/user/quota">
          <el-icon><DataAnalysis /></el-icon>
          <span>配额管理</span>
        </el-menu-item>

        <el-menu-item index="/user/settings">
          <el-icon><Setting /></el-icon>
          <span>偏好设置</span>
        </el-menu-item>

        <el-menu-item index="/user/security">
          <el-icon><Lock /></el-icon>
          <span>安全中心</span>
        </el-menu-item>

        <el-divider />

        <el-menu-item index="logout" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主要内容区域 -->
    <el-main class="user-main">
      <div class="main-header">
        <el-breadcrumb :separator-icon="ArrowRight" class="header-breadcrumb">
          <el-breadcrumb-item>用户中心</el-breadcrumb-item>
          <el-breadcrumb-item>{{ getCurrentPageTitle() }}</el-breadcrumb-item>
        </el-breadcrumb>
      </div>

      <div class="main-content">
        <router-view />
      </div>
    </el-main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  ShoppingCart,
  DataAnalysis,
  Setting,
  Lock,
  SwitchButton,
  ArrowRight,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => {
  return route.path || '/user/profile'
})

const pageTitles: Record<string, string> = {
  '/user/profile': '个人资料',
  '/user/orders': '订单历史',
  '/user/quota': '配额管理',
  '/user/settings': '偏好设置',
  '/user/security': '安全中心',
}

const getRoleName = (role?: string): string => {
  const roleMap: Record<string, string> = {
    user: '普通用户',
    admin: '管理员',
    manager: '经理',
  }
  return roleMap[role || 'user'] || '用户'
}

const getCurrentPageTitle = (): string => {
  return pageTitles[route.path] || '用户中心'
}

const handleMenuSelect = (index: string) => {
  if (index !== 'logout') {
    router.push(index)
  }
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    await userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}
</script>

<style scoped lang="scss">
.user-center {
  display: flex;
  min-height: calc(100vh - 60px); // 减去头部高度
  background-color: #f5f7fa;

  :deep(.el-aside) {
    background-color: #fff;
    border-right: 1px solid #f0f0f0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    overflow-y: auto;
    position: sticky;
    top: 60px;
    max-height: calc(100vh - 60px);
  }

  :deep(.el-main) {
    padding: 0;
  }

  .user-sidebar {
    .sidebar-header {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 20px 12px;
      border-bottom: 1px solid #f0f0f0;

      .user-avatar {
        margin-bottom: 12px;

        :deep(.el-avatar) {
          border: 2px solid #409eff;
        }
      }

      .user-info {
        text-align: center;
        width: 100%;

        .username {
          font-size: 14px;
          font-weight: 600;
          color: #333;
          margin-bottom: 4px;
          word-break: break-all;
        }

        .user-role {
          font-size: 12px;
          color: #909399;
        }
      }
    }

    .sidebar-menu {
      border: none;
      padding: 8px 0;

      :deep(.el-menu-item) {
        height: 44px;
        line-height: 44px;
        padding: 0 16px;
        margin: 4px 8px;
        border-radius: 4px;

        &:hover {
          background-color: #f5f7fa;
        }

        &.is-active {
          background-color: #e6f7ff;
          color: #409eff;

          .el-icon {
            color: #409eff;
          }
        }
      }

      .el-icon {
        margin-right: 8px;
        font-size: 16px;
      }

      span {
        font-size: 14px;
      }
    }

    :deep(.el-divider) {
      margin: 8px 0;
      border-color: #f0f0f0;
    }
  }

  .user-main {
    flex: 1;
    padding: 24px;

    .main-header {
      margin-bottom: 24px;
      padding: 16px;
      background-color: #fff;
      border-radius: 4px;
      border-bottom: 1px solid #f0f0f0;

      .header-breadcrumb {
        :deep(.el-breadcrumb__item) {
          font-size: 14px;

          &:last-child span {
            font-weight: 600;
            color: #409eff;
          }
        }
      }
    }

    .main-content {
      background-color: transparent;
    }
  }
}

@media (max-width: 768px) {
  .user-center {
    flex-direction: column;

    .user-sidebar {
      width: 100% !important;
      max-height: auto;
      position: relative;
      top: auto;

      .sidebar-menu {
        display: flex;
        gap: 8px;
        padding: 8px;
        overflow-x: auto;

        :deep(.el-menu-item) {
          flex-shrink: 0;
          min-width: auto;
          white-space: nowrap;
        }
      }
    }

    .user-main {
      padding: 16px;

      .main-header {
        padding: 12px;
        margin-bottom: 16px;
      }
    }
  }
}

@media (max-width: 576px) {
  .user-center {
    .user-sidebar {
      .sidebar-header {
        padding: 16px 12px;

        .user-avatar {
          :deep(.el-avatar) {
            width: 48px;
            height: 48px;
            line-height: 48px;
          }
        }

        .user-info {
          .username {
            font-size: 13px;
          }

          .user-role {
            font-size: 11px;
          }
        }
      }

      .sidebar-menu {
        :deep(.el-menu-item) {
          height: 40px;
          line-height: 40px;
          padding: 0 12px;
          margin: 2px 4px;
          font-size: 12px;

          .el-icon {
            font-size: 14px;
          }
        }
      }
    }

    .user-main {
      padding: 12px;

      .main-header {
        padding: 10px;
        margin-bottom: 12px;

        :deep(.el-breadcrumb__item) {
          font-size: 12px;
        }
      }
    }
  }
}
</style>
