/**
 * Aurora Frontend - useInvitations Composable
 *
 * Vue composable for managing invitations in components.
 * Provides convenient access to invitation store and actions.
 */

import { computed, onMounted, watch, type Ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useInvitationStore } from '../stores/invitations'
import {
  fetchInvitationTokenInfo,
  acceptInvitation as apiAcceptInvitation
} from '../services/invitations-api'
import type {
  Invitation,
  InvitationCreate,
  InvitationQueryParams,
  InvitationStatus,
  InvitationTokenInfo,
  UseInvitationsOptions
} from '../types/invitations'

/**
 * Composable for managing invitations
 *
 * Provides reactive access to invitation state and actions.
 *
 * @param options - Composable options
 * @returns Invitation state and methods
 *
 * @example
 * ```typescript
 * // Basic usage
 * const { invitations, isLoading, createInvitation } = useInvitations()
 *
 * // With auto-load and filters
 * const { invitations, pendingInvitations } = useInvitations({
 *   autoLoad: true,
 *   initialFilters: { status: 'pending' }
 * })
 * ```
 */
export function useInvitations(options: UseInvitationsOptions = {}) {
  const store = useInvitationStore()

  const {
    autoLoad = false,
    initialFilters,
    perPage = 20
  } = options

  // Get reactive refs from store
  const {
    invitations,
    page,
    perPage: storePerPage,
    total,
    hasMore,
    isLoading,
    error,
    filters,
    selectedInvitation,
    pendingInvitations,
    acceptedInvitations,
    expiredInvitations,
    validInvitations,
    totalPages,
    isFirstPage,
    isLastPage
  } = storeToRefs(store)

  // ==========================================================================
  // Lifecycle
  // ==========================================================================

  onMounted(async () => {
    if (autoLoad) {
      const params: InvitationQueryParams = {
        ...initialFilters,
        per_page: perPage
      }
      await store.loadInvitations(params)
    }
  })

  // ==========================================================================
  // Actions
  // ==========================================================================

  /**
   * Create a new invitation
   *
   * @param data - Invitation data
   */
  async function createInvitation(data: InvitationCreate): Promise<Invitation | null> {
    return store.createInvitation(data)
  }

  /**
   * Create multiple invitations
   *
   * @param dataList - List of invitation data
   */
  async function createInvitationsBatch(dataList: InvitationCreate[]): Promise<{
    created: Invitation[]
    failed: Array<{ email: string; error: string }>
  } | null> {
    return store.createInvitationsBatch(dataList)
  }

  /**
   * Resend invitation email
   *
   * @param invitationId - Invitation ID
   * @param customMessage - Optional custom message
   */
  async function resendInvitation(
    invitationId: string,
    customMessage?: string
  ): Promise<Invitation | null> {
    return store.resendInvitation(invitationId, customMessage)
  }

  /**
   * Revoke an invitation
   *
   * @param invitationId - Invitation ID
   * @param reason - Optional revocation reason
   */
  async function revokeInvitation(
    invitationId: string,
    reason?: string
  ): Promise<Invitation | null> {
    return store.revokeInvitation(invitationId, reason)
  }

  /**
   * Get invitation by ID
   *
   * @param invitationId - Invitation ID
   */
  async function getInvitation(invitationId: string): Promise<Invitation | null> {
    return store.getInvitation(invitationId)
  }

  /**
   * Load invitations with filters
   *
   * @param params - Query parameters
   */
  async function loadInvitations(params?: InvitationQueryParams): Promise<void> {
    await store.loadInvitations(params)
  }

  /**
   * Refresh invitations
   */
  async function refresh(): Promise<void> {
    await store.refresh()
  }

  /**
   * Set filters and reload
   *
   * @param newFilters - New filter values
   */
  async function setFilters(newFilters: InvitationQueryParams): Promise<void> {
    await store.setFilters(newFilters)
  }

  /**
   * Clear all filters
   */
  async function clearFilters(): Promise<void> {
    await store.clearFilters()
  }

  /**
   * Navigate to next page
   */
  async function nextPage(): Promise<void> {
    await store.nextPage()
  }

  /**
   * Navigate to previous page
   */
  async function previousPage(): Promise<void> {
    await store.previousPage()
  }

  /**
   * Go to specific page
   *
   * @param pageNum - Page number
   */
  async function goToPage(pageNum: number): Promise<void> {
    await store.goToPage(pageNum)
  }

  /**
   * Select an invitation
   *
   * @param invitation - Invitation to select
   */
  function selectInvitation(invitation: Invitation | null): void {
    store.selectInvitation(invitation)
  }

  /**
   * Clear the store
   */
  function clear(): void {
    store.clear()
  }

  // ==========================================================================
  // Computed
  // ==========================================================================

  /**
   * Get invitations by status
   */
  function getByStatus(status: InvitationStatus): Invitation[] {
    return store.invitationsByStatus(status)
  }

  /**
   * Check if an invitation can be resent
   */
  function canResend(invitation: Invitation): boolean {
    return invitation.status === 'pending' && invitation.is_valid
  }

  /**
   * Check if an invitation can be revoked
   */
  function canRevoke(invitation: Invitation): boolean {
    return invitation.status === 'pending'
  }

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // State
    invitations,
    page,
    perPage: storePerPage,
    total,
    hasMore,
    isLoading,
    error,
    filters,
    selectedInvitation,

    // Computed
    pendingInvitations,
    acceptedInvitations,
    expiredInvitations,
    validInvitations,
    totalPages,
    isFirstPage,
    isLastPage,

    // Actions
    createInvitation,
    createInvitationsBatch,
    resendInvitation,
    revokeInvitation,
    getInvitation,
    loadInvitations,
    refresh,
    setFilters,
    clearFilters,
    nextPage,
    previousPage,
    goToPage,
    selectInvitation,
    clear,

    // Helpers
    getByStatus,
    canResend,
    canRevoke
  }
}

