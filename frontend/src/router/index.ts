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
        component: () => import('@/views/products/ProductList.vue'), // 暂时复用产品列表
        meta: { requiresAuth: false },
      },
      {
        path: 'products/:id',
        name: 'ProductDetail',
        component: () => import('@/views/products/ProductDetail.vue'),
        meta: { requiresAuth: false },
      },
      // 对话相关
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
        meta: { requiresAuth: true },
        children: [
          {
            path: 'profile',
            name: 'UserProfile',
            component: () => import('@/views/user/Profile.vue'),
            meta: { requiresAuth: true },
          },
          {
            path: 'orders',
            name: 'UserOrders',
            component: () => import('@/views/user/Orders.vue'),
            meta: { requiresAuth: true },
          },
          {
            path: 'quota',
            name: 'UserQuota',
            component: () => import('@/views/user/Quota.vue'),
            meta: { requiresAuth: true },
          },
          {
            path: 'settings',
            name: 'UserSettings',
            component: () => import('@/views/user/Settings.vue'),
            meta: { requiresAuth: true },
          },
          {
            path: 'security',
            name: 'UserSecurity',
            component: () => import('@/views/user/Security.vue'),
            meta: { requiresAuth: true },
          },
          {
            path: 'logout',
            name: 'UserLogout',
            component: () => import('@/views/user/Logout.vue'),
            meta: { requiresAuth: true },
          },
        ],
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
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  // 仅在首次加载时初始化用户状态
  if (!userStore.user && !userStore.isLoggedIn) {
    userStore.restoreFromStorage()
  }

  // 检查是否需要认证
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  if (requiresAuth && !userStore.isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if (!requiresAuth && userStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
    next('/')
  } else {
    next()
  }
})

export default router
