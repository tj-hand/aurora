/**
 * Aurora API Service
 *
 * HTTP client functions for invitation endpoints.
 * Uses Evoke client for authenticated requests.
 */

import { createClient } from '@/evoke'
import type {
  Invitation,
  InvitationList,
  InvitationStats,
  InvitationQueryParams,
  InvitationCreate,
  InvitationAccept,
  InvitationAcceptResponse,
  InvitationResendResponse,
  InvitationRevokeResponse,
} from '../types'

// Create Evoke client instance
const client = createClient({
  baseURL: '/api',
})

/**
 * Build query string from params object
 */
function buildQueryParams(params: InvitationQueryParams): URLSearchParams {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value))
    }
  })

  return searchParams
}

/**
 * Fetch paginated list of invitations
 */
export async function fetchInvitations(params: InvitationQueryParams = {}): Promise<InvitationList> {
  const queryParams = buildQueryParams(params)
  const queryString = queryParams.toString()
  const url = queryString ? `/v1/aurora/invitations?${queryString}` : '/v1/aurora/invitations'

  const response = await client.get<InvitationList>(url)
  return response.data
}

/**
 * Fetch a single invitation by ID
 */
export async function fetchInvitation(invitationId: string): Promise<Invitation> {
  const response = await client.get<Invitation>(`/v1/aurora/invitations/${invitationId}`)
  return response.data
}

/**
 * Fetch invitation statistics for the current tenant
 */
export async function fetchInvitationStats(): Promise<InvitationStats> {
  const response = await client.get<InvitationStats>('/v1/aurora/invitations/stats')
  return response.data
}

/**
 * Create a new invitation
 */
export async function createInvitation(data: InvitationCreate): Promise<Invitation> {
  const response = await client.post<Invitation>('/v1/aurora/invitations', data)
  return response.data
}

/**
 * Resend an invitation email
 */
export async function resendInvitation(invitationId: string): Promise<InvitationResendResponse> {
  const response = await client.post<InvitationResendResponse>(
    `/v1/aurora/invitations/${invitationId}/resend`
  )
  return response.data
}

/**
 * Revoke a pending invitation
 */
export async function revokeInvitation(invitationId: string): Promise<InvitationRevokeResponse> {
  const response = await client.post<InvitationRevokeResponse>(
    `/v1/aurora/invitations/${invitationId}/revoke`
  )
  return response.data
}

/**
 * Accept an invitation using a token
 */
export async function acceptInvitation(data: InvitationAccept): Promise<InvitationAcceptResponse> {
  const response = await client.post<InvitationAcceptResponse>('/v1/aurora/invitations/accept', data)
  return response.data
}
