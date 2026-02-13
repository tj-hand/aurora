# Aurora - Test Documentation

## Validated Tests

### Backend Integration Tests (Blocked - Not Yet Deployed)

Aurora has not been deployed to a test project yet. The following tests are planned but require full stack deployment.

| Test | Status | Notes |
|------|--------|-------|
| Database migration | PENDING | Requires deployed Matrix + PostgreSQL |
| API endpoint connectivity | PENDING | Requires Manifast router registration |
| Mentor permission checks | PENDING | Requires Mentor + Guardian stack |

### Frontend Unit Tests (Blocked - No Test Framework)

| Test | Status | Notes |
|------|--------|-------|
| Store state management | PENDING | Requires Vitest setup in Infinity |
| Composable behavior | PENDING | Requires Vitest setup in Infinity |
| API client functions | PENDING | Requires MSW or mock setup |

---

## Pending Tests

### Test: Create Invitation Flow

**Blocked by:** Full stack deployment (Matrix + Mentor + Guardian + Reel)

```
Test Steps:
1. POST /api/v1/aurora/invitations with valid data
2. Verify invitation created in database
3. Verify token hash is SHA-256 of returned token
4. Verify email sent via Matrix email provider
5. Verify Reel audit log created

Expected:
- 201 Created response
- Invitation with status PENDING
- expires_at = created_at + 7 days (default)
```

### Test: Accept Invitation Flow

**Blocked by:** Full stack deployment + Mentor services

```
Test Steps:
1. Create invitation via API
2. POST /api/v1/aurora/invitations/accept with token
3. Verify Mentor creates user-tenant association
4. Verify Mentor assigns clients
5. Verify Mentor assigns role groups
6. Verify invitation status = ACCEPTED

Expected:
- 200 OK with tenant_id and tenant_name
- User now associated with tenant in Mentor
```

### Test: Duplicate Invitation Prevention

**Blocked by:** Database deployment

```
Test Steps:
1. Create invitation for email@example.com
2. Attempt to create another invitation for same email in same tenant

Expected:
- 400 Bad Request
- Error: "Pending invitation already exists for {email}"
```

### Test: Token Expiry

**Blocked by:** Database deployment

```
Test Steps:
1. Create invitation
2. Manually set expires_at to past date
3. POST /api/v1/aurora/invitations/accept with token

Expected:
- 400 Bad Request
- Error: "Invitation has expired"
- Invitation status updated to EXPIRED
```

### Test: Revoke Invitation

**Blocked by:** Full stack deployment

```
Test Steps:
1. Create invitation (PENDING)
2. POST /api/v1/aurora/invitations/{id}/revoke

Expected:
- 200 OK
- Invitation status = REVOKED
- revoked_at timestamp set
- revoked_by = current user ID
```

### Test: Permission Enforcement

**Blocked by:** Mentor permission system

```
Test Steps:
1. User without aurora.invitations.create permission
2. POST /api/v1/aurora/invitations

Expected:
- 403 Forbidden
```

### Test: Frontend Store State

**Blocked by:** Vitest setup

```
Test Steps:
1. Call loadInvitations()
2. Verify isLoading transitions: false -> true -> false
3. Verify invitations populated
4. Verify pagination state updated
```

### Test: Frontend Composable

**Blocked by:** Vitest setup + component testing

```
Test Steps:
1. Mount component with useInvitations({ autoLoad: true })
2. Verify loadInvitations called on mount
3. Verify store state exposed correctly
```

---

## Coverage Map

### Responsibilities to Tests

| Responsibility | Test | Status |
|----------------|------|--------|
| Generate secure tokens | Create Invitation Flow | PENDING |
| Hash tokens (SHA-256) | Create Invitation Flow | PENDING |
| Create invitation | Create Invitation Flow | PENDING |
| Prevent duplicates | Duplicate Invitation Prevention | PENDING |
| Send invitation email | Create Invitation Flow | PENDING |
| Accept invitation | Accept Invitation Flow | PENDING |
| Validate token on accept | Accept Invitation Flow | PENDING |
| Check expiry on accept | Token Expiry | PENDING |
| Revoke invitation | Revoke Invitation | PENDING |
| Resend invitation | (Not tested yet) | PENDING |
| List invitations with filters | (Not tested yet) | PENDING |
| Calculate statistics | (Not tested yet) | PENDING |
| Expire old invitations | (Not tested yet) | PENDING |

### Deliveries to Tests

| Delivery | Test | Status |
|----------|------|--------|
| POST /invitations | Create Invitation Flow | PENDING |
| POST /invitations/accept | Accept Invitation Flow | PENDING |
| POST /invitations/{id}/revoke | Revoke Invitation | PENDING |
| POST /invitations/{id}/resend | (Not tested yet) | PENDING |
| GET /invitations | (Not tested yet) | PENDING |
| GET /invitations/stats | (Not tested yet) | PENDING |
| GET /invitations/{id} | (Not tested yet) | PENDING |
| useInvitationStore | Frontend Store State | PENDING |
| useInvitations | Frontend Composable | PENDING |
| aurora.invitations.view | Permission Enforcement | PENDING |
| aurora.invitations.create | Permission Enforcement | PENDING |
| aurora.invitations.revoke | Permission Enforcement | PENDING |

### Expectations to Tests

| Expectation | Test | Status |
|-------------|------|--------|
| Matrix database | All backend tests | PENDING |
| Matrix email provider | Create Invitation Flow | PENDING |
| Mentor CurrentUser | All authenticated endpoints | PENDING |
| Mentor TenantContext | List, Create, Revoke | PENDING |
| Mentor require_permission | Permission Enforcement | PENDING |
| Mentor TenantService | Accept Invitation Flow | PENDING |
| Mentor RoleService | Accept Invitation Flow | PENDING |
| Reel logging | Create Invitation Flow | PENDING |
| Evoke HTTP client | All frontend tests | PENDING |

---

## Test Priority

### High Priority (Core Flow)

1. **Create Invitation Flow** - Core functionality
2. **Accept Invitation Flow** - Core functionality
3. **Permission Enforcement** - Security

### Medium Priority (Error Handling)

4. **Duplicate Invitation Prevention** - Data integrity
5. **Token Expiry** - Security
6. **Revoke Invitation** - Admin functionality

### Lower Priority (Features)

7. **List with Filters** - UX
8. **Statistics** - Dashboard
9. **Resend** - Admin convenience

---

## Deployment Checklist for Testing

Before running tests, ensure:

- [ ] Matrix deployed with PostgreSQL
- [ ] Guardian deployed and functional
- [ ] Mentor deployed with permissions system
- [ ] Reel deployed (optional, for logging tests)
- [ ] Aurora migration applied: `alembic upgrade head`
- [ ] Aurora router registered in Manifast
- [ ] Test user created with appropriate permissions
- [ ] Frontend test framework (Vitest) configured

---

## Manual Testing Commands

### Backend (via httpie or curl)

```bash
# Create invitation (requires JWT token)
http POST :8000/api/v1/aurora/invitations \
  Authorization:"Bearer $TOKEN" \
  email="test@example.com" \
  name="Test User"

# List invitations
http GET :8000/api/v1/aurora/invitations \
  Authorization:"Bearer $TOKEN"

# Accept invitation (requires token from email)
http POST :8000/api/v1/aurora/invitations/accept \
  Authorization:"Bearer $TOKEN" \
  token="invitation-token-here"
```

### Database Verification

```sql
-- Check invitation created
SELECT id, email, status, created_at, expires_at
FROM aurora_invitations
ORDER BY created_at DESC
LIMIT 5;

-- Check for duplicate prevention index
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'aurora_invitations';
```
