# TEST_INFRA — E2E Test Infrastructure & Specification

## 1. Test Philosophy & Architecture

### 1.1 Opaque-Box & Requirement-Driven Testing
The E2E Test Suite for **Web App Nhà hàng Mộc** operates strictly under an **opaque-box, requirement-driven** philosophy:
- **Zero reliance on implementation internals**: Tests evaluate observable outputs (HTTP status codes, response payloads, WebSocket push frames, cryptographic HMAC-SHA512 signatures, IPN webhook response codes, race-condition rejections, and inventory deductions) against authoritative project specifications.
- **Authoritative Oracles**: Every expected outcome is derived directly from:
  1. `ORIGINAL_REQUEST.md` (Requirements R1 to R5 and Acceptance Criteria).
  2. `moc_schema_tieng_viet.sql` (Authoritative database schema, enum definitions, constraint rules, and refund policy rules).
  3. Master Thesis Specification `BB-V1_1250080238-DE-CUONG-DACN-CNPM - Vũ Nguyễn Văn.docx` (Paragraphs 26, 36, 40, 103, 108).
  4. VNPay Payment Gateway Developer Specification v2.1.0 (`https://sandbox.vnpayment.vn/apis/`).

### 1.2 Progressive Testability & Dual Execution Modes
To guarantee tests can run at any phase of project implementation (even when backend micro-services, database migrations, or frontend builds are in active development), the test suite supports **Dual Execution Modes**:
1. **Live Network Mode (`--live`)**:
   - Executes HTTP/REST requests against the active Django ASGI/WSGI server (default `http://127.0.0.1:8000`).
   - Connects to real Redis instances (`redis://127.0.0.1:6379/0`) and WebSocket channels (`ws://127.0.0.1:8000/ws/...`).
2. **Specification & Contract Oracle Mode (`--offline` / Default Fallback)**:
   - When the live backend is unavailable or not yet migrated, tests execute authoritative requirement oracle contracts.
   - Evaluates real cryptographic HMAC-SHA512 hashing, IPN response parsing, multi-threaded table reservation race conditions (`SET NX EX 600`), strict FSM state transition validation matrices, mathematical refund time-delta calculations, and TF-IDF Cosine vector math.
   - Tests produce concrete, verifiable pass/fail signals without mocking away the real domain rules.

---

## 2. Directory Layout & Organization

The test framework is placed in `tests/e2e/`, structured modularly by tier:

```
/Users/VuVan/Documents/DO-AN/
├── TEST_INFRA.md                          <- This document
├── TEST_READY.md                          <- Test Readiness & Execution Report
└── tests/
    └── e2e/
        ├── __init__.py
        ├── runner.py                      <- Standalone CLI Runner (supports --tier, --live, --verbose, --json)
        ├── conftest.py                    <- Pytest / Unittest shared fixtures & environment config
        ├── helpers/                       <- Authoritative Specification Oracles
        │   ├── __init__.py
        │   ├── vnpay_oracle.py            <- HMAC-SHA512 checksum calculator & IPN simulator
        │   ├── refund_calculator.py       <- Cancellation refund policy engine (>24h, 6-24h, <6h, no-show)
        │   ├── fsm_validator.py           <- Order FSM 6-state transition matrix & audit validator
        │   ├── redis_lock_sim.py          <- 2-Phase Concurrency Control & Redis SET NX simulator
        │   ├── ai_gis_oracle.py           <- Content-Based TF-IDF Cosine math & Haversine/PostGIS distance
        │   └── api_client.py              <- Dual-mode HTTP/WebSocket client with auto-detection
        ├── tier1/                         <- Tier 1: Core Feature Coverage (>= 5 tests per group)
        │   ├── __init__.py
        │   ├── test_t1_backend.py         <- Django check, endpoint contracts, seed data verification (100+ foods, tables, branches)
        │   ├── test_t1_vnpay.py           <- Sandbox URL generation, HMAC-SHA512 verification, IPN callback simulation
        │   ├── test_t1_concurrency.py     <- Redis temporary hold (SET NX), 10m TTL, HTTP 409 rejection
        │   ├── test_t1_realtime.py        <- WebSocket connection, message echo, FSM status transitions
        │   ├── test_t1_recommendation_gis.py <- /api/recommendations/ items + explainable tags, nearest branch query
        │   └── test_t1_frontend.py        <- Frontend TypeScript compilation & adapter layer checks
        ├── tier2/                         <- Tier 2: Boundary & Corner Cases (>= 5 tests per group)
        │   ├── __init__.py
        │   ├── test_t2_vnpay.py           <- Invalid checksum (97), duplicate IPN (02), tampered amount (04), missing order (01)
        │   ├── test_t2_refund.py          <- Cancellation at >24h (100%), exactly 6h-24h (50%), <6h (0%), no-show (0%)
        │   ├── test_t2_concurrency.py     <- Simultaneous 2-user race condition on same table & time slot
        │   └── test_t2_fsm.py             <- Illegal transitions (e.g. san_sang -> cho_tiep_nhan, terminal immutability)
        ├── tier3/                         <- Tier 3: Cross-Feature Combinations
        │   ├── __init__.py
        │   └── test_t3_combinations.py    <- Hold table -> Pay VNPay deposit -> IPN confirm -> Order dishes -> Inventory deduction
        └── tier4/                         <- Tier 4: Real-World Application Scenarios (>= 5 scenarios)
            ├── __init__.py
            └── test_t4_scenarios.py       <- 5 end-to-end multi-step customer journeys
```

