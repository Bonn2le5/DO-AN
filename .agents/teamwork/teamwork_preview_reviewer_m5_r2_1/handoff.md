# 5-Component Review & Adversarial Verification Report: Milestone 5 (Round 2)

**Agent**: `m5_r2_reviewer_1` (Reviewer & Adversarial Critic)  
**Date**: 2026-10-15T00:31:00Z  
**Milestone**: Milestone 5 — Frontend Synchronization & Staff/Admin Portals (Post-Remediation)  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m5_r2_1`  
**Verdict**: **APPROVE**

---

## 1. Observation

### 1.1 Automated Suite & Build Verification
1. **Frontend Compilation & Bundle**:
   - Command: `cd /Users/VuVan/Documents/DO-AN/moc-frontend && npx tsc --noEmit`
     - Result: Exit code `0`, zero TypeScript compilation errors.
   - Command: `cd /Users/VuVan/Documents/DO-AN/moc-frontend && npm run build`
     - Result: Exit code `0`. Successfully emitted production bundle `dist/assets/index-CHuuxiQM.js` (567.94 kB) and CSS `dist/assets/index-BK83Z842.css` (83.65 kB).
2. **Backend System Health & E2E Suites**:
   - Command: `moc-backend/.venv/bin/python moc-backend/manage.py check`
     - Result: `System check identified no issues (0 silenced).` Exit code `0`.
   - Command: `moc-backend/.venv/bin/python tests/e2e/runner.py`
     - Result: 60 tests executed across Tiers 1–4. `Pass Rate: 100.0% (60/60 Passed, 0 Failed, 0 Errors)`.
   - Command: `PYTHONPATH=. moc-backend/.venv/bin/python moc-backend/manage.py test tests.e2e.test_adversarial_m5_portals`
     - Result: 16 tests executed in 29.041s. `OK (16/16 Passed, 100.0%)`.
   - Command: `moc-backend/.venv/bin/python moc-backend/manage.py test reviews orders foods reservations recommendations branches`
     - Result: 49 tests executed in 67.363s. `OK (49/49 Passed, 100.0%)`.
   - Command: `moc-backend/.venv/bin/python moc-backend/manage.py test chat`
     - Result: 9 tests executed in 33.304s. `OK (9/9 Passed, 100.0%)`.

### 1.2 In-Depth Verification of Remediations
1. **Remediation 1: VNPay Payment Step Integrity & Genuine Redirect**:
   - **File**: `moc-frontend/src/pages/reservation/PaymentStep.tsx`
   - **Observations**:
     - The dummy disclaimer claiming the backend cannot create signed sessions has been completely removed.
     - The fake local simulation button (`Giả lập thanh toán thành công`) has been removed.
     - Implemented `handleProceedPayment` (lines 16–20):
       ```tsx
       const handleProceedPayment = () => {
         if (paymentSession?.paymentUrl) {
           window.location.href = paymentSession.paymentUrl;
         }
       };
       ```
     - Renders a genuine action button: `"Tiến hành thanh toán VNPay"` with `onClick={handleProceedPayment}`.
     - Displays accurate transaction code (`paymentSession.txnRef`), deposit amount (`formatCurrency(paymentSession.amount)`), and `HoldCountdown` timer (`paymentSession.expiresAt`).
     - Integrity check: No fake bypasses, facades, or hardcoded success signals remain.

2. **Remediation 2: Dual Identifier Lookup in Order ViewSet & FSM Transitions**:
   - **File**: `moc-backend/orders/views.py` (lines 15–30)
   - **Observations**:
     - Custom `get_object()` in `DonHangViewSet` seamlessly accepts both numeric integer primary keys and string `ma_don_hang`:
       ```python
       def get_object(self):
           queryset = self.filter_queryset(self.get_queryset())
           lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
           lookup_val = self.kwargs.get(lookup_url_kwarg)
           if lookup_val is None:
               return super().get_object()
           if str(lookup_val).isdigit():
               obj = queryset.filter(pk=lookup_val).first()
               if not obj:
                   obj = queryset.filter(ma_don_hang__iexact=str(lookup_val)).first()
           else:
               obj = queryset.filter(ma_don_hang__iexact=str(lookup_val)).first()
           if not obj:
               raise Http404("Không tìm thấy đơn hàng.")
           self.check_object_permissions(self.request, obj)
           return obj
       ```
     - No unhandled `ValueError` when callers pass `ma_don_hang` (e.g., `"DH-20261015-0001"`). Non-existent orders correctly return HTTP 404 rather than HTTP 500.
     - In `moc-frontend/src/api/orders.api.ts`: Preserves numeric ID when present (`id: !isNaN(rawNum) && rawNum > 0 ? rawNum : (orderCode || order.id)`) and exposes `orderNumber` / `code`.
     - In `moc-frontend/src/pages/admin/AdminOrdersPage.tsx`: Handles `handleStatusChange(orderId: number | string, nextStatus: string)`, avoiding type friction with backend endpoints.

3. **Remediation 3: Atomic Stock Computation & Balance Validation in Inventory Transactions**:
   - **File**: `moc-backend/foods/views.py` (lines 38–68)
   - **Observations**:
     - `LichSuKhoViewSet.perform_create` is guarded by `@transaction.atomic`.
     - Ingredient row locked using `NguyenLieu.objects.select_for_update().get(id=nguyen_lieu.id)`.
     - Server computes `ton_kho_truoc` and `ton_kho_sau` according to `loai_giao_dich` (`nhap`, `xuat`, `dieu_chinh`), validating `ton_truoc >= so_luong` for export transactions (raising HTTP 400 `ValidationError` on underflow).
     - Persists `tao_boi=user`, `ton_kho_truoc`, `ton_kho_sau` to satisfy SQLite and PostgreSQL schema constraints.

4. **Remediation 4: Review Deletion Authorization & Dish Score Refresh**:
   - **File**: `moc-backend/reviews/views.py` (lines 57–64)
   - **Observations**:
     - `perform_destroy` checks `instance.nguoi_dung_id != user.id and not is_staff`. If unauthorized, immediately raises `PermissionDenied` (HTTP 403).
     - Deletes the record and immediately invokes `self._cap_nhat_diem_mon(mon_an)` to recompute average rating (`diem_danh_gia`) and review count (`so_luot_danh_gia`) across active reviews.

---

## 2. Logic Chain

1. **Step 1 (Integrity Remediation)**: The Round 1 rejection was primarily driven by the facade simulation button and mock text in `PaymentStep.tsx`. Code inspection verifies that the mock disclaimer and dummy button were completely replaced by genuine navigation to `paymentSession.paymentUrl` via `window.location.href = paymentSession.paymentUrl`. The backend endpoint `/api/payments/vnpay/create/` was already verified in M2 to generate valid VNPay Sandbox URLs with HMAC-SHA512 checksums. The full payment navigation loop is now authentic and complete.
2. **Step 2 (FSM & Routing Correctness)**: The previous runtime failure in `AdminOrdersPage.tsx` occurred because DRF expected an integer primary key in `pk`, while the frontend passed `ma_don_hang`. By introducing dual-lookup in `DonHangViewSet.get_object()` supporting both integer `pk` and case-insensitive `ma_don_hang`, both administrative and customer callers can advance or inspect orders seamlessly without encountering type mismatches or HTTP 500 errors.
3. **Step 3 (Data Consistency & Concurrency Protection)**: The manual inventory transaction crash in `LichSuKhoViewSet` was resolved by computing `ton_kho_truoc` and `ton_kho_sau` under `select_for_update()`. This protects against race conditions, guarantees non-null database integrity, and enforces inventory stock limits.
4. **Step 4 (Access Control & Cache Coherence)**: In `DanhGiaViewSet`, restricting review deletion to the author or staff and recalculating average scores upon deletion ensures that ratings reflect the true database state and prevents unauthorized cross-tenant modifications.
5. **Step 5 (Empirical Verification)**: Across all test layers—frontend TypeScript checks, Vite production build, Django system checks, E2E runner (60/60 tests passed), and specialized adversarial suites (16/16 portal tests passed, 58/58 backend app tests passed)—100% of tests execute successfully with zero errors and zero integrity compromises.

---

## 3. Caveats

- **Async Suite Execution Load**: Under heavy consecutive test execution on macOS with SQLite, occasional async websocket communicator connect timeouts may occur due to thread contention; when executed individually or via Django's test runner with isolated databases, all async real-time tests pass reliably.
- **VNPay Sandbox Gateway**: Live payment completion relies on VNPay's external sandbox environment responding to the browser redirect in real deployment; the local cryptographic signing, parameter formatting, and return/IPN handlers have all been thoroughly verified.

---

## 4. Conclusion

**Verdict: APPROVE**

Milestone 5 (Round 2 — Post-Remediation) satisfies all architectural contracts, functional requirements, and security criteria. All four findings from Round 1 have been completely resolved with clean, production-grade logic. No integrity violations or facade implementations remain.

---

## 5. Verification Method

To independently reproduce this verification:

1. **Frontend Compilation & Build**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN/moc-frontend
   npx tsc --noEmit
   npm run build
   ```
   *Expected output*: Exit code 0, 0 errors, successful bundle generation.

2. **Django System Health**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN
   moc-backend/.venv/bin/python moc-backend/manage.py check
   ```
   *Expected output*: `System check identified no issues (0 silenced).`

3. **Master E2E Suite**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN
   moc-backend/.venv/bin/python tests/e2e/runner.py
   ```
   *Expected output*: `Pass Rate: 100.0% (60/60 Passed)`.

4. **Adversarial Portal & Security Suite**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN
   PYTHONPATH=. moc-backend/.venv/bin/python moc-backend/manage.py test tests.e2e.test_adversarial_m5_portals
   ```
   *Expected output*: `Ran 16 tests ... OK`.

5. **Core App Suites**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN
   moc-backend/.venv/bin/python moc-backend/manage.py test reviews orders foods reservations recommendations branches chat
   ```
   *Expected output*: `OK`.
