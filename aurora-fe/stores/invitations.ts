/**
 * Aurora Pinia Store - Invitations
 *
 * Central state management for user invitations.
 * Manages invitation list, filtering, and CRUD operations.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Invitation,
  InvitationCreate,
  InvitationQueryParams,
  InvitationStatus
} from '../types/invitations'
import {
  createInvitation as apiCreateInvitation,
  createInvitationsBulk,
  fetchInvitations,
  fetchInvitation,
  resendInvitation as apiResendInvitation,
  revokeInvitation as apiRevokeInvitation
} from '../services/invitations-api'

/**
 * Default page size
 */
const DEFAULT_PER_PAGE = 20

/**
 * Invitation Store
 *
 * Provides centralized state for:
 * - Invitation list
 * - Pagination state
 * - Filter/query state
 * - CRUD operations
 */
export const useInvitationStore = defineStore('aurora-invitations', () => {
  // ==========================================================================
  // State
  // ==========================================================================

  /** Invitation list */
  const invitations = ref<Invitation[]>([])

  /** Current page */
  const page = ref<number>(1)

  /** Items per page */
  const perPage = ref<number>(DEFAULT_PER_PAGE)

  /** Total count */
  const total = ref<number>(0)

  /** Has more pages */
  const hasMore = ref<boolean>(false)

  /** Loading state */
  const isLoading = ref<boolean>(false)

  /** Error message */
  const error = ref<string | null>(null)

  /** Current filters */
  const filters = ref<InvitationQueryParams>({})

  /** Currently selected invitation */
  const selectedInvitation = ref<Invitation | null>(null)

  // ==========================================================================
  // Getters
  // ==========================================================================

  /** Get pending invitations */
  const pendingInvitations = computed(() =>
    invitations.value.filter(inv => inv.status === 'pending')
  )

  /** Get accepted invitations */
  const acceptedInvitations = computed(() =>
    invitations.value.filter(inv => inv.status === 'accepted')
  )

  /** Get expired invitations */
  const expiredInvitations = computed(() =>
    invitations.value.filter(inv => inv.is_expired)
  )

  /** Get valid invitations */
  const validInvitations = computed(() =>
    invitations.value.filter(inv => inv.is_valid)
  )

  /** Get invitations by status */
  const invitationsByStatus = computed(() => (status: InvitationStatus) =>
    invitations.value.filter(inv => inv.status === status)
  )

  /** Get total pages */
  const totalPages = computed(() =>
    Math.ceil(total.value / perPage.value)
  )

  /** Check if on first page */
  const isFirstPage = computed(() => page.value === 1)

  /** Check if on last page */
  const isLastPage = computed(() => page.value >= totalPages.value)

  // ==========================================================================
  // Actions
  // ==========================================================================

  /**
   * Load invitations with current filters
   *
   * @param params - Optional override params
   */
  async function loadInvitations(params?: Partial<InvitationQueryParams>): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      const queryParams: InvitationQueryParams = {
        ...filters.value,
        ...params,
        page: params?.page ?? page.value,
        per_page: params?.per_page ?? perPage.value
      }

      const response = await fetchInvitations(queryParams)

      invitations.value = response.invitations
      total.value = response.total
      hasMore.value = response.has_more
      page.value = response.page
      perPage.value = response.per_page

      // Update filters with used params
      if (params) {
        filters.value = { ...filters.value, ...params }
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load invitations'
      console.error('[AURORA] Failed to load invitations:', e)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create a new invitation
   *
   * @param data - Invitation creation data
   */
  async function createInvitation(data: InvitationCreate): Promise<Invitation | null> {
    isLoading.value = true
    error.value = null

    try {
      const invitation = await apiCreateInvitation(data)

      // Add to list if it matches current filters
      if (shouldIncludeInvitation(invitation)) {
        invitations.value = [invitation, ...invitations.value]
        total.value++
      }

      return invitation
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create invitation'
      console.error('[AURORA] Failed to create invitation:', e)
      return null
    } finally {
      isLoading.value = false
    }
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
    isLoading.value = true
    error.value = null

    try {
      const result = await createInvitationsBulk({ invitations: dataList })

      // Add successfully created invitations to list
      if (result.created.length > 0) {
        const matching = result.created.filter(shouldIncludeInvitation)
        invitations.value = [...matching, ...invitations.value]
        total.value += matching.length
      }

      return {
        created: result.created,
        failed: result.failed
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create invitations'
      console.error('[AURORA] Failed to create invitations:', e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get a single invitation by ID
   *
   * @param invitationId - Invitation ID
   */
  async function getInvitation(invitationId: string): Promise<Invitation | null> {
    // Check if already in store
    const existing = invitations.value.find(inv => inv.id === invitationId)
    if (existing) {
      selectedInvitation.value = existing
      return existing
    }

    try {
      const invitation = await fetchInvitation(invitationId)
      selectedInvitation.value = invitation
      return invitation
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch invitation'
      console.error('[AURORA] Failed to fetch invitation:', e)
      return null
    }
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
    isLoading.value = true
    error.value = null

    try {
      const invitation = await apiResendInvitation(
        invitationId,
        customMessage ? { custom_message: customMessage } : undefined
      )

      // Update in list
      const index = invitations.value.findIndex(inv => inv.id === invitationId)
      if (index !== -1) {
        invitations.value[index] = invitation
      }

      if (selectedInvitation.value?.id === invitationId) {
        selectedInvitation.value = invitation
      }

      return invitation
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to resend invitation'
      console.error('[AURORA] Failed to resend invitation:', e)
      return null
    } finally {
      isLoading.value = false
    }
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
    isLoading.value = true
    error.value = null

    try {
      const invitation = await apiRevokeInvitation(
        invitationId,
        reason ? { reason } : undefined
      )

      // Update in list
      const index = invitations.value.findIndex(inv => inv.id === invitationId)
      if (index !== -1) {
        invitations.value[index] = invitation
      }

      if (selectedInvitation.value?.id === invitationId) {
        selectedInvitation.value = invitation
      }

      return invitation
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to revoke invitation'
      console.error('[AURORA] Failed to revoke invitation:', e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Go to next page
   */
  async function nextPage(): Promise<void> {
    if (!isLastPage.value) {
      await loadInvitations({ page: page.value + 1 })
    }
  }

  /**
   * Go to previous page
   */
  async function previousPage(): Promise<void> {
    if (!isFirstPage.value) {
      await loadInvitations({ page: page.value - 1 })
    }
  }

  /**
   * Go to specific page
   *
   * @param pageNum - Page number
   */
  async function goToPage(pageNum: number): Promise<void> {
    if (pageNum >= 1 && pageNum <= totalPages.value) {
      await loadInvitations({ page: pageNum })
    }
  }

  /**
   * Update filters and reload
   *
   * @param newFilters - New filter values
   */
  async function setFilters(newFilters: InvitationQueryParams): Promise<void> {
    filters.value = newFilters
    page.value = 1
    await loadInvitations()
  }

  /**
   * Clear all filters
   */
  async function clearFilters(): Promise<void> {
    filters.value = {}
    page.value = 1
    await loadInvitations()
  }

  /**
   * Refresh invitations (reload current page)
   */
  async function refresh(): Promise<void> {
    await loadInvitations()
  }

  /**
   * Clear the store
   */
  function clear(): void {
    invitations.value = []
    page.value = 1
    total.value = 0
    hasMore.value = false
    filters.value = {}
    selectedInvitation.value = null
    error.value = null
  }

  /**
   * Select an invitation
   *
   * @param invitation - Invitation to select
   */
  function selectInvitation(invitation: Invitation | null): void {
    selectedInvitation.value = invitation
  }

  // ==========================================================================
  // Helpers
  // ==========================================================================

  /**
   * Check if an invitation matches current filters
   */
  function shouldIncludeInvitation(invitation: Invitation): boolean {
    const f = filters.value

    if (f.status && invitation.status !== f.status) return false
    if (f.statuses && !f.statuses.includes(invitation.status)) return false
    if (f.client_id && invitation.client_id !== f.client_id) return false

    if (f.search) {
      const search = f.search.toLowerCase()
      const matchesEmail = invitation.email.toLowerCase().includes(search)
      const matchesName = invitation.name?.toLowerCase().includes(search)
      if (!matchesEmail && !matchesName) return false
    }

    if (!f.include_expired && invitation.is_expired) return false

    return true
  }

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // State
    invitations,
    page,
    perPage,
    total,
    hasMore,
    isLoading,
    error,
    filters,
    selectedInvitation,

    // Getters
    pendingInvitations,
    acceptedInvitations,
    expiredInvitations,
    validInvitations,
    invitationsByStatus,
    totalPages,
    isFirstPage,
    isLastPage,

    // Actions
    loadInvitations,
    createInvitation,
    createInvitationsBatch,
    getInvitation,
    resendInvitation,
    revokeInvitation,
    nextPage,
    previousPage,
    goToPage,
    setFilters,
    clearFilters,
    refresh,
    clear,
    selectInvitation
  }
})
