# BRIEFING — 2026-10-14T16:31:00Z

## Mission
Investigate Bug 2 (`orders/services.py:83` setting `trong_so=6` instead of `4`), audit all `TuongTacMonAn` creation/updates across the codebase against Feature 20, verify reproduction test, and design exact remediation patch.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_2
- Original parent: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Milestone: Milestone 4 (Interaction Weights & Data Consistency)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement directly into source files
- Audit all `TuongTacMonAn` creation/updates against Feature 20 (`xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5`)
- Deliver 5-component handoff report with exact file locations and code diffs to `handoff.md` and send message to orchestrator

## Current Parent
- Conversation ID: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Updated: 2026-10-14T16:26:23Z

## Investigation State
- **Explored paths**:
  - `moc-backend/orders/services.py`: line 83 (`trong_so=6` on `DAT_MON`)
  - `moc-backend/recommendations/services.py`: `TRONG_SO_TUONG_TAC` & `ALIAS_TRONG_SO`
  - `moc-backend/recommendations/serializers.py`: `TuongTacMonAnSerializer.validate`
  - `moc-backend/recommendations/models.py`: `TuongTacMonAn` & `LoaiTuongTac`
  - `moc-backend/reviews/views.py`: `TuongTacMonAn.objects.create(..., trong_so=5)`
  - `moc-backend/foods/views.py`: `MonAnViewSet`
  - `moc-backend/carts/views.py`: `GioHangViewSet`
  - `tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py`: Bug 1, 2, 3 reproduction harness
- **Key findings**:
  - Bug 2 pinpointed: `moc-backend/orders/services.py:83` passes `trong_so=6` for `TuongTacMonAn.LoaiTuongTac.DAT_MON`. Feature 20 strictly specifies `dat_mon=4`.
  - Audited all interaction creation/update points: `reviews/views.py:42` correctly sets `trong_so=5`, `recommendations/serializers.py:48-49` correctly defaults weights according to `TRONG_SO_TUONG_TAC` (`xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5`). Only `orders/services.py:83` was out of compliance.
  - Empirically verified via Python simulation that changing `orders/services.py:83` to `trong_so=4` passes `test_reproduce_bug_2_order_service_interaction_weight_is_6_not_4` in `tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py`.
- **Unexplored areas**: None within the scope of Milestone 4 Bug 2 and Feature 20 audit.

## Key Decisions Made
- Architecture of remediation: change `trong_so=6` to `trong_so=4` in `moc-backend/orders/services.py:83`.
- In addition, verified that Bug 1 (`GoiYMonAnViewSet.queryset` and `get_queryset`) and Bug 3 (signal cache invalidation) can be remediated alongside Bug 2 to achieve 100% pass across all 3 tests in the reproduction suite.

## Artifact Index
- DISPATCH.md — Dispatch instructions
- BRIEFING.md — Working memory and status
- progress.md — Liveness heartbeat
- remediation_bug2_orders_services.patch — Standalone patch for Bug 2
- remediation_m4_all_bugs.patch — Comprehensive patch for M4 remediation (Bugs 1, 2, 3)
- handoff.md — Final 5-component report
