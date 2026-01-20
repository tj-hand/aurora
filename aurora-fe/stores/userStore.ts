/**
 * Pinia store for user management
 *
 * Uses Evoke (@/evoke) for authenticated API calls.
 * Orchestrates user CRUD through Aurora API which coordinates
 * Guardian (identity) and Mentor (tenant associations).
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api, API_PREFIX } from './api';
import type {
  User,
  UserCreate,
  UserUpdate,
  UserListResponse,
  PaginationParams,
  UserLevel,
} from './types';

export const useUserStore = defineStore('aurora-user', () => {
  // ==================== STATE ====================
  const users = ref<User[]>([]);
  const currentUser = ref<User | null>(null);
  const total = ref(0);
  const page = ref(1);
  const perPage = ref(20);
  const hasMore = ref(false);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ==================== GETTERS ====================

  const activeUsers = computed(() =>
    users.value.filter(u => u.is_active)
  );

  const inactiveUsers = computed(() =>
    users.value.filter(u => !u.is_active)
  );

  const adminUsers = computed(() =>
    users.value.filter(u => u.user_level === 'tenant_admin' && u.is_active)
  );

  const hasUser = computed(() => currentUser.value !== null);

  const userId = computed(() => currentUser.value?.id ?? null);

  // Group users by level
  const usersByLevel = computed(() => {
    const grouped: Record<UserLevel, User[]> = {
      tenant_admin: [],
      simple_user: [],
    };
    for (const user of users.value) {
      if (user.is_active) {
        grouped[user.user_level].push(user);
      }
    }
    return grouped;
  });

  // ==================== ACTIONS ====================

  async function fetchUsers(params: PaginationParams = {}) {
    loading.value = true;
    error.value = null;

    try {
      const queryParams: Record<string, string> = {};
      if (params.page) queryParams.page = String(params.page);
      if (params.per_page) queryParams.per_page = String(params.per_page);
      if (params.include_inactive) queryParams.include_inactive = 'true';

      const response = await api.get<UserListResponse>(
        `${API_PREFIX}/users`,
        { params: queryParams }
      );

      users.value = response.data.users;
      total.value = response.data.total;
      page.value = response.data.page;
      perPage.value = response.data.per_page;
      hasMore.value = response.data.has_more;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch users';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function fetchUser(id: string) {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.get<User>(
        `${API_PREFIX}/users/${id}`
      );

      return response.data;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch user';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function createUser(data: UserCreate) {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.post<User>(
        `${API_PREFIX}/users`,
        data
      );

      const user = response.data;
      users.value.push(user);
      total.value += 1;
      return user;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create user';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function updateUser(id: string, data: UserUpdate) {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.put<User>(
        `${API_PREFIX}/users/${id}`,
        data
      );

      const updated = response.data;

      // Update local state
      const index = users.value.findIndex(u => u.id === id);
      if (index !== -1) {
        users.value[index] = updated;
      }

      // Update current user if it's the one being edited
      if (currentUser.value?.id === id) {
        currentUser.value = updated;
      }

      return updated;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update user';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function deactivateUser(id: string) {
    loading.value = true;
    error.value = null;

    try {
      await api.delete(`${API_PREFIX}/users/${id}`);

      // Update local state - mark as inactive rather than removing
      const index = users.value.findIndex(u => u.id === id);
      if (index !== -1) {
        users.value[index] = { ...users.value[index], is_active: false };
      }

      // Clear current user if it's the deactivated one
      if (currentUser.value?.id === id) {
        currentUser.value = null;
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to deactivate user';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  function setCurrentUser(user: User | null) {
    currentUser.value = user;
  }

  function clearError() {
    error.value = null;
  }

  function reset() {
    users.value = [];
    currentUser.value = null;
    total.value = 0;
    page.value = 1;
    hasMore.value = false;
    error.value = null;
  }

  return {
    // State
    users,
    currentUser,
    total,
    page,
    perPage,
    hasMore,
    loading,
    error,
    // Getters
    activeUsers,
    inactiveUsers,
    adminUsers,
    hasUser,
    userId,
    usersByLevel,
    // Actions
    fetchUsers,
    fetchUser,
    createUser,
    updateUser,
    deactivateUser,
    setCurrentUser,
    clearError,
    reset,
  };
});
