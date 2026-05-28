<template>
  <div class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <span v-if="!collapsed" class="sidebar-title">导航菜单</span>
      <el-icon class="collapse-btn" @click="handleCollapse">
        <component :is="collapsed ? ArrowRight : ArrowLeft" />
      </el-icon>
    </div>

    <el-menu
      :default-active="activeMenu"
      :collapse="collapsed"
      active-text-color="#0d9668"
      router
    >
      <el-menu-item index="/">
        <el-icon><House /></el-icon>
        <template #title>首页</template>
      </el-menu-item>

      <el-sub-menu index="products-group">
        <template #title>
          <el-icon><Goods /></el-icon>
          <span>产品中心</span>
        </template>
        <el-menu-item index="/products">产品列表</el-menu-item>
        <el-menu-item index="/products/categories">分类浏览</el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/chat">
        <el-icon><ChatDotRound /></el-icon>
        <template #title>AI 对话</template>
      </el-menu-item>

      <el-menu-item index="/content-studio">
        <el-icon><Edit /></el-icon>
        <template #title>内容工作台</template>
      </el-menu-item>

      <!-- 已登录用户菜单 -->
      <template v-if="userStore.isLoggedIn">
        <el-sub-menu index="user-group">
          <template #title>
            <el-icon><User /></el-icon>
            <span>用户中心</span>
          </template>
          <el-menu-item index="/user/profile">个人资料</el-menu-item>
          <el-menu-item index="/user/orders">订单历史</el-menu-item>
          <el-menu-item index="/user/quota">配额管理</el-menu-item>
          <el-menu-item index="/user/settings">偏好设置</el-menu-item>
          <el-menu-item index="/user/security">安全中心</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="billing-group">
          <template #title>
            <el-icon><Wallet /></el-icon>
            <span>计费管理</span>
          </template>
          <el-menu-item index="/billing/overview">计费总览</el-menu-item>
          <el-menu-item index="/billing/records">消费记录</el-menu-item>
          <el-menu-item index="/billing/invoices">发票管理</el-menu-item>
        </el-sub-menu>

        <el-menu-item v-if="userStore.isAdminOrEnterpriseAdmin" index="/enterprise/ai-config">
          <el-icon><Cpu /></el-icon>
          <template #title>AI 配置</template>
        </el-menu-item>

        <el-menu-item v-if="userStore.isAdmin" index="/audit">
          <el-icon><Document /></el-icon>
          <template #title>审计日志</template>
        </el-menu-item>

        <el-menu-item v-if="userStore.isAdmin" index="/sla">
          <el-icon><TrendCharts /></el-icon>
          <template #title>SLA 监控</template>
        </el-menu-item>

        <el-menu-item index="/kefu">
          <el-icon><Service /></el-icon>
          <template #title>客服中心</template>
        </el-menu-item>

        <el-menu-item index="/kefu/tickets">
          <el-icon><Tickets /></el-icon>
          <template #title>我的工单</template>
        </el-menu-item>
      </template>

      <!-- 管理员菜单 -->
      <el-sub-menu v-if="userStore.isAdmin" index="admin-group">
        <template #title>
          <el-icon><Setting /></el-icon>
          <span>系统管理</span>
        </template>
        <el-menu-item index="/admin/dashboard">管理面板</el-menu-item>
        <el-menu-item index="/admin/users">用户管理</el-menu-item>
        <el-menu-item index="/admin/enterprises">企业管理</el-menu-item>
        <el-menu-item index="/admin/ai-media">AI 媒体生成</el-menu-item>
        <el-menu-item index="/admin/jd-import">京东商品导入</el-menu-item>
        <el-menu-item index="/admin/taobao-import">淘宝联盟导入</el-menu-item>
        <el-menu-item index="/admin/templates">内容模板管理</el-menu-item>
      </el-sub-menu>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  House,
  Goods,
  ChatDotRound,
  Edit,
  User,
  Wallet,
  Setting,
  Document,
  TrendCharts,
  ArrowLeft,
  ArrowRight,
  Cpu,
  Service,
  Tickets,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()
const collapsed = ref(false)

const activeMenu = computed(() => route.path)

const handleCollapse = () => {
  collapsed.value = !collapsed.value
}
</script>

<style scoped lang="scss">
.sidebar {
  width: $sidebar-width;
  background: $color-bg-card;
  border-right: 1px solid $color-border-light;
  transition: width 0.3s;
  height: calc(100vh - #{$header-height});
  overflow-y: auto;

  &.collapsed {
    width: $sidebar-collapsed-width;

    .sidebar-header {
      .sidebar-title {
        display: none;
      }
    }
  }

  .sidebar-header {
    padding: $spacing-md;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid $color-border-light;

    .sidebar-title {
      font-size: 14px;
      font-weight: 600;
      color: $color-text-primary;
    }

    .collapse-btn {
      cursor: pointer;
      color: $color-text-secondary;
      transition: color 0.3s;

      &:hover {
        color: $color-primary;
      }
    }
  }

  :deep(.el-menu) {
    border-right: none;
    background: $color-bg-card;

    .el-menu-item,
    .el-sub-menu__title {
      color: $color-text-regular;
      transition: all 0.3s;

      &:hover {
        background: $color-primary-light !important;
      }

      &.is-active {
        position: relative;
        background: $color-primary-light !important;
        color: $color-primary !important;
        font-weight: 500;

        &::before {
          content: '';
          position: absolute;
          left: 0;
          top: 8px;
          bottom: 8px;
          width: 3px;
          border-radius: 0 2px 2px 0;
          background: $color-primary;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: $header-height;
    height: calc(100vh - #{$header-height});
    z-index: 99;
    box-shadow: $shadow-lg;

    &.collapsed {
      width: 0;
      overflow: hidden;
    }
  }
}
</style>
