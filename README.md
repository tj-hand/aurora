# Aurora

User pre-registration and invitation management for Spark Framework.

---

## What It Does

Aurora manages the user invitation workflow before authentication:

- **Pre-register users** - Invite users before they exist in the system
- **Send branded emails** - Invitation emails with custom messages via Matrix email provider
- **Token-based acceptance** - Secure SHA-256 hashed tokens for invitation links
- **Role pre-assignment** - Assign clients and role groups that apply on acceptance
- **Audit logging** - All actions logged to Reel

---

## What It Provides

### Backend Exports (`aurora-be/__init__.py`)

| Export | Type | Description |
|--------|------|-------------|
| `router` | FastAPI APIRouter | Mounts at `/api/v1/aurora/*` |
| `InvitationService` | Class | Core invitation business logic |
| `get_invitation_service()` | Function | FastAPI dependency |
| `Invitation` | SQLAlchemy Model | Invitation database model |
| `InvitationStatus` | Enum | PENDING, ACCEPTED, EXPIRED, REVOKED |

### Frontend Exports (`aurora-fe/index.ts`)

| Export | Type | Description |
|--------|------|-------------|
| `useInvitationStore()` | Pinia Store | State management |
| `useInvitations()` | Composable | CRUD + filtering + pagination |
| `fetchInvitations()` | Function | API client |
| `createInvitation()` | Function | API client |
| `Invitation` | Type | TypeScript interface |

### Permission Actions (registered with Mentor)

| Action | Valid Scopes | Description |
|--------|--------------|-------------|
| `aurora.invitations.view` | ACCOUNT, CLIENT | View invitations list and details |
| `aurora.invitations.create` | ACCOUNT, CLIENT | Create and resend invitations |
| `aurora.invitations.revoke` | ACCOUNT, CLIENT | Revoke pending invitations |

### API Endpoints

| Method | Path | Permission |
|--------|------|------------|
| GET | `/api/v1/aurora/invitations` | aurora.invitations.view |
| GET | `/api/v1/aurora/invitations/stats` | aurora.invitations.view |
| GET | `/api/v1/aurora/invitations/{id}` | aurora.invitations.view |
| POST | `/api/v1/aurora/invitations` | aurora.invitations.create |
| POST | `/api/v1/aurora/invitations/{id}/resend` | aurora.invitations.create |
| POST | `/api/v1/aurora/invitations/{id}/revoke` | aurora.invitations.revoke |
| POST | `/api/v1/aurora/invitations/accept` | Authenticated (token-based) |

### Database Table

`aurora_invitations` - See migration `20250213_000002_aurora_invitations.py`

---

## What It Expects

### Backend Dependencies

| Dependency | Import | Usage |
|------------|--------|-------|
| Matrix | `src.database.get_db`, `Base` | Database session, ORM base |
| Matrix | `src.providers.email.get_email_provider()` | Send invitation emails |
| Mentor | `src.modules.mentor.dependencies.*` | Auth, tenant context, permissions |
| Mentor | `src.modules.mentor.services.*` | User/tenant/client associations |
| Mentor | `get_action_registry()` | Action registration |
| Reel | `src.modules.reel.get_reel_service` | Audit logging (optional) |

### Frontend Dependencies

| Dependency | Import | Usage |
|------------|--------|-------|
| Evoke | `@/evoke` | HTTP client with auth headers |
| Pinia | `pinia` | State management |
| Vue 3 | Composition API | Composables, refs, computed |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AURORA_INVITATION_EXPIRY_DAYS` | 7 | Days until expiry |
| `AURORA_TOKEN_LENGTH` | 32 | Token length |
| `AURORA_COMPANY_NAME` | "Your Company" | Email branding |
| `AURORA_APP_URL` | http://localhost:3000 | Invitation link base |

---

## What It Never Does

| Boundary | Responsible Module |
|----------|-------------------|
| User authentication | Guardian |
| JWT token management | Guardian |
| User identity storage | Guardian |
| Tenant/client management | Mentor |
| Permission enforcement | Mentor |
| Role group definitions | Mentor |
| Email transport | Matrix (email provider) |
| UI components | Stage (blade-aurora) |

---

## File Structure

```
aurora/
├── aurora-be/                           # Backend (Python/FastAPI)
│   ├── __init__.py                      # Module exports
│   ├── router.py                        # Main router (/v1/aurora)
│   ├── config.py                        # AuroraConfig settings
│   ├── dependencies.py                  # FastAPI DI
│   ├── actions.py                       # Mentor action registration
│   ├── models/
│   │   ├── __init__.py
│   │   └── invitation.py                # Invitation SQLAlchemy model
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── invitation.py                # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   └── invitation_service.py        # Business logic
│   ├── routers/
│   │   ├── __init__.py
│   │   └── invitations.py               # API endpoints
│   └── alembic/versions/
│       └── 20250213_000002_aurora_invitations.py
├── aurora-fe/                           # Frontend (Vue.js/TypeScript)
│   ├── index.ts                         # Module exports
│   ├── types/index.ts                   # TypeScript interfaces
│   ├── services/
│   │   ├── index.ts
│   │   └── aurora-api.ts                # HTTP client
│   ├── stores/
│   │   ├── index.ts
│   │   └── invitationStore.ts           # Pinia store
│   ├── composables/
│   │   ├── index.ts
│   │   └── useInvitations.ts            # Vue composable
│   └── locales/
│       ├── en.json                      # English
│       └── pt-BR.json                   # Portuguese
├── deploy.sh                            # Deployment script
├── README.md                            # This file
└── TESTS.md                             # Test documentation
```

---

## Usage

### Frontend - Creating Invitations

```typescript
import { useInvitations } from '@/aurora'

const { create, isCreating, error } = useInvitations()

await create({
  email: 'newuser@example.com',
  name: 'John Doe',
  client_ids: ['client-uuid'],
  message: 'Welcome to our team!',
})
```

### Frontend - Listing Invitations

```typescript
const { invitations, loadInvitations, filterByStatus, stats } = useInvitations({
  autoLoad: true,
  autoLoadStats: true,
})
```

### Backend - Direct Service Usage

```python
from src.modules.aurora import InvitationService

service = InvitationService(db)
invitation, token = await service.create(
    email="user@example.com",
    tenant_id=tenant_id,
    invited_by=current_user.id,
)
await service.send_invitation_email(invitation, token, "Acme Corp")
```

---

## Stack Specification

See [architecture.md](https://github.com/tj-hand/spark/blob/main/architecture.md) section 4.3 for full Aurora specification.

---

## Invitation Flow

```
1. Admin creates invitation (aurora.invitations.create)
   └─> Invitation record created (PENDING)
   └─> SHA-256 token hash stored
   └─> Email sent via Matrix

2. User clicks email link → /accept-invitation?token=xxx

3. User authenticates (if needed) via Guardian

4. POST /aurora/invitations/accept with token
   └─> Token validated (hash match, not expired/revoked)
   └─> Mentor creates user-tenant association
   └─> Mentor assigns clients and role groups
   └─> Status updated to ACCEPTED
   └─> Reel logs acceptance
```