/**
 * Composable for invitation acceptance flow
 *
 * Use this in the invitation acceptance page.
 *
 * @param token - Invitation token (reactive ref)
 * @returns Token info and acceptance methods
 *
 * @example
 * ```typescript
 * const token = ref(route.params.token as string)
 * const { tokenInfo, isValid, accept } = useInvitationAccept(token)
 * ```
 */
export function useInvitationAccept(token: Ref<string>) {
  const tokenInfo = ref<InvitationTokenInfo | null>(null)
  const isLoading = ref<boolean>(false)
  const error = ref<string | null>(null)
  const isAccepted = ref<boolean>(false)

  /**
   * Check if invitation is valid
   */
  const isValid = computed(() => tokenInfo.value?.is_valid ?? false)

  /**
   * Check if invitation is expired
   */
  const isExpired = computed(() => {
    if (!tokenInfo.value) return false
    return new Date(tokenInfo.value.expires_at) < new Date()
  })

  /**
   * Load token info
   */
  async function loadTokenInfo(): Promise<void> {
    if (!token.value) return

    isLoading.value = true
    error.value = null

    try {
      tokenInfo.value = await fetchInvitationTokenInfo(token.value)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Invalid invitation'
      tokenInfo.value = null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Accept the invitation
   */
  async function accept(): Promise<boolean> {
    if (!token.value || !isValid.value) return false

    isLoading.value = true
    error.value = null

    try {
      await apiAcceptInvitation(token.value)
      isAccepted.value = true
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to accept invitation'
      return false
    } finally {
      isLoading.value = false
    }
  }

  // Load token info when token changes
  watch(token, () => {
    if (token.value) {
      loadTokenInfo()
    }
  }, { immediate: true })

  return {
    tokenInfo,
    isLoading,
    error,
    isValid,
    isExpired,
    isAccepted,
    loadTokenInfo,
    accept
  }
}

// Re-export types for convenience
export type {
  Invitation,
  InvitationCreate,
  InvitationQueryParams,
  InvitationStatus,
  InvitationTokenInfo,
  UseInvitationsOptions
}
