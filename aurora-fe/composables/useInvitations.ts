/**
 * useInvitations Composable
 *
 * Primary composable for invitation management functionality.
 * Provides invitation CRUD operations for Vue components.
 */

import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useInvitationStore } from '../stores/invitationStore'
import type {
  Invitation,
  InvitationCreate,
  InvitationFilter,
  InvitationStatus,
  InvitationAcceptResponse,
} from '../types'

/**
 * Options for useInvitations composable
 */
export interface UseInvitationsOptions {
  /**
   * Automatically load invitations on mount
   * @default false
   */
  autoLoad?: boolean

  /**
   * Automatically load stats on mount
   * @default false
   */
  autoLoadStats?: boolean

  /**
   * Initial filter to apply
   */
  initialFilter?: InvitationFilter

  /**
   * Initial page size
   * @default 50
   */
  pageSize?: number
}

/**
 * useInvitations composable for invitation management
 *
 * @example
 * ```typescript
 * // Basic usage - creating invitations
 * const { create, isCreating } = useInvitations()
 *
 * await create({
 *   email: 'newuser@example.com',
 *   name: 'John Doe',
 * })
 *
 * // Dashboard usage - viewing invitations
 * const { invitations, loadInvitations, stats, filter, setFilter } = useInvitations({
 *   autoLoad: true,
 *   autoLoadStats: true,
 * })
 * ```
 */
export function useInvitations(options: UseInvitationsOptions = {}) {
  const {
    autoLoad = false,
    autoLoadStats = false,
    initialFilter,
    pageSize = 50,
  } = options

  // Get store and refs
  const store = useInvitationStore()
  const {
    invitations,
    currentInvitation,
    totalInvitations,
    currentPage,
    totalPages,
    filter,
    stats,
    isLoading,
    isLoadingStats,
    isCreating,
    isResending,
    isRevoking,
    isAccepting,
    error,
    hasInvitations,
    hasMorePages,
    hasPreviousPage,
    activeFiltersCount,
    hasActiveFilters,
    pendingInvitations,
    pendingCount,
  } = storeToRefs(store)

  // ============================================================================
  // CRUD ACTIONS
  // ============================================================================

  /**
   * Create a new invitation
   */
  async function create(data: InvitationCreate): Promise<Invitation | null> {
    try {
      return await store.create(data)
    } catch {
      return null
    }
  }

  /**
   * Resend an invitation email
   */
  async function resend(invitationId: string): Promise<boolean> {
    try {
      return await store.resend(invitationId)
    } catch {
      return false
    }
  }

  /**
   * Revoke a pending invitation
   */
  async function revoke(invitationId: string): Promise<boolean> {
    try {
      return await store.revoke(invitationId)
    } catch {
      return false
    }
  }

  /**
   * Accept an invitation
   */
  async function accept(token: string): Promise<InvitationAcceptResponse | null> {
    try {
      return await store.accept(token)
    } catch {
      return null
    }
  }

  // ============================================================================
  // LOADING
  // ============================================================================

  /**
   * Load invitations with current filter/pagination
   */
  async function loadInvitations(): Promise<void> {
    await store.loadInvitations()
  }

  /**
   * Load a single invitation
   */
  async function loadInvitation(invitationId: string): Promise<Invitation | undefined> {
    try {
      return await store.loadInvitation(invitationId)
    } catch {
      return undefined
    }
  }

  /**
   * Load invitation statistics
   */
  async function loadStats(): Promise<void> {
    await store.loadStats()
  }

  /**
   * Refresh invitations and stats
   */
  async function refresh(): Promise<void> {
    await store.refresh()
  }

  // ============================================================================
  // FILTERING
  // ============================================================================

  /**
   * Set filter and reload
   */
  async function setFilter(newFilter: InvitationFilter): Promise<void> {
    await store.setFilter(newFilter)
  }

  /**
   * Update a single filter property
   */
  async function updateFilter<K extends keyof InvitationFilter>(
    key: K,
    value: InvitationFilter[K]
  ): Promise<void> {
    await store.updateFilter(key, value)
  }

  /**
   * Clear all filters
   */
  async function clearFilters(): Promise<void> {
    await store.clearFilters()
  }

  /**
   * Filter by status
   */
  async function filterByStatus(status: InvitationStatus | undefined): Promise<void> {
    await updateFilter('status', status)
  }

  /**
   * Filter by email
   */
  async function filterByEmail(email: string | undefined): Promise<void> {
    await updateFilter('email', email)
  }

  // ============================================================================
  // PAGINATION
  // ============================================================================

  /**
   * Go to next page
   */
  async function nextPage(): Promise<void> {
    await store.nextPage()
  }

  /**
   * Go to previous page
   */
  async function previousPage(): Promise<void> {
    await store.previousPage()
  }

  /**
   * Go to specific page
   */
  async function goToPage(page: number): Promise<void> {
    await store.goToPage(page)
  }

  // ============================================================================
  // HELPERS
  // ============================================================================

  /**
   * Check if an invitation can be resent
   */
  function canResend(invitation: Invitation): boolean {
    return invitation.status === 'PENDING'
  }

  /**
   * Check if an invitation can be revoked
   */
  function canRevoke(invitation: Invitation): boolean {
    return invitation.status === 'PENDING'
  }

  /**
   * Get status color class
   */
  function getStatusColor(status: InvitationStatus): string {
    switch (status) {
      case 'PENDING':
        return 'warning'
      case 'ACCEPTED':
        return 'success'
      case 'EXPIRED':
        return 'muted'
      case 'REVOKED':
        return 'error'
      default:
        return 'default'
    }
  }

  // ============================================================================
  // LIFECYCLE
  // ============================================================================

  onMounted(async () => {
    // Apply initial filter if provided
    if (initialFilter) {
      store.filter = { ...initialFilter }
    }

    // Set page size
    if (pageSize !== store.pageSize) {
      store.pageSize = pageSize
    }

    // Auto-load on mount
    if (autoLoad) {
      await loadInvitations()
    }

    if (autoLoadStats) {
      await loadStats()
    }
  })

  // ============================================================================
  // RETURN
  // ============================================================================

  return {
    // CRUD
    create,
    resend,
    revoke,
    accept,

    // State (readonly refs from store)
    invitations,
    currentInvitation,
    totalInvitations,
    currentPage,
    totalPages,
    filter,
    stats,
    isLoading,
    isLoadingStats,
    isCreating,
    isResending,
    isRevoking,
    isAccepting,
    error,

    // Computed
    hasInvitations,
    hasMorePages,
    hasPreviousPage,
    activeFiltersCount,
    hasActiveFilters,
    pendingInvitations,
    pendingCount,

    // Actions
    loadInvitations,
    loadInvitation,
    loadStats,
    refresh,
    setFilter,
    updateFilter,
    clearFilters,
    filterByStatus,
    filterByEmail,
    nextPage,
    previousPage,
    goToPage,

    // Helpers
    canResend,
    canRevoke,
    getStatusColor,
  }
}
