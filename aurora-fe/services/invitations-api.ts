/**
 * Aurora Frontend - Invitations API Client
 *
 * HTTP client for invitation CRUD operations.
 */

import type {
  Invitation,
  InvitationCreate,
  InvitationResend,
  InvitationRevoke,
  InvitationBulkCreate,
  InvitationListResponse,
  InvitationBulkResult,
  InvitationTokenInfo,
  InvitationQueryParams
} from '../types/invitations'

/**
 * Base API URL for aurora service
 */
const API_BASE = '/api/v1/aurora'

/**
 * Helper to build query string from params
 */
function buildQueryString(params: Record<string, unknown>): string {
  const searchParams = new URLSearchParams()

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(v => searchParams.append(key, String(v)))
      } else {
        searchParams.append(key, String(value))
      }
    }
  }

  const query = searchParams.toString()
  return query ? `?${query}` : ''
}

/**
 * Helper to handle API responses
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP error: ${response.status}`)
  }
  return response.json()
}

/**
 * Create a new invitation
 *
 * @param data - Invitation creation data
 * @returns Created invitation
 */
export async function createInvitation(data: InvitationCreate): Promise<Invitation> {
  const response = await fetch(`${API_BASE}/invitations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return handleResponse<Invitation>(response)
}

/**
 * Create multiple invitations in bulk
 *
 * @param data - Bulk invitation data
 * @returns Bulk creation result
 */
export async function createInvitationsBulk(
  data: InvitationBulkCreate
): Promise<InvitationBulkResult> {
  const response = await fetch(`${API_BASE}/invitations/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return handleResponse<InvitationBulkResult>(response)
}

/**
 * Fetch invitations with optional filters
 *
 * @param params - Query parameters
 * @returns Paginated invitation list
 */
export async function fetchInvitations(
  params: InvitationQueryParams = {}
): Promise<InvitationListResponse> {
  const query = buildQueryString(params)
  const response = await fetch(`${API_BASE}/invitations${query}`)
  return handleResponse<InvitationListResponse>(response)
}

/**
 * Fetch a single invitation by ID
 *
 * @param invitationId - Invitation ID
 * @returns Invitation details
 */
export async function fetchInvitation(invitationId: string): Promise<Invitation> {
  const response = await fetch(`${API_BASE}/invitations/${invitationId}`)
  return handleResponse<Invitation>(response)
}

/**
 * Fetch invitation token info (public endpoint)
 *
 * @param token - Invitation token
 * @returns Token info for acceptance page
 */
export async function fetchInvitationTokenInfo(token: string): Promise<InvitationTokenInfo> {
  const response = await fetch(`${API_BASE}/invitations/token/${token}`)
  return handleResponse<InvitationTokenInfo>(response)
}

/**
 * Resend invitation email
 *
 * @param invitationId - Invitation ID
 * @param data - Optional custom message
 * @returns Updated invitation
 */
export async function resendInvitation(
  invitationId: string,
  data?: InvitationResend
): Promise<Invitation> {
  const response = await fetch(`${API_BASE}/invitations/${invitationId}/resend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data || {})
  })
  return handleResponse<Invitation>(response)
}

/**
 * Revoke an invitation
 *
 * @param invitationId - Invitation ID
 * @param data - Optional revocation reason
 * @returns Updated invitation
 */
export async function revokeInvitation(
  invitationId: string,
  data?: InvitationRevoke
): Promise<Invitation> {
  const response = await fetch(`${API_BASE}/invitations/${invitationId}/revoke`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data || {})
  })
  return handleResponse<Invitation>(response)
}

/**
 * Accept an invitation (public endpoint)
 *
 * @param token - Invitation token
 * @returns Accepted invitation
 */
export async function acceptInvitation(token: string): Promise<Invitation> {
  const response = await fetch(`${API_BASE}/invitations/accept/${token}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  return handleResponse<Invitation>(response)
}

/**
 * Check health of invitation service
 *
 * @returns Health check result
 */
export async function checkHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/health`)
  return handleResponse<{ status: string }>(response)
}
