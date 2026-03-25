import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { requiresAuth: false },
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Home.vue'),
        meta: { requiresAuth: false },
      },
      // 产品相关
      {
        path: 'products',
        name: 'ProductList',
        component: () => import('@/views/products/ProductList.vue'),
        meta: { requiresAuth: false },
      },
      {
        path: 'products/categories',
        name: 'ProductCategories',
        component: () => import('@/views/products/ProductList.vue'),
        meta: { requiresAuth: false },
      },
      {
        path: 'products/:id',
        name: 'ProductDetail',
        component: () => import('@/views/products/ProductDetail.vue'),
        meta: { requiresAuth: false },
      },
      // AI 对话
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/chat/ChatPage.vue'),
        meta: { requiresAuth: true },
      },
      // 内容生成工作台
      {
        path: 'content-studio',
        name: 'ContentStudio',
        component: () => import('@/views/ContentStudio.vue'),
        meta: { requiresAuth: true },
      },
      // 用户中心
      {
        path: 'user',
        component: () => import('@/views/user/UserCenter.vue'),
        redirect: '/user/profile',
        meta: { requiresAuth: true },
        children: [
          {
            path: 'profile',
            name: 'UserProfile',
            component: () => import('@/views/user/Profile.vue'),
          },
          {
            path: 'orders',
            name: 'UserOrders',
            component: () => import('@/views/user/Orders.vue'),
          },
          {
            path: 'quota',
            name: 'UserQuota',
            component: () => import('@/views/user/Quota.vue'),
          },
          {
            path: 'settings',
            name: 'UserSettings',
            component: () => import('@/views/user/Settings.vue'),
          },
          {
            path: 'security',
            name: 'UserSecurity',
            component: () => import('@/views/user/Security.vue'),
          },
        ],
      },
      // 管理后台
      {
        path: 'admin',
        redirect: '/admin/dashboard',
        meta: { requiresAuth: true, requiresAdmin: true },
        children: [
          {
            path: 'dashboard',
            name: 'AdminDashboard',
            component: () => import('@/views/admin/DashboardView.vue'),
          },
          {
            path: 'users',
            name: 'AdminUsers',
            component: () => import('@/views/admin/UsersView.vue'),
          },
          {
            path: 'enterprises',
            name: 'AdminEnterprises',
            component: () => import('@/views/admin/EnterprisesView.vue'),
          },
        ],
      },
      // 企业配置
      {
        path: 'enterprise',
        redirect: '/enterprise/ai-config',
        meta: { requiresAuth: true, requiresAdmin: true },
        children: [
          {
            path: 'ai-config',
            name: 'AIConfig',
            component: () => import('@/views/enterprise/AIConfigView.vue'),
          },
          {
            path: 'model-config',
            name: 'ModelConfig',
            component: () => import('@/views/enterprise/ModelConfig.vue'),
          },
        ],
      },
      // 审计日志
      {
        path: 'audit',
        name: 'AuditLogs',
        component: () => import('@/views/audit/AuditLogs.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      // 计费
      {
        path: 'billing',
        redirect: '/billing/overview',
        meta: { requiresAuth: true },
        children: [
          {
            path: 'overview',
            name: 'BillingOverview',
            component: () => import('@/views/billing/BillingOverview.vue'),
          },
          {
            path: 'records',
            name: 'BillingRecords',
            component: () => import('@/views/billing/BillingRecords.vue'),
          },
          {
            path: 'invoices',
            name: 'BillingInvoices',
            component: () => import('@/views/billing/Invoices.vue'),
          },
        ],
      },
      // SLA 仪表板
      {
        path: 'sla',
        name: 'SLADashboard',
        component: () => import('@/views/sla/SLADashboard.vue'),
        meta: { requiresAuth: true },
      },
    ],
  },
  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore()

  // 仅在首次加载时初始化用户状态
  if (!userStore.user && !userStore.isLoggedIn) {
    userStore.restoreFromStorage()
  }

  // 检查是否需要认证
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some((record) => record.meta.requiresAdmin)

  if (requiresAuth && !userStore.isLoggedIn) {
    // 验证 redirect 目标安全性：必须以 / 开头且不含协议前缀
    const redirect = to.fullPath
    const safeRedirect = redirect.startsWith('/') && !redirect.includes('://') ? redirect : '/'
    next({ path: '/login', query: { redirect: safeRedirect } })
  } else if (requiresAdmin && !userStore.isAdmin) {
    next('/')
  } else if (!requiresAuth && userStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
    next('/')
  } else {
    next()
  }
})

export default router
