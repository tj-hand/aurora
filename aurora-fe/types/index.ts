/**
 * Aurora types - TypeScript interfaces for invitation management
 */

/**
 * Invitation status states
 */
export type InvitationStatus = 'PENDING' | 'ACCEPTED' | 'EXPIRED' | 'REVOKED'

/**
 * Invitation from the API
 */
export interface Invitation {
  id: string
  email: string
  name: string | null
  tenant_id: string
  client_ids: string[] | null
  role_group_ids: string[] | null
  status: InvitationStatus
  invited_by: string
  created_at: string
  expires_at: string
  accepted_at: string | null
  revoked_at: string | null
  revoked_by: string | null
  message: string | null
}

/**
 * Create invitation request
 */
export interface InvitationCreate {
  email: string
  name?: string
  client_ids?: string[]
  role_group_ids?: string[]
  message?: string
}

/**
 * Filter parameters for invitation queries
 */
export interface InvitationFilter {
  status?: InvitationStatus
  email?: string
  invited_by?: string
  created_after?: string
  created_before?: string
}

/**
 * Paginated list of invitations
 */
export interface InvitationList {
  items: Invitation[]
  total: number
  page: number
  page_size: number
  pages: number
}

/**
 * Invitation statistics
 */
export interface InvitationStats {
  total: number
  pending: number
  accepted: number
  expired: number
  revoked: number
  sent_today: number
  sent_this_week: number
}

/**
 * Accept invitation request
 */
export interface InvitationAccept {
  token: string
}

/**
 * Accept invitation response
 */
export interface InvitationAcceptResponse {
  success: boolean
  message: string
  tenant_id: string
  tenant_name: string | null
}

/**
 * Resend invitation response
 */
export interface InvitationResendResponse {
  success: boolean
  message: string
}

/**
 * Revoke invitation response
 */
export interface InvitationRevokeResponse {
  success: boolean
  message: string
}

/**
 * Pagination parameters
 */
export interface PaginationParams {
  page?: number
  page_size?: number
}

/**
 * Combined query parameters for invitation listing
 */
export type InvitationQueryParams = InvitationFilter & PaginationParams
