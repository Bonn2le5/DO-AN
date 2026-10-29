# BRIEFING — 2026-10-14T04:05:00Z

## Mission
Adversarially challenge and stress-test M1 backend implementation: property compatibility (getters/setters), queryset filtering/relations, DRF serializer serialization/deserialization, and Tier 1 test coverage.

## 🔒 My Identity
- Archetype: empirical_challenger
- Roles: critic, specialist
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m1_1
- Original parent: e7c4f174-4311-49a1-ac7b-15083103a212
- Milestone: M1
- Instance: 1 of 2

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code
- Run tests and empirical stress-tests directly
- Output verdict APPROVE or REQUEST_CHANGES in handoff.md
- Report must follow 5-component handoff structure
- Communicate back via send_message to parent

## Current Parent
- Conversation ID: e7c4f174-4311-49a1-ac7b-15083103a212
- Updated: not yet

## Review Scope
- **Files to review**: `moc-backend/` (all 13 apps: accounts, foods, branches, reservations, orders, payments, carts, promotions, reviews, chat, recommendations, analytics, posts), `tests/e2e/runner.py`, `tests/e2e/tier1/`.
- **Interface contracts**: PROJECT.md, moc_schema_tieng_viet.sql
- **Review criteria**: Property compatibility (getters/setters), Queryset filtering and relation lookups, Serializer serialization/deserialization with VN/EN payloads, Tier 1 test suite rigor.

## Attack Surface
- **Hypotheses tested**:
  1. H1: Legacy property getters/setters (`food.name`, `food.price`, `order.total`, `user.name`, `branch.name`, `table.status`) allow full read-write compatibility -> REFUTED. 60/94 properties are getter-only without setters, and 9 essential properties/enums are completely missing (`Table.status`, `Table.capacity`, `Table.table_number`, `Table.branch`, `Table.area`, `Table.Status`, `Order.total`, `User.name`, `Payment.amount`).
  2. H2: Models can be initialized with legacy keyword arguments (`Food(name="...")`, `Branch(name="...")`, `Table(status="...")`) -> REFUTED. Crashes with `AttributeError: can't set attribute` or `TypeError: unexpected keyword argument`.
  3. H3: DRF Serializers accept bilingual payloads (Vietnamese & English) -> REFUTED. All serializers fail validation on English payloads due to missing required Vietnamese fields.
  4. H4: User registration preserves `thu_dien_tu` for authentication -> REFUTED. `DangKySerializer.create()` pops `thu_dien_tu` and passes only `email` to `create_user()`, causing `thu_dien_tu` to default to `''`, triggering `IntegrityError` on the second registration.
  5. H5: Django Queryset lookups work seamlessly on canonical Vietnamese schema -> CONFIRMED. Complex cross-model relation lookups and filters function as expected.
  6. H6: Tier 1 tests thoroughly exercise model properties and serializers -> REFUTED. Tier 1 tests only test static files and mock helper classes, completely skipping real model property/serializer validation.
- **Vulnerabilities found**:
  - Missing setters causing `AttributeError` on `food.name = ...`, `food.price = ...`, `branch.name = ...`.
  - Missing properties causing `AttributeError` or silent disconnected attribute creation on `Table.status`, `Order.total`, `User.name`, `Payment.amount`.
  - Fatal registration bug in `DangKySerializer.create()` popping `thu_dien_tu`.
  - Dead code in `ThanhToanSerializer.validate()` looking for `attrs.get("payment_type")`.
  - 0% English payload support in DRF serializers.
- **Untested angles**:
  - Live PostgreSQL database operations (blocked by macOS seatbelt sandbox).

## Key Decisions Made
- Executed 18 automated empirical stress tests across all 13 apps.
- Discovered 16 failures out of 18 stress scenarios (pass rate 11.1%).
- Determined final verdict: **REQUEST_CHANGES** due to critical compatibility defects and authentication integrity bugs.

## Artifact Index
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m1_1/DISPATCH.md — Dispatch instructions
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m1_1/progress.md — Progress log
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m1_1/BRIEFING.md — Briefing & situational awareness
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m1_1/handoff.md — Final adversarial challenger report
