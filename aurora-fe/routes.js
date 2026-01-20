/**
 * Aurora Routes
 * 
 * Defines Vue Router routes for Aurora module.
 * These are automatically registered by Infinity.
 */

export default [
  {
    path: '/users',
    name: 'aurora-users',
    component: () => import('@/aurora/views/UserList.vue'),
    meta: {
      requiresAuth: true,
      permission: 'aurora:users:read'
    }
  },
  {
    path: '/users/new',
    name: 'aurora-user-create',
    component: () => import('@/aurora/views/UserForm.vue'),
    meta: {
      requiresAuth: true,
      permission: 'aurora:users:create'
    }
  },
  {
    path: '/users/:id',
    name: 'aurora-user-detail',
    component: () => import('@/aurora/views/UserDetail.vue'),
    meta: {
      requiresAuth: true,
      permission: 'aurora:users:read'
    }
  },
  {
    path: '/users/:id/edit',
    name: 'aurora-user-edit',
    component: () => import('@/aurora/views/UserForm.vue'),
    meta: {
      requiresAuth: true,
      permission: 'aurora:users:update'
    }
  }
]
