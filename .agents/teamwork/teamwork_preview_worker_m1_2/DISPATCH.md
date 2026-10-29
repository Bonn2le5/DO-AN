# Dispatch: Milestone 1 Iteration 2 Implementation Worker

## Mandatory Integrity Warning
> DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Objective
Implement all fixes identified by Reviewer 1 and Challenger 1, following the exact recipes in the 3 Milestone 1 Iteration 2 Explorer reports.

## Key Files to Read Before Implementing
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_1/handoff.md` (Property Setters, LegacyKwargsMixin, Table/Order/Payment properties)
4. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_2/handoff.md` (DangKySerializer email fix, XacThucViewSet action aliases, DualPayloadMixin)
5. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_3/handoff.md` (Admin registrations for 12 apps and 18-case adversarial test harness)
6. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m1_1/handoff.md` (Detailed failure output)

## Implementation Tasks
1. **Property Setters & LegacyKwargsMixin (Explorer 1)**:
   - Implement `LegacyKwargsMixin` (or model `__init__` mapping) so legacy kwargs like `Food(name=..., price=...)`, `Branch(name=...)`, `Table(status=...)` work.
   - Add property setters (`@<prop>.setter`) for all legacy properties so `food.name = ...` and `food.price = ...` do not raise `AttributeError`.
   - Ensure `Table` has `status`, `capacity`, `table_number`, `branch`, `area`, `Table.Status = BanAn.TrangThaiBan`.
   - Ensure `Order.total`, `User.name`, `Payment.amount` exist with getters and setters.
2. **Registration, Auth Actions & Bilingual Serializers (Explorer 2)**:
   - Fix `DangKySerializer.create()` in `accounts/serializers.py` so `thu_dien_tu` is properly saved to the database.
   - Add `@action` methods in `XacThucViewSet`: `register`, `profile`, `change_password`.
   - Implement `DualPayloadMixin` on serializers to accept English payload keys.
3. **Admin Registrations for 12 Apps (Explorer 3)**:
   - Register models in `admin.py` across `foods`, `branches`, `reservations`, `orders`, `payments`, `promotions`, `chat`, `recommendations`, `carts`, `reviews`, `posts`, and `analytics`.
4. **Verification**:
   - Run `python manage.py check` (must exit code 0).
   - Run the 18-case adversarial test harness from Explorer 3:
     `python /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_3/proposed_test_adversarial_challenger_m1.py` (must pass 18/18).
   - Run `python tests/e2e/runner.py --tier 1` (must pass 30/30).

## Deliverables
Write your handoff report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m1_2/handoff.md`
and notify Orchestrator via `send_message`.


## 2026-10-14T04:22:17Z
You are Milestone 1 Iteration 2 Implementation Worker for Web App Nhà hàng Mộc.
Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m1_2
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m1_2/DISPATCH.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your task:
Apply the exact fixes from the 3 M1 R2 Explorer handoff reports:
1. Property setters & LegacyKwargsMixin for model instantiation across all 13 apps (from Explorer 1 report).
2. DangKySerializer email fix, XacThucViewSet action aliases (register, profile, change_password), and DualPayloadMixin for serializers (from Explorer 2 report).
3. Admin.py registrations across all 12 apps (from Explorer 3 report).
4. Run `python manage.py check`, the 18-case adversarial test script from Explorer 3, and `python tests/e2e/runner.py --tier 1`.
Document all verification outputs in /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m1_2/handoff.md and notify me via send_message when done.
