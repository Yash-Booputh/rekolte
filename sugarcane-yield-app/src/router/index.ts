import { createRouter, createWebHistory } from '@ionic/vue-router'
import { RouteRecordRaw } from 'vue-router'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
  },
  {
    path: '/regions',
    name: 'Regions',
    component: () => import('@/views/RegionDetailView.vue'),
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/HistoricalDataView.vue'),
  },
  {
    path: '/compare',
    name: 'Compare',
    component: () => import('@/views/ModelComparisonView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('rekolte_token')
  if (!to.meta.public && !token) {
    return '/login'
  }
})

export default router