---

## 3. Feature Inventory & Test Mapping Matrix

| Tier | Group Code | Feature Name | Test File | Test Count | Authoritative Spec Source |
|---|---|---|---|---|---|
| **Tier 1** | `T1_backend` | Backend Health, Schema & Seed Data | `tests/e2e/tier1/test_t1_backend.py` | 5 | R1, `moc_schema_tieng_viet.sql`, `Du-lieu-test.txt` |
| **Tier 1** | `T1_vnpay` | VNPay Sandbox URL, Checksum & IPN | `tests/e2e/tier1/test_t1_vnpay.py` | 5 | R2, VNPay v2.1.0 API Spec |
| **Tier 1** | `T1_concurrency` | Redis Table Hold & 409 Conflict | `tests/e2e/tier1/test_t1_concurrency.py` | 5 | R2, Đề cương ¶26 (`SET NX EX 600`) |
| **Tier 1** | `T1_realtime` | Channels WebSocket & FSM Transitions | `tests/e2e/tier1/test_t1_realtime.py` | 5 | R3, Django Channels 4.x ASGI, Redis Layer |
| **Tier 1** | `T1_recommendation_gis` | AI Recommendation & PostGIS Distance | `tests/e2e/tier1/test_t1_recommendation_gis.py` | 5 | R4, TF-IDF Cosine math, PostGIS `ST_Distance` |
| **Tier 1** | `T1_frontend` | Frontend TypeScript Build & Adapters | `tests/e2e/tier1/test_t1_frontend.py` | 5 | R5, `moc-frontend/package.json` (`npm run build`) |
| **Tier 2** | `T2_vnpay` | VNPay Security, Tampering & Idempotency | `tests/e2e/tier2/test_t2_vnpay.py` | 5 | R2, VNPay Webhook Security Codes `97`, `02`, `04`, `01` |
| **Tier 2** | `T2_refund` | Deposit Refund Boundaries (100%, 50%, 0%) | `tests/e2e/tier2/test_t2_refund.py` | 5 | R2, `moc_schema_tieng_viet.sql` lines 281-287 |
| **Tier 2** | `T2_concurrency` | Race Condition Stress & Token Hijack | `tests/e2e/tier2/test_t2_concurrency.py` | 5 | R2, Đề cương ¶108, Multi-threaded Collision |
| **Tier 2** | `T2_fsm` | Illegal State Machine Transitions | `tests/e2e/tier2/test_t2_fsm.py` | 5 | R3, `orders/models.py`, Terminal State Rules |
| **Tier 3** | `T3_combined` | Cross-Feature End-to-End Pipeline | `tests/e2e/tier3/test_t3_combinations.py` | 5 | R1-R4, Table Hold + VNPay + IPN + BOM Deduction |
| **Tier 4** | `T4_scenarios` | Real-World Customer Journeys | `tests/e2e/tier4/test_t4_scenarios.py` | 5 | Acceptance Criteria 1 to 7 |
| **Total** | | **Comprehensive Test Suite** | **12 Test Modules** | **60 Tests** | **100% Coverage of R1-R5** |

---

## 4. Tier 4: Real-World Application Scenarios

The suite models 5 comprehensive, realistic multi-actor customer and staff journeys:

