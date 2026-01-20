/**
 * TypeScript interfaces for Aurora stores
 *
 * Mirrors backend schemas from aurora-be/schemas/users.py
 */

// ==================== ENUMS ====================

export type UserLevel = 'tenant_admin' | 'simple_user';

// ==================== USER ====================

export interface User {
  id: string;
  email: string;
  user_level: UserLevel;
  is_active: boolean;
  tenant_id: string;
  association_id: string;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  email: string;
  user_level?: UserLevel;
}

export interface UserUpdate {
  user_level?: UserLevel;
  is_active?: boolean;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

// ==================== API RESPONSE ====================

export interface MessageResponse {
  message: string;
  success: boolean;
}

export interface PaginationParams {
  page?: number;
  per_page?: number;
  include_inactive?: boolean;
}
