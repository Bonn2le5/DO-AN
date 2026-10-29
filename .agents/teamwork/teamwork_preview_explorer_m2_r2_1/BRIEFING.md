# BRIEFING — 2026-10-14T09:51:00Z

## Mission
Formulate line-by-line fix recommendations for transaction scoping in tao_dat_ban, khau_tru_nguyen_lieu_bom, hoan_tra_nguyen_lieu_bom, process_ipn, and doi_trang_thai.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_1
- Original parent: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Milestone: Milestone 2 Iteration 2

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Deliver report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_1/handoff.md
- Formulate line-by-line fix recommendations for transaction scoping in tao_dat_ban, khau_tru_nguyen_lieu_bom, hoan_tra_nguyen_lieu_bom, process_ipn, and doi_trang_thai

## Current Parent
- Conversation ID: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Updated: 2026-10-14T09:44:01Z

## Investigation State
- **Explored paths**:
  * `moc-backend/reservations/services.py:tao_dat_ban` (lines 127–235) and `doi_trang_thai` (lines 236–275)
  * `moc-backend/foods/services.py:khau_tru_nguyen_lieu_bom` (lines 10–116) and `hoan_tra_nguyen_lieu_bom` (lines 119–170)
  * `moc-backend/payments/services.py:process_ipn` (lines 121–238)
  * `moc-backend/reservations/views.py:huy_dat_ban` (lines 118–141)
  * `tests/e2e/test_milestone2_verification.py`
  * Django compiler check `django.db.models.sql.compiler.SQLCompiler.as_sql` (line 816)
- **Key findings**:
  * Proved `SQLCompiler.as_sql` raises `TransactionManagementError: select_for_update cannot be used outside of a transaction.` when `connection.get_autocommit()` is True.
  * In `tao_dat_ban`, `with transaction.atomic():` only wrapped 1 line (`du_lieu.pop`), leaving `BanAn.objects.select_for_update()` and `DatBan` creation outside the transaction.
  * In `khau_tru_nguyen_lieu_bom` and `hoan_tra_nguyen_lieu_bom`, `with transaction.atomic():` was prematurely closed after the idempotency check, leaving `NguyenLieu.objects.select_for_update()` and stock updates outside the transaction.
  * In `process_ipn`, row lock on `ThanhToan` was released after line 154 before the amount check, idempotency check, and state updates, exposing the system to duplicate IPN race conditions.
  * In `doi_trang_thai`, `except Exception: pass` swallowed `ValidationError` from BOM deduction, allowing reservations to be confirmed despite zero ingredient stock.
  * In `reservations/views.py:huy_dat_ban`, `is_no_show` lacked permission check against non-staff users.
- **Unexplored areas**: None. All 5 required service methods and secondary review points fully analyzed and solved.

## Key Decisions Made
- Generated unified unified diff patch `transaction_scoping_fixes.patch` in working directory.
- Formulated line-by-line replacement recommendations with `@transaction.atomic` decorators and `transaction.on_commit()` cache hooks.
- Formulated test remediation recommendations for Phase 2 booking and unmocked transaction assertions.

## Artifact Index
- DISPATCH.md — Task instructions and dispatch log
- transaction_scoping_fixes.patch — Machine-applicable diff patch for all 5 targets
- handoff.md — Comprehensive 5-component handoff report
