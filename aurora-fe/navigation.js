/**
 * Aurora Navigation
 * 
 * Defines navigation menu items for Aurora module.
 * These are automatically registered by Infinity's navigation system.
 */

export default {
  // Main menu item
  main: {
    id: 'aurora-users',
    label: 'Users',
    icon: 'users',
    route: '/users',
    permission: 'aurora:users:read',
    order: 30  // After Tenants (mentor)
  },
  
  // Sub-menu items (optional)
  items: [
    {
      id: 'aurora-users-list',
      label: 'All Users',
      icon: 'list',
      route: '/users',
      permission: 'aurora:users:read'
    },
    {
      id: 'aurora-users-create',
      label: 'Add User',
      icon: 'user-plus',
      route: '/users/new',
      permission: 'aurora:users:create'
    }
  ]
}
