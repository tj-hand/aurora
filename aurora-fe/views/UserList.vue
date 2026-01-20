<script setup>
/**
 * UserList - User Management View
 *
 * Page wrapper for UserManager component.
 * Lists and manages users within the current tenant.
 */
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGuardianStore } from '@/stores/guardian'
import UserManager from '../components/ui/UserManager.vue'

const router = useRouter()
const guardian = useGuardianStore()

// Verify authentication on mount
onMounted(() => {
  if (!guardian.isAuthenticated) {
    router.push({ name: 'guardian-login' })
  }
})
</script>

<template>
  <div class="aurora-page users-page">
    <div class="page-content">
      <UserManager />
    </div>
  </div>
</template>

<style scoped>
.aurora-page {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-content {
  background: var(--color-bg, white);
}
</style>
