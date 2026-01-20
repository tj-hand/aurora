<script setup lang="ts">
/**
 * User Manager Component
 *
 * Full CRUD interface for managing users.
 * Includes list, create, edit, and deactivate functionality.
 *
 * STYLING: Uses scoped fallback CSS for Vibes independence.
 * Tailwind classes preserved for when Vibes is deployed.
 */
import { ref, computed, onMounted } from 'vue';
import { useUserStore } from '../../stores/userStore';
import { useUserManagement } from '../../composables/useUserManagement';
import type { User, UserCreate, UserUpdate, UserLevel } from '../../stores/types';

const store = useUserStore();
const {
  filteredUsers,
  loading,
  error,
  searchQuery,
  filterLevel,
  showInactive,
  setSearch,
  setLevelFilter,
  toggleInactive,
  refresh,
} = useUserManagement({ autoLoad: true });

// UI State
const showCreateModal = ref(false);
const showEditModal = ref(false);
const showDeactivateConfirm = ref(false);
const editingUser = ref<User | null>(null);
const deactivatingUser = ref<User | null>(null);

// Form state
const formData = ref<UserCreate & { is_active?: boolean }>({
  email: '',
  user_level: 'simple_user',
});
const formErrors = ref<Record<string, string>>({});

const userLevelOptions: { value: UserLevel; label: string }[] = [
  { value: 'simple_user', label: 'Simple User' },
  { value: 'tenant_admin', label: 'Tenant Admin' },
];

function resetForm() {
  formData.value = {
    email: '',
    user_level: 'simple_user',
  };
  formErrors.value = {};
}

function validateForm(): boolean {
  formErrors.value = {};

  if (!formData.value.email.trim()) {
    formErrors.value.email = 'Email is required';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.value.email)) {
    formErrors.value.email = 'Invalid email format';
  }

  if (!formData.value.user_level) {
    formErrors.value.user_level = 'User level is required';
  }

  return Object.keys(formErrors.value).length === 0;
}

function openCreateModal() {
  resetForm();
  editingUser.value = null;
  showCreateModal.value = true;
}

function openEditModal(user: User) {
  editingUser.value = user;
  formData.value = {
    email: user.email,
    user_level: user.user_level,
    is_active: user.is_active,
  };
  formErrors.value = {};
  showEditModal.value = true;
}

function openDeactivateConfirm(user: User) {
  deactivatingUser.value = user;
  showDeactivateConfirm.value = true;
}

async function handleCreate() {
  if (!validateForm()) return;

  try {
    await store.createUser({
      email: formData.value.email,
      user_level: formData.value.user_level,
    });
    showCreateModal.value = false;
    resetForm();
  } catch (e: any) {
    if (e?.status === 409) {
      formErrors.value.email = 'A user with this email already exists';
    }
  }
}

async function handleUpdate() {
  if (!editingUser.value) return;

  const updateData: UserUpdate = {};
  if (formData.value.user_level !== editingUser.value.user_level) {
    updateData.user_level = formData.value.user_level;
  }
  if (formData.value.is_active !== editingUser.value.is_active) {
    updateData.is_active = formData.value.is_active;
  }

  // Only update if there are changes
  if (Object.keys(updateData).length === 0) {
    showEditModal.value = false;
    editingUser.value = null;
    return;
  }

  try {
    await store.updateUser(editingUser.value.id, updateData);
    showEditModal.value = false;
    editingUser.value = null;
  } catch (e) {
    // Error handled by store
  }
}

async function handleDeactivate() {
  if (!deactivatingUser.value) return;

  try {
    await store.deactivateUser(deactivatingUser.value.id);
    showDeactivateConfirm.value = false;
    deactivatingUser.value = null;
  } catch (e) {
    // Error handled by store
  }
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString();
}

function getUserLevelLabel(level: UserLevel): string {
  return level === 'tenant_admin' ? 'Tenant Admin' : 'Simple User';
}
</script>

