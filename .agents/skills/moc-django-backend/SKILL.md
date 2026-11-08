---
name: moc-django-backend
description: Work on the Mộc Django API, models, permissions, migrations, and transactional business services.
---

# Mộc Django backend

Use for changes under `moc-backend/`.

## Project map

- Django applications own their domain models, serializers, views, and URLs (for example `reservations/`, `orders/`, `payments/`, `accounts/`, and `branches/`).
- Cross-model business operations belong in the relevant `services.py`; views should validate/request data, enforce permissions, call services, and serialize results.
- The system has bilingual compatibility surfaces. Preserve existing Vietnamese model/database names and API aliases unless the task explicitly migrates them; check serializers and frontend adapters before changing a field.
- Authentication, branch scoping, and staff roles are enforced by shared API permissions and queryset filtering. Do not treat a hidden frontend action as an access check.

## Implementation guidance

- Inspect neighboring code and existing API contracts before adding or changing an endpoint.
- Put multi-object state transitions in `transaction.atomic` services and lock rows in a consistent order when concurrent staff actions could conflict.
- Enforce table capacity, branch ownership, active-session uniqueness, payment state, and allowed status transitions on the backend.
- Add a migration when a persisted model/schema change requires one; keep migration names consistent with the app's existing conventions.
- Return the established serializer shape and error format. Keep compatibility aliases where existing clients still use them.
- Never put credentials, personal data, or local `.env` values in skill instructions or example output.
