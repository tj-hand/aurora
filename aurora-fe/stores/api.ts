/**
 * Shared Evoke API Client for Aurora Module
 *
 * All Aurora stores use this client for authenticated API calls.
 * The auth token is automatically included from Guardian's session.
 *
 * Deployment Order (per repos.txt):
 * 1. Evoke (API client) → deploys to @/evoke
 * 2. Guardian (auth) → sets token via evoke.setToken()
 * 3. Aurora (user management) → uses shared Evoke client
 */
import { createClient } from '@/evoke';

// Create shared evoke client for Aurora API calls
// baseURL points to Matrix backend through Ether gateway
export const api = createClient({
  baseURL: import.meta.env.VITE_API_URL || '/api',
});

// API prefix for Aurora routes
export const API_PREFIX = '/v1/aurora';
