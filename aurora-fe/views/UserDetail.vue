<script setup lang="ts">
/**
 * UserDetail - User Detail View
 *
 * Displays user details with edit and deactivate actions.
 * Route: /users/:id
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useGuardianStore } from '@/stores/guardian'
import { useUserStore } from '../stores/userStore'
import type { User, UserLevel } from '../stores/types'

const router = useRouter()
const route = useRoute()
const guardian = useGuardianStore()
const store = useUserStore()

const userId = computed(() => route.params.id as string)
const user = ref<User | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const showDeactivateConfirm = ref(false)

function getUserLevelLabel(level: UserLevel): string {
  return level === 'tenant_admin' ? 'Tenant Admin' : 'Simple User'
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString()
}

async function loadUser() {
  loading.value = true
  error.value = null

  try {
    user.value = await store.fetchUser(userId.value)
  } catch (e: any) {
    error.value = e?.message || 'Failed to load user'
  } finally {
    loading.value = false
  }
}

function handleEdit() {
  router.push({ name: 'aurora-user-edit', params: { id: userId.value } })
}

function handleBack() {
  router.push({ name: 'aurora-users' })
}

async function handleDeactivate() {
  if (!user.value) return

  try {
    await store.deactivateUser(user.value.id)
    showDeactivateConfirm.value = false
    router.push({ name: 'aurora-users' })
  } catch (e) {
    // Error handled by store
  }
}

onMounted(() => {
  if (!guardian.isAuthenticated) {
    router.push({ name: 'guardian-login' })
    return
  }

  loadUser()
})
</script>

<template>
  <div class="aurora-page user-detail-page">
    <div class="page-header">
      <button type="button" class="btn-back" @click="handleBack">
        <svg class="back-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Back to Users
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
      <button type="button" class="btn-secondary" @click="loadUser">Retry</button>
    </div>

    <!-- User Details -->
    <div v-else-if="user" class="detail-container">
      <div class="detail-header">
        <div class="user-avatar">
          {{ user.email.charAt(0).toUpperCase() }}
        </div>
        <div class="user-info">
          <h1 class="user-email">{{ user.email }}</h1>
          <div class="user-badges">
            <span
              class="level-badge"
              :class="user.user_level === 'tenant_admin' ? 'level-admin' : 'level-user'"
            >
              {{ getUserLevelLabel(user.user_level) }}
            </span>
            <span
              class="status-badge"
              :class="user.is_active ? 'status-active' : 'status-inactive'"
            >
              {{ user.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
        </div>
        <div class="header-actions">
          <button type="button" class="btn-secondary" @click="handleEdit">
            <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Edit
          </button>
          <button
            v-if="user.is_active"
            type="button"
            class="btn-danger"
            @click="showDeactivateConfirm = true"
          >
            <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
            Deactivate
          </button>
        </div>
      </div>

      <div class="detail-body">
        <div class="detail-section">
          <h2 class="section-title">User Information</h2>
          <dl class="detail-list">
            <div class="detail-item">
              <dt class="detail-label">User ID</dt>
              <dd class="detail-value mono">{{ user.id }}</dd>
            </div>
            <div class="detail-item">
              <dt class="detail-label">Email</dt>
              <dd class="detail-value">{{ user.email }}</dd>
            </div>
            <div class="detail-item">
              <dt class="detail-label">User Level</dt>
              <dd class="detail-value">{{ getUserLevelLabel(user.user_level) }}</dd>
            </div>
            <div class="detail-item">
              <dt class="detail-label">Status</dt>
              <dd class="detail-value">{{ user.is_active ? 'Active' : 'Inactive' }}</dd>
            </div>
          </dl>
        </div>

        <div class="detail-section">
          <h2 class="section-title">Tenant Association</h2>
          <dl class="detail-list">
            <div class="detail-item">
              <dt class="detail-label">Tenant ID</dt>
              <dd class="detail-value mono">{{ user.tenant_id }}</dd>
            </div>
            <div class="detail-item">
              <dt class="detail-label">Association ID</dt>
              <dd class="detail-value mono">{{ user.association_id }}</dd>
            </div>
          </dl>
        </div>

        <div class="detail-section">
          <h2 class="section-title">Timestamps</h2>
          <dl class="detail-list">
            <div class="detail-item">
              <dt class="detail-label">Created</dt>
              <dd class="detail-value">{{ formatDate(user.created_at) }}</dd>
            </div>
            <div class="detail-item">
              <dt class="detail-label">Updated</dt>
              <dd class="detail-value">{{ formatDate(user.updated_at) }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>

    <!-- Deactivate Confirmation Modal -->
    <Teleport to="body">
      <div
        v-if="showDeactivateConfirm"
        class="modal-overlay"
      >
        <div class="modal-backdrop" @click="showDeactivateConfirm = false" />
        <div class="modal-content">
          <h3 class="modal-title">Deactivate User</h3>
          <p class="modal-message">
            Are you sure you want to deactivate <strong>{{ user?.email }}</strong>?
            They will lose access to this tenant.
          </p>
          <div class="modal-actions">
            <button
              type="button"
              class="btn-secondary"
              @click="showDeactivateConfirm = false"
            >
              Cancel
            </button>
            <button
              type="button"
              class="btn-danger"
              :disabled="store.loading"
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
.aurora-page {
  padding: 1.5rem;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 1.5rem;
}

.btn-back {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem;
  background: none;
  border: none;
  color: var(--color-text-secondary, #6b7280);
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-back:hover {
  color: var(--color-text, #111827);
}

.back-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  gap: 1rem;
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

.error-message {
  color: var(--color-error, #dc2626);
  margin: 0;
}

.detail-container {
  background: white;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 0.5rem;
  overflow: hidden;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
  background: var(--color-bg-secondary, #f9fafb);
}

.user-avatar {
  width: 4rem;
  height: 4rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary, #2563eb);
  color: white;
  font-size: 1.5rem;
  font-weight: 600;
  border-radius: 50%;
}

.user-info {
  flex: 1;
}

.user-email {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-heading, #111827);
  margin: 0 0 0.5rem 0;
}

.user-badges {
  display: flex;
  gap: 0.5rem;
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

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: transparent;
  color: var(--color-text, #374151);
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background-color 0.15s;
}

.btn-secondary:hover {
  background: var(--color-hover, #f3f4f6);
}

.btn-danger {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: var(--color-danger, #dc2626);
  color: white;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background-color 0.15s;
}

.btn-danger:hover {
  background: var(--color-danger-hover, #b91c1c);
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  width: 1rem;
  height: 1rem;
}

.detail-body {
  padding: 1.5rem;
}

.detail-section {
  margin-bottom: 2rem;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-secondary, #6b7280);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 1rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.detail-list {
  margin: 0;
}

.detail-item {
  display: flex;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--color-border-light, #f3f4f6);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  width: 140px;
  flex-shrink: 0;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary, #6b7280);
}

.detail-value {
  font-size: 0.875rem;
  color: var(--color-text, #111827);
}

.detail-value.mono {
  font-family: monospace;
  font-size: 0.8125rem;
  background: var(--color-bg-secondary, #f3f4f6);
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

/* Modal */
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
  max-width: 24rem;
  margin: 1rem;
  padding: 1.5rem;
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-heading, #111827);
  margin: 0 0 0.5rem 0;
}

.modal-message {
  color: var(--color-text-secondary, #4b5563);
  margin: 0 0 1.5rem 0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}
</style>
