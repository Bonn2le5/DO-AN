# BRIEFING — 2026-10-14T16:24:10Z

## Mission
Adversarially and empirically stress-test Milestone 4 AI Recommendation Engine for Web App Nhà hàng Mộc.

## 🔒 My Identity
- Archetype: empirical_challenger
- Roles: critic, specialist
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_1
- Original parent: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Milestone: Milestone 4 (Recommendation Engine)
- Instance: 1 of 1

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code
- Empirical verification required: must execute tests directly, reproduce any claimed bugs
- High-level verdict: APPROVE or REQUEST_CHANGES with concrete empirical evidence

## Current Parent
- Conversation ID: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Updated: 2026-10-14T16:24:10Z

## Review Scope
- **Files to review**: backend recommendation services, models, endpoints, celery tasks/signals, tests
- **Interface contracts**: ORIGINAL_REQUEST.md, PROJECT.md, worker handoff.md
- **Review criteria**: TF-IDF & Cosine similarity pure-Python math, interaction weights (1..5), cold-start score bounds [0.0, 1.0], cache invalidation upon interaction, guest access robustness, explainable tags

## Attack Surface
- **Hypotheses tested**:
  1. Pure-Python TF-IDF and Cosine similarity mathematical accuracy & edge cases: VERIFIED PASS in isolation.
  2. Cold-start popularity bounds in [0.0, 1.0] and PostgreSQL NUMERIC(5,4) safety: VERIFIED PASS.
  3. Explainable recommendation tags: VERIFIED PASS.
  4. Guest/anonymous recommendation retrieval: VERIFIED PASS for list endpoint.
  5. Detail endpoint GET /api/recommendations/<pk>/: FAILED (Bug 1 - 500 AssertionError).
  6. Interaction weight consistency across apps: FAILED (Bug 2 - orders/services.py:83 uses weight 6.00 instead of 4.00).
  7. Cache invalidation on ordering / reviewing: FAILED (Bug 3 - cache not invalidated when orders/reviews are created).
- **Vulnerabilities found**:
  - Bug 1 (CRITICAL): `GoiYMonAnViewSet` missing `queryset`/`get_queryset()` causes 500 AssertionError on detail requests.
  - Bug 2 (HIGH): `orders/services.py:83` hardcodes `trong_so=6` instead of `trong_so=4` on `dat_mon`.
  - Bug 3 (MEDIUM): Recommendation cache is not invalidated upon creating orders or reviews.
- **Untested angles**: Celery async worker queue (offline environment operates synchronously).

## Loaded Skills
- None

## Key Decisions Made
- Formulated REQUEST_CHANGES verdict based on 3 reproducible bugs.
- Implemented comprehensive adversarial test suites `test_adversarial_challenger_m4_recommendations.py` and `test_adversarial_challenger_m4_bug_reproduction.py`.

## Artifact Index
- DISPATCH.md — Task instructions
- progress.md — Challenger liveness and step tracking
- handoff.md — Final challenger evaluation report with empirical proof
