/**
 * Invitation Store
 *
 * Pinia store for invitation state management.
 * Handles invitation listing, filtering, pagination, and CRUD operations.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Invitation,
  InvitationList,
  InvitationStats,
  InvitationFilter,
  InvitationQueryParams,
  InvitationCreate,
  InvitationAccept,
  InvitationAcceptResponse,
} from '../types'
import {
  fetchInvitations,
  fetchInvitation,
  fetchInvitationStats,
  createInvitation,
  resendInvitation,
  revokeInvitation,
  acceptInvitation,
} from '../services/aurora-api'

export const useInvitationStore = defineStore('invitation', () => {
  // ============================================================================
  // STATE
  // ============================================================================

  // Invitations
  const invitations = ref<Invitation[]>([])
  const currentInvitation = ref<Invitation | null>(null)

  // Pagination
  const totalInvitations = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(50)
  const totalPages = ref(0)

  // Filter state
  const filter = ref<InvitationFilter>({})

  // Statistics
  const stats = ref<InvitationStats | null>(null)

  // Loading states
  const isLoading = ref(false)
  const isLoadingStats = ref(false)
  const isCreating = ref(false)
  const isResending = ref(false)
  const isRevoking = ref(false)
  const isAccepting = ref(false)

  // Error state
  const error = ref<string | null>(null)

  // ============================================================================
  // GETTERS (Computed)
  // ============================================================================

  const hasInvitations = computed(() => invitations.value.length > 0)
  const hasMorePages = computed(() => currentPage.value < totalPages.value)
  const hasPreviousPage = computed(() => currentPage.value > 1)

  const activeFiltersCount = computed(() => {
    return Object.values(filter.value).filter(
      (v) => v !== undefined && v !== null && v !== ''
    ).length
  })

  const hasActiveFilters = computed(() => activeFiltersCount.value > 0)

  const pendingInvitations = computed(() =>
    invitations.value.filter((i) => i.status === 'PENDING')
  )

  const pendingCount = computed(() => stats.value?.pending ?? 0)

  // ============================================================================
  // ACTIONS
  // ============================================================================

  /**
   * Load invitations with current filter and pagination
   */
  async function loadInvitations(resetPage = false): Promise<void> {
    if (resetPage) {
      currentPage.value = 1
    }

    const params: InvitationQueryParams = {
      ...filter.value,
      page: currentPage.value,
      page_size: pageSize.value,
    }

    isLoading.value = true
    error.value = null

    try {
      const result = await fetchInvitations(params)
      invitations.value = result.items
      totalInvitations.value = result.total
      totalPages.value = result.pages
      currentPage.value = result.page
      pageSize.value = result.page_size
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load invitations'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load a single invitation
   */
  async function loadInvitation(invitationId: string): Promise<Invitation> {
    isLoading.value = true
    error.value = null

    try {
      const result = await fetchInvitation(invitationId)
      currentInvitation.value = result
      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load invitation'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load invitation statistics
   */
  async function loadStats(): Promise<void> {
    isLoadingStats.value = true
    error.value = null

    try {
      stats.value = await fetchInvitationStats()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load stats'
      throw e
    } finally {
      isLoadingStats.value = false
    }
  }

  /**
   * Create a new invitation
   */
  async function create(data: InvitationCreate): Promise<Invitation> {
    isCreating.value = true
    error.value = null

    try {
      const invitation = await createInvitation(data)
      // Add to list
      invitations.value.unshift(invitation)
      totalInvitations.value++
      // Reload stats
      await loadStats()
      return invitation
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create invitation'
      throw e
    } finally {
      isCreating.value = false
    }
  }

  /**
   * Resend an invitation
   */
  async function resend(invitationId: string): Promise<boolean> {
    isResending.value = true
    error.value = null

    try {
      const result = await resendInvitation(invitationId)
      return result.success
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to resend invitation'
      throw e
    } finally {
      isResending.value = false
    }
  }

  /**
   * Revoke an invitation
   */
  async function revoke(invitationId: string): Promise<boolean> {
    isRevoking.value = true
    error.value = null

    try {
      const result = await revokeInvitation(invitationId)
      if (result.success) {
        // Update local state
        const index = invitations.value.findIndex((i) => i.id === invitationId)
        if (index !== -1) {
          invitations.value[index].status = 'REVOKED'
          invitations.value[index].revoked_at = new Date().toISOString()
        }
        // Reload stats
        await loadStats()
      }
      return result.success
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to revoke invitation'
      throw e
    } finally {
      isRevoking.value = false
    }
  }

  /**
   * Accept an invitation
   */
  async function accept(token: string): Promise<InvitationAcceptResponse> {
    isAccepting.value = true
    error.value = null

    try {
      const result = await acceptInvitation({ token })
      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to accept invitation'
      throw e
    } finally {
      isAccepting.value = false
    }
  }

  /**
   * Go to next page
   */
  async function nextPage(): Promise<void> {
    if (hasMorePages.value) {
      currentPage.value++
      await loadInvitations()
    }
  }

  /**
   * Go to previous page
   */
  async function previousPage(): Promise<void> {
    if (hasPreviousPage.value) {
      currentPage.value--
      await loadInvitations()
    }
  }

  /**
   * Go to specific page
   */
  async function goToPage(page: number): Promise<void> {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
      await loadInvitations()
    }
  }

  /**
   * Set filter and reload
   */
  async function setFilter(newFilter: InvitationFilter): Promise<void> {
    filter.value = { ...newFilter }
    await loadInvitations(true)
  }

  /**
   * Update filter property and reload
   */
  async function updateFilter<K extends keyof InvitationFilter>(
    key: K,
    value: InvitationFilter[K]
  ): Promise<void> {
    filter.value[key] = value
    await loadInvitations(true)
  }

  /**
   * Clear all filters and reload
   */
  async function clearFilters(): Promise<void> {
    filter.value = {}
    await loadInvitations(true)
  }

  /**
   * Set page size and reload
   */
  async function setPageSize(size: number): Promise<void> {
    pageSize.value = size
    await loadInvitations(true)
  }

  /**
   * Refresh current view
   */
  async function refresh(): Promise<void> {
    await loadInvitations()
    await loadStats()
  }

  /**
   * Clear current invitation selection
   */
  function clearCurrentInvitation(): void {
    currentInvitation.value = null
  }

  /**
   * Reset store to initial state
   */
  function $reset(): void {
    invitations.value = []
    currentInvitation.value = null
    totalInvitations.value = 0
    currentPage.value = 1
    pageSize.value = 50
    totalPages.value = 0
    filter.value = {}
    stats.value = null
    isLoading.value = false
    isLoadingStats.value = false
    isCreating.value = false
    isResending.value = false
    isRevoking.value = false
    isAccepting.value = false
    error.value = null
  }

  // ============================================================================
  // RETURN
  // ============================================================================

  return {
    // State
    invitations,
    currentInvitation,
    totalInvitations,
    currentPage,
    pageSize,
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

    // Getters
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
    create,
    resend,
    revoke,
    accept,
    nextPage,
    previousPage,
    goToPage,
    setFilter,
    updateFilter,
    clearFilters,
    setPageSize,
    refresh,
    clearCurrentInvitation,
    $reset,
  }
})
