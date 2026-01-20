# Next Session: Implement Aurora Frontend

## Backend Completed ✓

| Component | Status | Files |
|-----------|--------|-------|
| Schemas | ✓ | `aurora-be/schemas/users.py` |
| Service | ✓ | `aurora-be/services/user_service.py` |
| Router | ✓ | `aurora-be/routers/users.py` |
| Dependencies | ✓ | `aurora-be/dependencies/auth.py` |
| Unit Tests | ✓ | `aurora-be/tests/test_user_service.py` |
| Integration Tests | ✓ | `aurora-be/tests/test_users_router.py` |

## API Endpoints Available

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/aurora/users` | Create user | Tenant admin |
| GET | `/aurora/users` | List users (paginated) | Authenticated |
| GET | `/aurora/users/{id}` | Get user details | Authenticated |
| PUT | `/aurora/users/{id}` | Update user level/status | Tenant admin |
| DELETE | `/aurora/users/{id}` | Deactivate user (soft delete) | Tenant admin |

## What to Build

### Frontend Structure

```
aurora-fe/
├── views/
│   ├── UserList.vue        # Main user management view
│   └── UserDetail.vue      # User detail/edit view (optional)
├── components/
│   ├── UserTable.vue       # Data table for users
│   ├── UserForm.vue        # Create/edit user form
│   └── UserStatusBadge.vue # Active/inactive status indicator
├── composables/
│   └── useUsers.ts         # API calls via Evoke
├── stores/
│   └── userStore.ts        # Pinia store for user state
└── types/
    └── user.ts             # TypeScript interfaces
```

### Key Features

1. **UserList.vue**
   - Table with columns: Email, Level, Status, Actions
   - Pagination controls
   - "Add User" button (admin only)
   - Edit/Deactivate actions per row (admin only)
   - Search/filter (optional)

2. **UserForm.vue**
   - Email input (required, validated)
   - User level dropdown (tenant_admin / simple_user)
   - Submit/Cancel buttons
   - Used for both create and edit

3. **useUsers.ts composable**
   ```typescript
   // API calls via Evoke
   const createUser = (email: string, userLevel: string) => ...
   const listUsers = (page: number, perPage: number) => ...
   const getUser = (userId: string) => ...
   const updateUser = (userId: string, data: UpdateUserData) => ...
   const deactivateUser = (userId: string) => ...
   ```

4. **userStore.ts (Pinia)**
   - `users: User[]`
   - `loading: boolean`
   - `pagination: { page, perPage, total, hasMore }`
   - Actions: `fetchUsers()`, `createUser()`, `updateUser()`, `deactivateUser()`

### API Response Types

```typescript
interface User {
  id: string
  email: string
  user_level: 'tenant_admin' | 'simple_user'
  is_active: boolean
  tenant_id: string
  association_id: string
  created_at: string
  updated_at: string
}

interface UserListResponse {
  users: User[]
  total: number
  page: number
  per_page: number
  has_more: boolean
}
```

## To Continue

Say: **"Let's implement Aurora frontend - start with the Pinia store and composables"**

### Implementation Order

1. **Types** (`types/user.ts`) - TypeScript interfaces
2. **Composables** (`composables/useUsers.ts`) - API layer via Evoke
3. **Store** (`stores/userStore.ts`) - State management
4. **Components** - UI components
5. **Views** - Page-level components
6. **Navigation** - Wire up routes

## Reference: Existing Patterns

Check these repos for Vue/Pinia patterns used in the ecosystem:
- `tj-hand/mentor` → `mentor-fe/` (if exists)
- `tj-hand/evoke` → API client patterns
- `tj-hand/spark` → Component library patterns

## Development Approach

All code is developed directly on GitHub (no local cloning).
Use `mcp__github__push_files` to push changes.
