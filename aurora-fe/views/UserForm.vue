<script setup lang="ts">
/**
 * UserForm - Create/Edit User View
 *
 * Standalone form page for creating or editing users.
 * Route: /users/new (create) or /users/:id/edit (edit)
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useGuardianStore } from '@/stores/guardian'
import { useUserStore } from '@/stores/userStore'
import type { User, UserCreate, UserUpdate, UserLevel } from '@/stores/types'

const router = useRouter()
const route = useRoute()
const guardian = useGuardianStore()
const store = useUserStore()

// Mode detection
const isEditMode = computed(() => !!route.params.id)
const userId = computed(() => route.params.id as string | undefined)
const pageTitle = computed(() => isEditMode.value ? 'Edit User' : 'Create User')

// Form state
const formData = ref<UserCreate & { is_active?: boolean }>({
  email: '',
  user_level: 'simple_user',
})
const formErrors = ref<Record<string, string>>({})
const originalUser = ref<User | null>(null)
const loading = ref(false)
const submitError = ref<string | null>(null)

const userLevelOptions: { value: UserLevel; label: string }[] = [
  { value: 'simple_user', label: 'Simple User' },
  { value: 'tenant_admin', label: 'Tenant Admin' },
]

function validateForm(): boolean {
  formErrors.value = {}

  if (!isEditMode.value) {
    if (!formData.value.email.trim()) {
      formErrors.value.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.value.email)) {
      formErrors.value.email = 'Invalid email format'
    }
  }

  if (!formData.value.user_level) {
    formErrors.value.user_level = 'User level is required'
  }

  return Object.keys(formErrors.value).length === 0
}

async function loadUser() {
  if (!userId.value) return

  loading.value = true
  try {
    const user = await store.fetchUser(userId.value)
    originalUser.value = user
    formData.value = {
      email: user.email,
      user_level: user.user_level,
      is_active: user.is_active,
    }
  } catch (e) {
    submitError.value = 'Failed to load user'
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!validateForm()) return

  loading.value = true
  submitError.value = null

  try {
    if (isEditMode.value && userId.value) {
      // Update existing user
      const updateData: UserUpdate = {}
      if (formData.value.user_level !== originalUser.value?.user_level) {
        updateData.user_level = formData.value.user_level
      }
      if (formData.value.is_active !== originalUser.value?.is_active) {
        updateData.is_active = formData.value.is_active
      }
      await store.updateUser(userId.value, updateData)
    } else {
      // Create new user
      await store.createUser({
        email: formData.value.email,
        user_level: formData.value.user_level,
      })
    }
    router.push({ name: 'aurora-users' })
  } catch (e: any) {
    if (e?.status === 409) {
      formErrors.value.email = 'A user with this email already exists'
    } else {
      submitError.value = e?.message || 'Failed to save user'
    }
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.back()
}

// Load user data if editing
onMounted(() => {
  if (!guardian.isAuthenticated) {
    router.push({ name: 'guardian-login' })
    return
  }

  if (isEditMode.value) {
    loadUser()
  }
})

// Watch for route changes (e.g., navigating from edit to create)
watch(() => route.params.id, (newId) => {
  if (newId) {
    loadUser()
  } else {
    formData.value = { email: '', user_level: 'simple_user' }
    originalUser.value = null
    formErrors.value = {}
  }
})
</script>

<template>
  <div class="aurora-page user-form-page">
    <div class="page-header">
      <button type="button" class="btn-back" @click="handleCancel">
        <svg class="back-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Back
      </button>
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>

    <!-- Loading -->
    <div v-if="loading && isEditMode" class="loading-state">
      <div class="spinner" />
    </div>

    <!-- Form -->
    <div v-else class="form-container">
      <form class="user-form" @submit.prevent="handleSubmit">
        <!-- Error -->
        <div v-if="submitError" class="error-banner">
          {{ submitError }}
        </div>

        <!-- Email -->
        <div class="form-group">
          <label class="form-label">Email</label>
          <input
            v-model="formData.email"
            type="email"
            class="form-input"
            :class="{ 'input-error': formErrors.email }"
            :disabled="isEditMode"
            placeholder="user@example.com"
          />
          <p v-if="formErrors.email" class="form-error">{{ formErrors.email }}</p>
          <p v-if="isEditMode" class="form-hint">Email cannot be changed</p>
        </div>

        <!-- User Level -->
        <div class="form-group">
          <label class="form-label">User Level</label>
          <select
            v-model="formData.user_level"
            class="form-input"
            :class="{ 'input-error': formErrors.user_level }"
          >
            <option v-for="opt in userLevelOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
          <p v-if="formErrors.user_level" class="form-error">{{ formErrors.user_level }}</p>
        </div>

        <!-- Active (edit mode only) -->
        <div v-if="isEditMode" class="form-group">
          <label class="checkbox-label">
            <input
              v-model="formData.is_active"
              type="checkbox"
              class="form-checkbox"
            />
            <span>Active</span>
          </label>
        </div>

        <!-- Actions -->
        <div class="form-actions">
          <button type="button" class="btn-secondary" @click="handleCancel">
            Cancel
          </button>
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ isEditMode ? 'Update' : 'Create' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.aurora-page {
  padding: 1.5rem;
  max-width: 600px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 1rem;
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

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-heading, #111827);
  margin: 0;
}

.loading-state {
  display: flex;
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

.form-container {
  background: white;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.user-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.error-banner {
  padding: 1rem;
  background: var(--color-error-bg, #fef2f2);
  border: 1px solid var(--color-error-border, #fecaca);
  border-radius: 0.375rem;
  color: var(--color-error, #dc2626);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text, #374151);
}

.form-input {
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--color-border, #d1d5db);
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary, #2563eb);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

.form-input:disabled {
  background: var(--color-bg-secondary, #f9fafb);
  color: var(--color-text-secondary, #6b7280);
}

.input-error {
  border-color: var(--color-danger, #dc2626);
}

.form-error {
  font-size: 0.875rem;
  color: var(--color-danger, #dc2626);
  margin: 0;
}

.form-hint {
  font-size: 0.75rem;
  color: var(--color-text-secondary, #6b7280);
  margin: 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text, #374151);
}

.form-checkbox {
  width: 1rem;
  height: 1rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border, #e5e7eb);
}

.btn-primary {
  padding: 0.625rem 1.25rem;
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
  padding: 0.625rem 1.25rem;
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
</style>
