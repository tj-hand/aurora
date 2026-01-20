/**
 * Composable for user management operations
 *
 * Provides user CRUD, filtering, and search functionality
 * with reactive state management.
 */
import { computed, watch, ref } from 'vue';
import { useUserStore } from '../stores/userStore';
import type { User, UserCreate, UserUpdate, PaginationParams, UserLevel } from '../stores/types';

export interface UseUserManagementOptions {
  /** Auto-load users on mount */
  autoLoad?: boolean;
  /** Include inactive users in list */
  includeInactive?: boolean;
  /** Items per page */
  perPage?: number;
}

export function useUserManagement(options: UseUserManagementOptions = {}) {
  const {
    autoLoad = true,
    includeInactive = false,
    perPage = 20,
  } = options;

  const userStore = useUserStore();

  // Local state
  const searchQuery = ref('');
  const filterLevel = ref<UserLevel | 'all'>('all');
  const showInactive = ref(includeInactive);

  // ==================== COMPUTED ====================

  /** Current selected user */
  const user = computed(() => userStore.currentUser);

  /** Current user ID */
  const userId = computed(() => userStore.userId);

  /** Whether a user is selected */
  const hasUser = computed(() => userStore.hasUser);

  /** All users */
  const users = computed(() => userStore.users);

  /** Active users only */
  const activeUsers = computed(() => userStore.activeUsers);

  /** Admin users */
  const adminUsers = computed(() => userStore.adminUsers);

  /** Users grouped by level */
  const usersByLevel = computed(() => userStore.usersByLevel);

  /** Pagination info */
  const pagination = computed(() => ({
    total: userStore.total,
    page: userStore.page,
    perPage: userStore.perPage,
    hasMore: userStore.hasMore,
  }));

  /** Loading state */
  const loading = computed(() => userStore.loading);

  /** Error state */
  const error = computed(() => userStore.error);

  /** Filtered and searched users */
  const filteredUsers = computed(() => {
    let result = showInactive.value ? users.value : activeUsers.value;

    // Filter by level
    if (filterLevel.value !== 'all') {
      result = result.filter(u => u.user_level === filterLevel.value);
    }

    // Search by email
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase();
      result = result.filter(u =>
        u.email.toLowerCase().includes(query)
      );
    }

    return result;
  });

  // ==================== METHODS ====================

  /**
   * Load users from API
   */
  async function loadUsers(params: PaginationParams = {}) {
    await userStore.fetchUsers({
      per_page: perPage,
      include_inactive: showInactive.value,
      ...params,
    });
  }

  /**
   * Load next page of users
   */
  async function loadNextPage() {
    if (!userStore.hasMore || userStore.loading) return;

    await loadUsers({
      page: userStore.page + 1,
    });
  }

  /**
   * Refresh the current user list
   */
  async function refresh() {
    await loadUsers({ page: 1 });
  }

  /**
   * Select a user
   */
  async function selectUser(userOrId: User | string | null) {
    if (userOrId === null) {
      userStore.setCurrentUser(null);
      return;
    }

    let targetUser: User | null = null;

    if (typeof userOrId === 'string') {
      // Find in local store first
      targetUser = users.value.find(u => u.id === userOrId) ?? null;
      // Fetch if not found
      if (!targetUser) {
        targetUser = await userStore.fetchUser(userOrId);
      }
    } else {
      targetUser = userOrId;
    }

    if (targetUser) {
      userStore.setCurrentUser(targetUser);
    }
  }

  /**
   * Clear the current user selection
   */
  function clearUser() {
    userStore.setCurrentUser(null);
  }

  /**
   * Create a new user
   */
  async function createUser(data: UserCreate): Promise<User> {
    const newUser = await userStore.createUser(data);
    return newUser;
  }

  /**
   * Update an existing user
   */
  async function updateUser(id: string, data: UserUpdate): Promise<User> {
    const updated = await userStore.updateUser(id, data);
    return updated;
  }

  /**
   * Deactivate a user (soft delete)
   */
  async function deactivateUser(id: string): Promise<void> {
    await userStore.deactivateUser(id);
  }

  /**
   * Set search query
   */
  function setSearch(query: string) {
    searchQuery.value = query;
  }

  /**
   * Set level filter
   */
  function setLevelFilter(level: UserLevel | 'all') {
    filterLevel.value = level;
  }

  /**
   * Toggle showing inactive users
   */
  function toggleInactive() {
    showInactive.value = !showInactive.value;
  }

  /**
   * Clear all filters
   */
  function clearFilters() {
    searchQuery.value = '';
    filterLevel.value = 'all';
  }

  /**
   * Clear error state
   */
  function clearError() {
    userStore.clearError();
  }

  // ==================== LIFECYCLE ====================

  // Auto-load on mount if enabled
  if (autoLoad) {
    loadUsers();
  }

  // Reload when showInactive changes
  watch(showInactive, () => {
    loadUsers({ page: 1 });
  });

  return {
    // State
    user,
    userId,
    hasUser,
    users,
    activeUsers,
    adminUsers,
    usersByLevel,
    filteredUsers,
    pagination,
    loading,
    error,
    searchQuery,
    filterLevel,
    showInactive,
    // Methods
    loadUsers,
    loadNextPage,
    refresh,
    selectUser,
    clearUser,
    createUser,
    updateUser,
    deactivateUser,
    setSearch,
    setLevelFilter,
    toggleInactive,
    clearFilters,
    clearError,
    // Store access
    store: userStore,
  };
}

export type UseUserManagementReturn = ReturnType<typeof useUserManagement>;
