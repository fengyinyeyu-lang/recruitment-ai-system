import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/home',
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { title: '系统首页', icon: 'HomeFilled' }
      },
      {
        path: 'visualization',
        name: 'Visualization',
        component: () => import('@/views/Visualization.vue'),
        meta: { title: '数据可视化大屏', icon: 'DataAnalysis' }
      },
      {
        path: 'wordcloud',
        name: 'WordCloud',
        component: () => import('@/views/WordCloud.vue'),
        meta: { title: '岗位词云与需求', icon: 'Cloudy' }
      },
      {
        path: 'ml',
        name: 'MLAnalysis',
        component: () => import('@/views/MLAnalysis.vue'),
        meta: { title: '机器学习聚类分析', icon: 'Cpu' }
      },
      {
        path: 'ai',
        name: 'AIAssistant',
        component: () => import('@/views/AIAssistant.vue'),
        meta: { title: '智能求职助手', icon: 'ChatDotRound' }
      },
      {
        path: 'resume',
        name: 'ResumeMatch',
        component: () => import('@/views/ResumeMatch.vue'),
        meta: { title: 'PDF简历推荐', icon: 'Document' }
      },
      {
        path: 'company',
        name: 'CompanyProfile',
        component: () => import('@/views/CompanyProfile.vue'),
        meta: { title: '企业深度画像', icon: 'OfficeBuilding' }
      },
      {
        path: 'report',
        name: 'ReportExport',
        component: () => import('@/views/ReportExport.vue'),
        meta: { title: '分析报告导出', icon: 'Download' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/home')
  } else {
    next()
  }
})

export default router