### Scenario 1 (S1): Cold-Start Customer Discovery & Reservation
1. An unauthenticated new visitor opens the website.
2. The user queries the nearest branch using browser geolocation coordinates (e.g. Tân Bình `10.7925, 106.6669`).
3. The AI engine activates **Cold-Start Popularity Fallback**, displaying Top-6 highly rated dishes tagged `"Phổ biến hôm nay"`.
4. The user chooses a table at 18:30, triggering a 10-minute Redis temporary hold (`SET NX EX 600`) with unique `id_giu_ban`.
5. The user proceeds to VNPay Sandbox checkout, pays the 200,000 VND deposit, receives IPN confirmation, and the table lock transitions to database confirmed (`da_xac_nhan`).

### Scenario 2 (S2): Returning Gourmet Customer with Explainable AI & Live Chat
1. An authenticated customer with a history of ordering spicy hotpot visits the platform.
2. The AI recommendation engine evaluates the user interaction weights (`xem`=1, `thich`=2, `gio`=3, `dat`=4, `danh_gia`=5) and computes Cosine similarities against the menu corpus.
3. Recommendations are returned with explicit explainable tags: `"Gợi ý vì bạn yêu thích các món lẩu ấm cúng"` and `"Phù hợp với khẩu vị thích món cay nồng của bạn"`.
4. The customer opens the live chat widget to ask the staff about table preferences.
5. The WebSocket consumer verifies JWT authentication, writes the message into PostgreSQL `tin_nhan`, and broadcasts it to both customer and staff portals in real time.

### Scenario 3 (S3): Early Booking Cancellation with 100% Deposit Refund
1. A customer who booked a table for 2 days ahead ($\Delta t = 48\text{h} > 24\text{h}$) requests a cancellation.
2. The system calculates $\Delta t$, identifies the `truoc_24h` policy threshold, and calculates a 100% deposit refund rate.
3. The booking status changes to `da_huy`, deposit status updates to `da_hoan_tien`, and a formal `PhieuHoanTien` receipt is generated with full refund amount and reconciliation code.
4. The table is automatically released back to `trong` status for new reservations.

### Scenario 4 (S4): Late Booking Cancellation with 0% Deposit Forfeiture
1. A customer cancels only 3 hours before the scheduled reservation ($\Delta t = 3.0\text{h} < 6\text{h}$).
2. The system applies the `trong_6h` rule: 0% refund, deposit status set to `that_bai` (restaurant retains deposit as late penalty).
3. The system generates an audit record showing 0 VND refund and penalty explanation.
4. The table is immediately returned to `trong` status so walk-in guests can take it.

### Scenario 5 (S5): High-Concurrency Table Race Condition
1. At 19:00 peak time, Customer A and Customer B both attempt to reserve Table 8 for 20:00 within the same millisecond.
2. The backend executes Redis `SET NX EX 600`:
   - Customer A receives HTTP 200 with hold token `HOLD_...` and a 600-second countdown.
   - Customer B receives HTTP 409 Conflict with code `TABLE_CURRENTLY_HELD`.
3. Customer A completes VNPay deposit payment; the system acquires database pessimistic lock `select_for_update()`, verifies Redis token, updates `DatBan` to `da_xac_nhan`, and deletes the Redis temporary key.
4. If Customer B retries, the table is now permanently marked as `da_dat` in the database, preserving strict ACID isolation.

---

## 5. Test Execution Instructions

### 5.1 Prerequisites
- Python 3.9+ with virtual environment activated (`source moc-backend/.venv/bin/activate`).
- Installed packages: `requests`, `urllib3`, `psycopg2-binary`, `django` (already in `.venv`).

### 5.2 Test Runner Command
The test suite can be run using the built-in runner:

```bash
# Run all 60 tests across all 4 Tiers
python tests/e2e/runner.py

# Run a specific Tier
python tests/e2e/runner.py --tier 1
python tests/e2e/runner.py --tier 2
python tests/e2e/runner.py --tier 3
python tests/e2e/runner.py --tier 4

# Run with verbose output and generate JSON report
python tests/e2e/runner.py --verbose --json-report test_report.json

# Run against a live running backend server
python tests/e2e/runner.py --live --base-url http://127.0.0.1:8000
```

### 5.3 Standard Python Unittest Command
The tests are 100% compliant with Python's standard `unittest` framework:

```bash
python -m unittest discover -s tests/e2e -p "test_*.py" -v
```
