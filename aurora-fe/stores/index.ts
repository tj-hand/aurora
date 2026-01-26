/**
 * Aurora Stores Index
 *
 * Exports all Pinia stores for the Aurora module.
 *
 * Aurora orchestrates Guardian (identity) and Mentor (tenant associations)
 * to provide a unified user management interface.
 */

// User store
export { useUserStore } from './userStore';

// Invitation store
export { useInvitationStore } from './invitations';

// Re-export types
export * from './types';
