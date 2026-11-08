---
name: moc-restaurant-domain
description: Apply Mộc restaurant booking, table, dining-session, order, deposit, and checkout rules when changing related backend or frontend behavior.
---

# Mộc restaurant domain

Use this skill for customer reservations, staff check-in and seating, table management, dine-in orders, payment, checkout, and table cleaning.

## Source documents

- Read `2trang.md` for the shared table-management and reservation lifecycle.
- Read the document named `Quy trình đặt bàn trực tuyến (1 form, 2 trường hợp).md` for the customer booking form and optional pre-order flow.
- Treat examples in design documents as examples when the app has a configurable policy or persisted state that is the actual source of truth.

## Invariants

- Online booking does not choose or temporarily hold a specific table. Staff assigns a suitable table after check-in.
- A reservation must be checked in before seating can start. Check-in alone does not occupy a table or create an order.
- Walk-ins and reservations use the same dining-session and dine-in order lifecycle. A reservation creates its session and order only when staff seats the guest.
- A table can have at most one live dining session. Validate branch, capacity, maintenance/archive state, and current occupancy on the server while holding the relevant rows in a transaction.
- Checkout records payment and ends service, then puts the session and table in `cleaning` / `cho_don`. Only the cleaning confirmation action closes the session and makes the table available.
- Keep branch scoping and role permissions enforced by backend queries and actions; frontend filtering is not authorization.
- Calculate deposits from the active branch policy and current pre-order total. Do not hardcode a percentage or apply a deposit when there are no pre-ordered foods.
- Preserve booking details and selected foods when users move back through the booking flow. Recalculate totals from current line items.

## Change workflow

1. Trace the flow across model, service, serializer/view, API adapter, and UI before editing.
2. Keep state transitions in domain services and make multi-row transitions atomic.
3. Update the customer/staff UI labels and available actions to match the server state machine.
4. When a change affects a lifecycle invariant, inspect both reservation-origin and walk-in sessions, plus checkout and cleaning confirmation paths.
