---
name: moc-react-admin
description: Build or change Mộc's React and TypeScript customer or admin interfaces, including API integration, permissions, and operational states.
---

# Mộc React frontend

Use for changes under `moc-frontend/src/`.

## Project conventions

- The frontend uses React, TypeScript, Vite, Tailwind CSS, React Router, Zustand, and Axios.
- Admin pages and shared operational components live under `src/admin/`; customer-facing pages live under `src/pages/` and reusable UI under `src/components/`.
- Admin API mapping, status translation, and stores are centralized in `src/admin/api/admin.api.ts`. Prefer those adapters over direct endpoint calls from page components.
- Reuse existing primitives, drawers, tables, toasts, and permission hooks. Check `src/admin/permissions.ts` and the route guards before exposing staff actions.
- Keep user-facing copy in Vietnamese and use the established status labels and currency/date helpers.

## Implementation guidance

- Trace API response shapes through the adapter into the TypeScript types before changing either side of a contract.
- Represent loading, empty, error, busy, and terminal states clearly. Hide or disable actions that the current server state cannot accept.
- Keep forms and drawers usable on narrow screens, keyboard accessible, and consistent with nearby pages. For substantial visual redesigns, also apply the repository's `frontend-design` skill.
- Avoid duplicating business calculations that the backend owns, especially deposits, totals, branch access, and status transitions.
