import { createRouter, createWebHistory, RouterView, type RouteComponent } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { h } from 'vue'

const PassThrough: RouteComponent = { render: () => h(RouterView) }

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
      // AI 对话（公开，提示登录引导）
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/chat/ChatPage.vue'),
        meta: { requiresAuth: false },
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
        component: PassThrough,
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
            meta: { requiresAuth: false },
          },
          {
            path: 'quota',
            name: 'UserQuota',
            component: () => import('@/views/user/Quota.vue'),
            meta: { requiresAuth: false },
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
        component: PassThrough,
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
          {
            path: 'ai-media',
            name: 'AdminAIMedia',
            component: () => import('@/views/admin/AIMediaView.vue'),
            meta: { requiresAuth: true, requiresAdmin: true },
          },
          {
            path: 'jd-import',
            name: 'AdminJDImport',
            component: () => import('@/views/admin/JDImportView.vue'),
            meta: { requiresAuth: true, requiresAdmin: true },
          },
          {
            path: 'taobao-import',
            name: 'AdminTaobaoImport',
            component: () => import('@/views/admin/TaobaoImportView.vue'),
            meta: { requiresAuth: true, requiresAdmin: true },
          },
          {
            path: 'templates',
            name: 'AdminTemplates',
            component: () => import('@/views/admin/TemplatesView.vue'),
            meta: { requiresAuth: true, requiresAdmin: true },
          },
        ],
      },
      // 企业配置
      {
        path: 'enterprise',
        redirect: '/enterprise/ai-config',
        component: PassThrough,
        meta: { requiresAuth: true, requiresEnterpriseAdmin: true },
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
        component: PassThrough,
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
      // 智能客服
      {
        path: 'kefu',
        name: 'KefuChat',
        component: () => import('@/views/kefu/KefuChatView.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'kefu/tickets',
        name: 'KefuTickets',
        component: () => import('@/views/kefu/KefuTicketView.vue'),
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
  const requiresEnterpriseAdmin = to.matched.some((record) => record.meta.requiresEnterpriseAdmin)
  const requiredRole = to.matched.find((record) => record.meta.role)?.meta.role as string | undefined

  if (requiresAuth && !userStore.isLoggedIn) {
    // 验证 redirect 目标安全性：必须以 / 开头且不含协议前缀
    const redirect = to.fullPath
    const safeRedirect = redirect.startsWith('/') && !redirect.includes('://') ? redirect : '/'
    next({ path: '/login', query: { redirect: safeRedirect } })
  } else if (requiresAdmin && !userStore.isAdmin) {
    // 系统管理员权限检查
    next('/')
  } else if (requiresEnterpriseAdmin && !userStore.isAdminOrEnterpriseAdmin) {
    // 企业管理员权限检查（系统管理员也可通过）
    next('/')
  } else if (requiredRole && userStore.userRole !== requiredRole) {
    // 角色级权限检查：admin 拥有最高权限，可访问所有角色路由
    if (userStore.userRole !== 'admin') {
      next('/')
      return
    }
    next()
  } else if (!requiresAuth && userStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
    // 已登录用户不能访问登录/注册页
    next('/')
  } else {
    next()
  }
})

// 路由懒加载错误处理
router.onError((error) => {
  // 捕获chunk加载失败等动态导入错误
  if (/Loading chunk \d+ failed|failed to fetch/i.test(error.message)) {
    window.location.reload()
  }
})


export default router
