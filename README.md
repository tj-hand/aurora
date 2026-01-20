# Aurora 🌅

**User management and pre-registration module for Spark Stack**

Aurora brings users into existence by orchestrating Guardian (identity) and Mentor (tenant association).

## Theme Fit

| Module | Role | Symbol |
|--------|------|--------|
| **Guardian** | Protects identity | Shield |
| **Mentor** | Guides tenant relationships | Wisdom |
| **Aurora** | Brings users into existence | Dawn 🌅 |

## Responsibilities

1. User CRUD (create/read/update/deactivate)
2. Assign users to tenants/clients
3. Orchestrates Guardian (identity) + Mentor (tenant association)

## Architecture Flow

```
Admin creates user → Aurora API →
    1. Guardian: Create guardian_users record
    2. Mentor: Create UserTenantAssociation
    3. Aurora: Store user metadata (optional)
```

## Deploy Order

```
Guardian → Mentor → Aurora → Other modules
```

## Structure

```
aurora/
├── spark.json          # Module configuration
├── deploy.sh           # Root deployment orchestrator
├── aurora-be/          # Backend (FastAPI)
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   ├── routers/        # API endpoints
│   └── migrations/     # Alembic migrations
└── aurora-fe/          # Frontend (Vue 3)
    ├── components/     # Vue components
    ├── stores/         # Pinia stores
    ├── composables/    # Vue composables
    ├── views/          # Page views
    ├── routes.js       # Vue Router routes
    └── navigation.js   # Nav menu items
```

## Deployment

```bash
# Via Spark
./spark deploy aurora

# Standalone
./deploy.sh
./deploy.sh --migrate
```

## Dependencies

- **Guardian**: Identity management
- **Mentor**: Tenant/permission management
- **Evoke**: API client (frontend)
