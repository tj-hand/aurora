/**
 * Aurora Frontend - Invitation Types
 *
 * TypeScript type definitions for the invitation system.
 * Mirrors backend schemas from aurora-be/schemas/invitations.py
 */

/**
 * Invitation status values
 */
export type InvitationStatus = 'pending' | 'accepted' | 'revoked' | 'expired'

/**
 * User hierarchy levels
 */
export type UserLevel = 'tenant_admin' | 'simple_user'

/**
 * Request to create a new invitation
 */
export interface InvitationCreate {
  email: string
  name?: string
  user_level?: UserLevel
  role_id?: string
  client_id?: string
  message?: string
  validity_days?: number
}

/**
 * Request to resend an invitation
 */
export interface InvitationResend {
  custom_message?: string
}

/**
 * Request to revoke an invitation
 */
export interface InvitationRevoke {
  reason?: string
}

/**
 * Bulk invitation creation request
 */
export interface InvitationBulkCreate {
  invitations: InvitationCreate[]
}

/**
 * Invitation response from API
 */
export interface Invitation {
  id: string
  email: string
  name?: string
  tenant_id: string
  tenant_slug?: string
  client_id?: string
  client_slug?: string
  user_level: string
  role_id?: string
  status: InvitationStatus
  message?: string
  invited_by: string
  invited_by_email?: string
  accepted_by?: string
  accepted_at?: string
  revoked_by?: string
  revoked_at?: string
  revocation_reason?: string
  created_at: string
  expires_at: string
  updated_at: string
  email_sent_at?: string
  email_sent_count: number
  is_expired: boolean
  is_valid: boolean
}

/**
 * Paginated invitation list response
 */
export interface InvitationListResponse {
  invitations: Invitation[]
  total: number
  page: number
  per_page: number
  has_more: boolean
}

/**
 * Result of bulk invitation operation
 */
export interface InvitationBulkResult {
  created: Invitation[]
  failed: Array<{
    email: string
    error: string
  }>
  total_created: number
  total_failed: number
}

/**
 * Public token information for invitation acceptance page
 */
export interface InvitationTokenInfo {
  email: string
  tenant_slug?: string
  invited_by_email?: string
  expires_at: string
  is_valid: boolean
  message?: string
}

/**
 * Query parameters for fetching invitations
 */
export interface InvitationQueryParams {
  /** Filter by status */
  status?: InvitationStatus
  /** Filter by statuses */
  statuses?: InvitationStatus[]
  /** Filter by client ID */
  client_id?: string
  /** Search by email or name */
  search?: string
  /** Include expired */
  include_expired?: boolean
  /** Page number */
  page?: number
  /** Items per page */
  per_page?: number
  /** Sort field */
  sort_by?: 'created_at' | 'email' | 'status' | 'expires_at'
  /** Sort direction */
  sort_order?: 'asc' | 'desc'
}

/**
 * Invitation store state
 */
export interface InvitationState {
  /** List of invitations */
  invitations: Invitation[]
  /** Current page */
  page: number
  /** Items per page */
  perPage: number
  /** Total count */
  total: number
  /** Has more pages */
  hasMore: boolean
  /** Loading state */
  isLoading: boolean
  /** Error message */
  error: string | null
  /** Current filters */
  filters: InvitationQueryParams
  /** Currently selected invitation */
  selectedInvitation: Invitation | null
}

/**
 * Options for the invitation composable
 */
export interface UseInvitationsOptions {
  /** Auto-load on mount */
  autoLoad?: boolean
  /** Initial filters */
  initialFilters?: InvitationQueryParams
  /** Items per page */
  perPage?: number
}
