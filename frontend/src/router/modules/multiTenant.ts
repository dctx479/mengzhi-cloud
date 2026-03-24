import type { RouteRecordRaw } from 'vue-router'

// 企业管理路由
const enterpriseRoutes: RouteRecordRaw[] = [
  {
    path: '/enterprise',
    name: 'Enterprise',
    meta: { requiresAuth: true, role: 'enterprise_admin' },
    children: [
      {
        path: 'ai-config',
        name: 'EnterpriseAIConfig',
        component: () => import('@/views/enterprise/AIConfigView.vue'),
        meta: { title: 'AI配置管理' }
      },
      {
        path: 'audit-logs',
        name: 'EnterpriseAuditLogs',
        component: () => import('@/views/audit/AuditLogs.vue'),
        meta: { title: '审计日志' }
      }
    ]
  }
]

// 管理员路由
const adminRoutes: RouteRecordRaw[] = [
  {
    path: '/admin',
    name: 'Admin',
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/DashboardView.vue'),
        meta: { title: '管理员仪表盘' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UsersView.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'enterprises',
        name: 'AdminEnterprises',
        component: () => import('@/views/admin/EnterprisesView.vue'),
        meta: { title: '企业管理' }
      },
      {
        path: 'audit-logs',
        name: 'AdminAuditLogs',
        component: () => import('@/views/audit/AuditLogs.vue'),
        meta: { title: '审计日志' }
      }
    ]
  }
]

// 导出路由配置
export const multiTenantRoutes = [
  ...enterpriseRoutes,
  ...adminRoutes
]
