<template>
  <div class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <span v-if="!collapsed" class="sidebar-title">菜单</span>
      <el-icon class="collapse-btn" @click="handleCollapse">
        <component :is="collapsed ? ArrowRight : ArrowLeft" />
      </el-icon>
    </div>

    <el-menu
      :collapse="collapsed"
      active-text-color="#409eff"
      router
      @select="handleMenuSelect"
    >
      <el-menu-item index="/dashboard">
        <el-icon><House /></el-icon>
        <template #title>仪表板</template>
      </el-menu-item>

      <el-sub-menu index="products">
        <template #title>
          <el-icon><Goods /></el-icon>
          <span>产品管理</span>
        </template>
        <el-menu-item index="/products">产品列表</el-menu-item>
        <el-menu-item index="/products/categories">分类管理</el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/chat">
        <el-icon><ChatDotRound /></el-icon>
        <template #title>AI对话</template>
      </el-menu-item>

      <el-sub-menu index="user" v-if="userStore.isLoggedIn">
        <template #title>
          <el-icon><User /></el-icon>
          <span>用户</span>
        </template>
        <el-menu-item index="/user/profile">个人中心</el-menu-item>
        <el-menu-item index="/user/settings">账号设置</el-menu-item>
      </el-sub-menu>

      <el-sub-menu index="admin" v-if="userStore.isAdmin">
        <template #title>
          <el-icon><Setting /></el-icon>
          <span>系统管理</span>
        </template>
        <el-menu-item index="/admin/users">用户管理</el-menu-item>
        <el-menu-item index="/admin/products">产品管理</el-menu-item>
        <el-menu-item index="/admin/logs">操作日志</el-menu-item>
      </el-sub-menu>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  House,
  Goods,
  ChatDotRound,
  User,
  Setting,
  ArrowLeft,
  ArrowRight,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const collapsed = ref(false)

const handleCollapse = () => {
  collapsed.value = !collapsed.value
}

const handleMenuSelect = () => {
  // Menu selection handled by router
}
</script>

<style scoped lang="scss">
.sidebar {
  width: 200px;
  background: #f5f7fa;
  border-right: 1px solid #e4e7eb;
  transition: width 0.3s;
  height: calc(100vh - 64px);
  overflow-y: auto;

  &.collapsed {
    width: 64px;

    .sidebar-header {
      .sidebar-title {
        display: none;
      }
    }
  }

  .sidebar-header {
    padding: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #e4e7eb;

    .sidebar-title {
      font-size: 14px;
      font-weight: 600;
      color: #333;
    }

    .collapse-btn {
      cursor: pointer;
      color: #666;
      transition: color 0.3s;

      &:hover {
        color: #409eff;
      }
    }
  }

  :deep(.el-menu) {
    border-right: none;
    background: #f5f7fa;

    .el-menu-item,
    .el-sub-menu__title {
      color: #606266;
      transition: all 0.3s;

      &:hover {
        background: #e9ecef !important;
      }

      &.is-active {
        background: #e9ecef !important;
        color: #409eff !important;
      }
    }
  }
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 64px;
    height: calc(100vh - 64px);
    z-index: 99;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);

    &.collapsed {
      width: 0;
      overflow: hidden;
    }
  }
}
</style>
