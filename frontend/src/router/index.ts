import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresAuth: false, hideLayout: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { requiresAuth: false, hideLayout: true },
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/teams',
      name: 'teams',
      component: () => import('@/views/TeamsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('@/views/ProjectsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/projects/:id',
      name: 'project-detail',
      component: () => import('@/views/ProjectDetailView.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'project-overview',
          component: () => import('@/views/ProjectOverviewView.vue'),
        },
        {
          path: 'requirements',
          name: 'project-requirements',
          component: () => import('@/views/RequirementListView.vue'),
        },
        {
          path: 'tasks',
          name: 'project-tasks',
          component: () => import('@/views/ProjectTasksView.vue'),
        },
        {
          path: 'members',
          name: 'project-members',
          component: () => import('@/views/ProjectMembersView.vue'),
        },
        {
          path: 'settings',
          name: 'project-settings',
          component: () => import('@/views/ProjectSettingsView.vue'),
        },
      ],
    },
    {
      path: '/projects/:projectId/requirements/:reqId',
      name: 'requirement-detail',
      component: () => import('@/views/RequirementDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/projects/:projectId/requirements/:reqId/specs/:specId',
      name: 'specification-detail',
      component: () => import('@/views/SpecificationDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/projects/:projectId/requirements/:reqId/coverage',
      name: 'coverage-report',
      component: () => import('@/views/CoverageReportView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
})

export default router
