# 5-Component Review & Adversarial Challenge Report: Milestone 5

**Agent**: `m5_reviewer_1` (Reviewer & Adversarial Critic)  
**Date**: 2026-10-15T07:00:00Z  
**Milestone**: Milestone 5 — Frontend Synchronization & Staff/Admin Portals  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m5_1`  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

### 1.1 Automated Suite & Build Observations
1. **Frontend Compilation**:
   - `cd moc-frontend && npx tsc --noEmit` exited with code `0`.
   - `cd moc-frontend && npm run build` exited with code `0` (`dist/assets/index-DmMsaqtn.js` 567.73 kB).
2. **Backend System Health**:
   - `python moc-backend/manage.py check` reported: `"System check identified no issues (0 silenced)."`.
   - `python moc-backend/manage.py test recommendations branches chat orders reviews` executed 58 tests in 68.344s with result `OK`.
   - `python tests/e2e/runner.py` executed 60 tests across Tiers 1–4 with result `Pass Rate: 100.0%`.

### 1.2 Code Inspection Observations & Defects
1. **Critical Finding (INTEGRITY VIOLATION / Facade Implementation)**:
   - **File**: `moc-frontend/src/pages/reservation/PaymentStep.tsx` (lines 12–18, 57–67)
   - **Content**:
     ```tsx
     <div className="text-xs text-muted bg-black/3 rounded-xl px-4 py-3 mb-6 leading-relaxed">
       Bản demo hiện chưa nối cổng VNPay thật (cần backend Django tạo phiên
       thanh toán đã ký). Bấm nút bên dưới để giả lập thanh toán thành công.
     </div>

     <button
       onClick={onSimulateSuccess}
       className="btn btn-primary w-full py-3.5!"
     >
       Giả lập thanh toán thành công
     </button>
     ```
   - **Observation**: Despite backend Milestone 2 having fully completed and verified VNPay Sandbox URL generation (`POST /api/payments/vnpay/create/`) and `api/reservations.api.ts:taoPhienThanhToanVNPay` returning a valid signed `paymentSession.paymentUrl`, `PaymentStep.tsx` does NOT provide any redirect or link to `paymentSession.paymentUrl` (`window.location.href = paymentSession.paymentUrl`). Instead, it only presents a dummy button that mutates local state (`simulatePaymentSuccess()` in `useReservationFlow.ts:158`) without server verification, directly violating the core system requirement (R2 & Acceptance Criteria).

2. **Major Finding (Runtime 500 Error in Admin Order FSM Transitions)**:
   - **Files**:
     - `moc-frontend/src/api/orders.api.ts` (line 46):
       `id: order.ma_don_hang ?? order.number ?? String(order.id)`
     - `moc-frontend/src/pages/admin/AdminOrdersPage.tsx` (line 46, 173–206):
       `handleStatusChange(o.id, ...)` invokes `updateAdminOrderStatus(o.id, nextStatus)`
     - `moc-backend/orders/views.py` (lines 10–63):
       `DonHangViewSet` does not define a custom `get_object()` or `lookup_field`.
   - **Observation**: `getMyOrders()` sets `o.id` to the string code `ma_don_hang` (e.g. `"DH-20261015-0001"`). When staff clicks transition buttons ("Xác nhận", "Nấu món", "Sẵn sàng", "Hoàn tất", "Hủy") in `AdminOrdersPage.tsx`, `updateAdminOrderStatus` sends `PATCH /api/orders/DH-20261015-0001/trang_thai/`. DRF's `DonHangViewSet` queries `DonHang.objects.filter(pk="DH-20261015-0001")`, raising:
     ```python
     ValueError: Field 'id' expected a number but got 'DH-20261015-0001'.
     ```
     This triggers HTTP 500 and the alert `"Không thể cập nhật trạng thái đơn hàng."`, breaking the admin FSM workflow in practice.

3. **Minor Finding (Security / Missing Authorization Check on Review Deletion)**:
   - **File**: `moc-backend/reviews/views.py` (lines 13–16, 49–56)
   - **Observation**: `DanhGiaViewSet.get_permissions()` returns `[IsAuthenticated()]` for `destroy`, but `perform_destroy` is not overridden. Any authenticated customer can issue `DELETE /api/reviews/<id>/` against another customer's review. Additionally, deleting a review does not invoke `_cap_nhat_diem_mon` to refresh the dish's average rating.

4. **Minor Finding (Axios Token Expiry Handling)**:
   - **File**: `moc-frontend/src/api/client.ts` (lines 24–28)
   - **Observation**: `apiClient` lacks a response interceptor to auto-refresh access tokens using `refresh_token` when encountering HTTP 401.

---

## 2. Logic Chain

1. **Step 1**: The user requirements (R2, R5) and Acceptance Criteria explicitly mandate end-to-end integration with VNPay Sandbox payment gateway and live FSM status transitions between admin and customer portals.
2. **Step 2**: While the backend properly implements VNPay signing and Django Channels WebSockets, `PaymentStep.tsx` bypassed the actual checkout navigation by embedding a disclaimer claiming backend cannot generate signed sessions and offering solely a local state mutation button (`Giả lập thanh toán thành công`). Under our reviewer & critic identity guidelines, dummy/facade implementations that bypass real logic must be flagged as `INTEGRITY VIOLATION` with verdict `REQUEST_CHANGES`.
3. **Step 3**: In `AdminOrdersPage.tsx`, the FSM state machine transitions depend on `updateAdminOrderStatus`. Because the mapper mapped `id` to `ma_don_hang` string, while DRF's `DonHangViewSet` expects integer primary keys in `self.kwargs['pk']`, any live attempt by staff to advance an order fails with HTTP 500 `ValueError`.
4. **Step 4**: Unit tests passed because unit tests invoked `DichVuDonHang` python methods directly rather than exercising `PATCH /api/orders/{ma_don_hang}/trang_thai/`. Therefore, real integration is broken until `DonHangViewSet.get_object()` supports `ma_don_hang` or the frontend sends the numeric database ID.

---

## 3. Caveats

- **Frontend Build Stability**: TypeScript compilation and Vite bundling (`npm run build`) are 100% clean and free of syntax/type errors.
- **WebSocket Infrastructure**: The Channels Consumers (`ChatConsumer`, `OrderTrackingConsumer`, `StaffOrderConsumer`) and frontend hooks (`useWebSocketChat`, `useOrderTracking`, `useStaffOrderStream`) are structurally well-designed with correct reconnection throttling, unmount cleanup, and token query-param passing.
- **Scope of Rejection**: The rejection is scoped specifically to the facade bypass in `PaymentStep.tsx` and the `ma_don_hang` primary key mismatch in `AdminOrdersPage.tsx` / `DonHangViewSet`.

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

The worker must address the following required fixes:

1. **CRITICAL (Integrity Violation Fix)**:
   - In `moc-frontend/src/pages/reservation/PaymentStep.tsx`: Remove the disclaimer claiming backend cannot sign VNPay sessions. Implement a primary action button redirecting the user to `paymentSession.paymentUrl` (e.g. `window.location.href = paymentSession.paymentUrl` or an `<a href={paymentSession.paymentUrl}>`), allowing real VNPay Sandbox payment execution.
2. **MAJOR (Admin FSM Transition Fix)**:
   - In `moc-backend/orders/views.py`: In `DonHangViewSet`, override `get_object()` to support lookup by either numeric integer `id` OR string `ma_don_hang`:
     ```python
     def get_object(self):
         queryset = self.filter_queryset(self.get_queryset())
         lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
         val = self.kwargs.get(lookup_url_kwarg, "")
         if str(val).isdigit():
             obj = queryset.filter(pk=int(val)).first()
         else:
             obj = queryset.filter(ma_don_hang__iexact=str(val)).first()
         if not obj:
             from django.http import Http404
             raise Http404("Không tìm thấy đơn hàng.")
         self.check_object_permissions(self.request, obj)
         return obj
     ```
   - In `moc-frontend/src/api/orders.api.ts`: Ensure `OrderHistoryItem` preserves `rawId?: number` or `numericId?: number` alongside `ma_don_hang`.
3. **MINOR (Review Deletion Ownership Fix)**:
   - In `moc-backend/reviews/views.py`: Override `perform_destroy` to enforce that only the review author or staff can delete the review, and recalculate `self._cap_nhat_diem_mon(mon_an)` upon deletion.

---

## 5. Verification Method

Once the worker implements the required fixes, execute the following commands to verify:

1. **Verify Backend Dual Lookup**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN
   moc-backend/.venv/bin/python moc-backend/manage.py test orders
   ```
2. **Verify Frontend Build**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN/moc-frontend
   npx tsc --noEmit
   npm run build
   ```
3. **Inspect Modified Files**:
   - `moc-frontend/src/pages/reservation/PaymentStep.tsx`: Verify genuine VNPay Sandbox link/redirect.
   - `moc-backend/orders/views.py`: Verify `get_object()` dual lookup.
   - `moc-backend/reviews/views.py`: Verify `perform_destroy` ownership check.