<template>
  <div class="user-manager">
    <!-- Header -->
    <div class="manager-header flex items-center justify-between mb-6">
      <h2 class="manager-title text-2xl font-bold text-gray-900">Users</h2>
      <button
        type="button"
        class="btn-primary px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
        @click="openCreateModal"
      >
        <svg class="btn-icon w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        New User
      </button>
    </div>

    <!-- Filters -->
    <div class="filters-row flex items-center gap-4 mb-4">
      <div class="search-wrapper flex-1">
        <input
          :value="searchQuery"
          type="text"
          placeholder="Search by email..."
          class="search-input w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          @input="setSearch(($event.target as HTMLInputElement).value)"
        />
      </div>
      <select
        :value="filterLevel"
        class="filter-select px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        @change="setLevelFilter(($event.target as HTMLSelectElement).value as UserLevel | 'all')"
      >
        <option value="all">All Levels</option>
        <option value="tenant_admin">Tenant Admin</option>
        <option value="simple_user">Simple User</option>
      </select>
      <label class="filter-checkbox flex items-center gap-2 text-sm text-gray-600">
        <input
          :checked="showInactive"
          type="checkbox"
          class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          @change="toggleInactive()"
        />
        Show inactive
      </label>
    </div>

    <!-- Error display -->
    <div
      v-if="error"
      class="error-banner mb-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-700"
    >
      {{ error }}
      <button
        type="button"
        class="error-dismiss ml-2 text-red-500 hover:text-red-700"
        @click="store.clearError()"
      >
        Dismiss
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state flex items-center justify-center py-12">
      <div class="spinner animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>

    <!-- User list -->
    <div v-else class="table-container bg-white rounded-lg border border-gray-200 overflow-hidden">
      <table class="data-table min-w-full divide-y divide-gray-200">
        <thead class="table-header bg-gray-50">
          <tr>
            <th class="th-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Email
            </th>
            <th class="th-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Level
            </th>
            <th class="th-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th class="th-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Created
            </th>
            <th class="th-cell th-actions px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="table-body divide-y divide-gray-200">
          <tr
            v-for="user in filteredUsers"
            :key="user.id"
            class="table-row hover:bg-gray-50"
          >
            <td class="td-cell px-6 py-4 whitespace-nowrap">
              <div class="user-email font-medium text-gray-900">
                {{ user.email }}
              </div>
            </td>
            <td class="td-cell px-6 py-4 whitespace-nowrap">
              <span
                class="level-badge px-2 py-1 text-xs font-medium rounded-full"
                :class="user.user_level === 'tenant_admin'
                  ? 'level-admin bg-purple-100 text-purple-800'
                  : 'level-user bg-gray-100 text-gray-600'"
              >
                {{ getUserLevelLabel(user.user_level) }}
              </span>
            </td>
            <td class="td-cell px-6 py-4 whitespace-nowrap">
              <span
                class="status-badge px-2 py-1 text-xs font-medium rounded-full"
                :class="user.is_active
                  ? 'status-active bg-green-100 text-green-800'
                  : 'status-inactive bg-gray-100 text-gray-600'"
              >
                {{ user.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="td-cell td-date px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatDate(user.created_at) }}
            </td>
            <td class="td-cell td-actions px-6 py-4 whitespace-nowrap text-right text-sm">
              <div class="action-buttons">
                <button
                  type="button"
                  class="btn-action btn-action-edit"
                  title="Edit user"
                  @click="openEditModal(user)"
                >
                  <svg class="action-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  v-if="user.is_active"
                  type="button"
                  class="btn-action btn-action-delete"
                  title="Deactivate user"
                  @click="openDeactivateConfirm(user)"
                >
                  <svg class="action-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                  </svg>
                </button>
              </div>
            </td>
          </tr>

          <tr v-if="filteredUsers.length === 0">
            <td colspan="5" class="empty-state px-6 py-12 text-center text-gray-500">
              No users found
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <Teleport to="body">
      <div
        v-if="showCreateModal"
        class="modal-overlay fixed inset-0 z-50 flex items-center justify-center"
      >
        <div class="modal-backdrop absolute inset-0 bg-black/50" @click="showCreateModal = false" />
        <div class="modal-content relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
          <div class="modal-header px-6 py-4 border-b">
            <h3 class="modal-title text-lg font-semibold">Create User</h3>
          </div>

          <form @submit.prevent="handleCreate">
            <div class="modal-body px-6 py-4 space-y-4">
              <!-- Email -->
              <div class="form-group">
                <label class="form-label block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  v-model="formData.email"
                  type="email"
                  class="form-input w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  :class="formErrors.email ? 'input-error border-red-500' : 'border-gray-300'"
                  placeholder="user@example.com"
                />
                <p v-if="formErrors.email" class="form-error mt-1 text-sm text-red-600">
                  {{ formErrors.email }}
                </p>
              </div>

              <!-- User Level -->
              <div class="form-group">
                <label class="form-label block text-sm font-medium text-gray-700 mb-1">User Level</label>
                <select
                  v-model="formData.user_level"
                  class="form-input w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  :class="formErrors.user_level ? 'input-error border-red-500' : 'border-gray-300'"
                >
                  <option v-for="opt in userLevelOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>
                <p v-if="formErrors.user_level" class="form-error mt-1 text-sm text-red-600">
                  {{ formErrors.user_level }}
                </p>
              </div>
            </div>

            <div class="modal-footer px-6 py-4 border-t flex justify-end gap-3">
              <button
                type="button"
                class="btn-secondary px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                @click="showCreateModal = false"
              >
                Cancel
              </button>
              <button
                type="submit"
                class="btn-primary px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                :disabled="loading"
              >
                Create
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Edit Modal -->
    <Teleport to="body">
      <div
        v-if="showEditModal"
        class="modal-overlay fixed inset-0 z-50 flex items-center justify-center"
      >
        <div class="modal-backdrop absolute inset-0 bg-black/50" @click="showEditModal = false" />
        <div class="modal-content relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
          <div class="modal-header px-6 py-4 border-b">
            <h3 class="modal-title text-lg font-semibold">Edit User</h3>
          </div>

          <form @submit.prevent="handleUpdate">
            <div class="modal-body px-6 py-4 space-y-4">
              <!-- Email (read-only) -->
              <div class="form-group">
                <label class="form-label block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  :value="formData.email"
                  type="email"
                  class="form-input w-full px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-500"
                  disabled
                />
                <p class="form-hint mt-1 text-xs text-gray-500">Email cannot be changed</p>
              </div>

              <!-- User Level -->
              <div class="form-group">
                <label class="form-label block text-sm font-medium text-gray-700 mb-1">User Level</label>
                <select
                  v-model="formData.user_level"
                  class="form-input w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option v-for="opt in userLevelOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>
              </div>

              <!-- Active -->
              <div class="form-group">
                <label class="checkbox-label flex items-center gap-2">
                  <input
                    v-model="formData.is_active"
                    type="checkbox"
                    class="form-checkbox rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span class="text-sm text-gray-700">Active</span>
                </label>
              </div>
            </div>

            <div class="modal-footer px-6 py-4 border-t flex justify-end gap-3">
              <button
                type="button"
                class="btn-secondary px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                @click="showEditModal = false"
              >
                Cancel
              </button>
              <button
                type="submit"
                class="btn-primary px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                :disabled="loading"
              >
                Update
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Deactivate Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="showDeactivateConfirm"
        class="modal-overlay fixed inset-0 z-50 flex items-center justify-center"
      >
        <div class="modal-backdrop absolute inset-0 bg-black/50" @click="showDeactivateConfirm = false" />
        <div class="modal-content modal-sm relative bg-white rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
          <h3 class="modal-title text-lg font-semibold mb-2">Deactivate User</h3>
          <p class="modal-message text-gray-600 mb-4">
            Are you sure you want to deactivate <strong>{{ deactivatingUser?.email }}</strong>?
            They will lose access to this tenant.
          </p>
          <div class="modal-actions flex justify-end gap-3">
            <button
              type="button"
              class="btn-secondary px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              @click="showDeactivateConfirm = false"
            >
              Cancel
            </button>
            <button
              type="button"
              class="btn-danger px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              :disabled="loading"
              @click="handleDeactivate"
            >
              Deactivate
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/**
 * Fallback styles for Vibes independence
 */

/* === Layout === */
.user-manager {
  font-family: system-ui, -apple-system, sans-serif;
  color: var(--color-text, #1f2937);
}

.manager-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.manager-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-heading, #111827);
  margin: 0;
}

/* === Buttons === */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--color-primary, #2563eb);
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-primary:hover {
  background: var(--color-primary-hover, #1d4ed8);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background: transparent;
  color: var(--color-text, #374151);
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-secondary:hover {
  background: var(--color-hover, #f3f4f6);
}

.btn-danger {
  padding: 0.5rem 1rem;
  background: var(--color-danger, #dc2626);
  color: white;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-danger:hover {
  background: var(--color-danger-hover, #b91c1c);
}

.btn-icon {
  width: 1.25rem;
  height: 1.25rem;
}

/* === Filters === */
.filters-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.search-wrapper {
  flex: 1;
}

.search-input,
.filter-select {
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.search-input {
  width: 100%;
}

.search-input:focus,
.filter-select:focus {
  outline: none;
  border-color: var(--color-primary, #2563eb);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

.filter-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary, #6b7280);
  cursor: pointer;
}

/* === Error Banner === */
.error-banner {
  padding: 1rem;
  background: var(--color-error-bg, #fef2f2);
  border: 1px solid var(--color-error-border, #fecaca);
  border-radius: 0.375rem;
  color: var(--color-error, #dc2626);
  margin-bottom: 1rem;
}

.error-dismiss {
  margin-left: 0.5rem;
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  text-decoration: underline;
}

/* === Loading State === */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid var(--color-border, #e5e7eb);
  border-top-color: var(--color-primary, #2563eb);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* === Table === */
.table-container {
  background: white;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 0.5rem;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.table-header {
  background: var(--color-bg-secondary, #f9fafb);
}

.th-cell {
  padding: 0.75rem 1.5rem;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-secondary, #6b7280);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.th-actions {
  text-align: right;
}

.table-body tr {
  border-top: 1px solid var(--color-border, #e5e7eb);
}

.table-row:hover {
  background: var(--color-hover, #f9fafb);
}

.td-cell {
  padding: 1rem 1.5rem;
  white-space: nowrap;
}

.user-email {
  font-weight: 500;
  color: var(--color-text, #111827);
}

.level-badge,
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.level-admin {
  background: var(--color-purple-bg, #f3e8ff);
  color: var(--color-purple, #7c3aed);
}

.level-user {
  background: var(--color-bg-secondary, #f3f4f6);
  color: var(--color-text-secondary, #6b7280);
}

.status-active {
  background: var(--color-success-bg, #d1fae5);
  color: var(--color-success, #065f46);
}

.status-inactive {
  background: var(--color-bg-secondary, #f3f4f6);
  color: var(--color-text-secondary, #6b7280);
}

.td-date {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #6b7280);
}

.td-actions {
  text-align: right;
}

.empty-state {
  padding: 3rem 1.5rem;
  text-align: center;
  color: var(--color-text-secondary, #6b7280);
}

/* === Action Buttons === */
.action-buttons {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
}

.btn-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 0.375rem;
  background: white;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-action:hover {
  background: var(--color-hover, #f3f4f6);
}

.btn-action-edit {
  color: var(--color-primary, #2563eb);
}

.btn-action-edit:hover {
  border-color: var(--color-primary, #2563eb);
  background: rgba(37, 99, 235, 0.1);
}

.btn-action-delete {
  color: var(--color-danger, #dc2626);
}

.btn-action-delete:hover {
  border-color: var(--color-danger, #dc2626);
  background: rgba(220, 38, 38, 0.1);
}

.action-icon {
  width: 1rem;
  height: 1rem;
}

/* === Modal === */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
}

.modal-content {
  position: relative;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  width: 100%;
  max-width: 28rem;
  margin: 1rem;
}

.modal-sm {
  max-width: 24rem;
  padding: 1.5rem;
}

.modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-heading, #111827);
  margin: 0;
}

.modal-body {
  padding: 1rem 1.5rem;
}

.modal-body > * + * {
  margin-top: 1rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border, #e5e7eb);
}

.modal-message {
  color: var(--color-text-secondary, #4b5563);
  margin-bottom: 1rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

/* === Form === */
.form-group {
  margin-bottom: 0;
}

.form-label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text, #374151);
}

.form-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary, #2563eb);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

.input-error {
  border-color: var(--color-danger, #dc2626);
}

.input-error:focus {
  border-color: var(--color-danger, #dc2626);
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.2);
}

.form-error {
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: var(--color-danger, #dc2626);
}

.form-hint {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--color-text-secondary, #6b7280);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.form-checkbox {
  width: 1rem;
  height: 1rem;
}
</style>
