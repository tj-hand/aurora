/**
 * Aurora Frontend Module
 *
 * User pre-registration and invitation management.
 *
 * Exports:
 * - useInvitationStore: Pinia store for invitation state management
 * - useInvitations: Composable for invitation management
 * - API functions: fetchInvitations, createInvitation, etc.
 * - Types: Invitation, InvitationFilter, InvitationStats, etc.
 */

// Store
export { useInvitationStore } from './stores'

// Composable
export { useInvitations } from './composables'
export type { UseInvitationsOptions } from './composables/useInvitations'

// API functions
export {
  fetchInvitations,
  fetchInvitation,
  fetchInvitationStats,
  createInvitation,
  resendInvitation,
  revokeInvitation,
  acceptInvitation,
} from './services/aurora-api'

// Types
export type {
  Invitation,
  InvitationStatus,
  InvitationCreate,
  InvitationFilter,
  InvitationList,
  InvitationStats,
  InvitationAccept,
  InvitationAcceptResponse,
  InvitationResendResponse,
  InvitationRevokeResponse,
  InvitationQueryParams,
  PaginationParams,
} from './types'
