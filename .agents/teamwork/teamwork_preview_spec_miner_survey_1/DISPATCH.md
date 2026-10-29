# Dispatch for Business Logic & Spec Miner

## Mission
Probe and document all business logic specifications, algorithms, and integration protocols required across R1 to R5.

## Key Files to Read
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (Authoritative requirements R1-R5)
- `/Users/VuVan/Documents/DO-AN/prompt web nhà hàng .txt`
- `/Users/VuVan/Documents/DO-AN/moc_schema_tieng_viet.sql`
- Relevant backend files in `/Users/VuVan/Documents/DO-AN/moc-backend/`

## Deliverables
Write your comprehensive specification report to `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_survey_1/handoff.md` detailing:
1. **VNPay Sandbox Payment & Refund Flow**:
   - Exact query parameters, hashing with HMAC-SHA512, return URL validation, IPN callback verification and transaction status mapping.
   - Deposit refund rules: >24h 100%, 6-24h 50%, <6h 0%. Refund receipt generation logic.
2. **Table Concurrency Control**:
   - Phase 1: Redis temporary lock (`SET NX` with 10-minute TTL per table/slot). HTTP 409 conflict return format.
   - Phase 2: Pessimistic locking inside database transaction (`select_for_update()`).
3. **Realtime Communication (WebSocket & FSM)**:
   - Order lifecycle FSM states (`cho_tiep_nhan` -> `da_xac_nhan` -> `dang_che_bien` -> `san_sang` -> `hoan_tat`/`da_huy`) and event broadcast triggers.
   - Staff-Customer 2-way chat: schema for messages, message persistence in PostgreSQL before broadcast, room routing.
4. **AI Recommendation & PostGIS GIS**:
   - Content-Based Filtering: item feature matrix (TF-IDF vectorizer over ingredients, category, spiciness level, taste profile), cosine similarity calculation.
   - User interaction weighted profile (view=1, favorite=2, cart=3, order=4, review=5 or project specification weights).
   - Cold-start fallback (top popular items) and Explainable Recommendation explanation generator.
   - PostGIS spatial query: `ST_Distance`, `GiST` spatial index, finding nearest branch given (latitude, longitude).


## 2026-10-14T03:06:03Z
Sender: e7c4f174-4311-49a1-ac7b-15083103a212
Priority: MESSAGE_PRIORITY_HIGH
Content:
You are Business Logic & Spec Miner for Web App Nhà hàng Mộc.
Your working directory is: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_survey_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_survey_1/DISPATCH.md.
Probe and specify:
1. VNPay Sandbox payment, checksum HMAC-SHA512, IPN webhook, and refund policy (>24h 100%, 6-24h 50%, <6h 0%).
2. Concurrency control: Redis temporary hold 10m TTL (SET NX) and DB pessimistic locking (select_for_update).
3. Realtime FSM order states and WebSocket 2-way chat with persistence.
4. AI Recommendation (TF-IDF + Cosine similarity, weights, cold-start, explainable tags) & PostGIS nearest branch query (ST_Distance, GiST).
Write your complete report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_survey_1/handoff.md and notify me via send_message when done.
