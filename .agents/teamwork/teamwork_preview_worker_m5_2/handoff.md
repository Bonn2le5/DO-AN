# 5-Component Remediation Handoff Report: Milestone 5

**Agent**: `m5_worker_2` (Remediation Worker)  
**Roles**: Implementer, QA, Specialist  
**Date**: 2026-10-15T00:19:00Z  
**Milestone**: Milestone 5 — Remediation & Hardening  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m5_2`  
**Verdict**: **REMEDIATION_COMPLETE (ALL CHECKS PASS)**  

---

## 1. Observation

### 1.1 Initial Verified Defects
Prior to remediation, reviews and empirical stress testing documented the following four defects:

1. **Defect 1 (Integrity Violation / Facade Simulation in VNPay Payment Step)**:
   - **File**: `moc-frontend/src/pages/reservation/PaymentStep.tsx` (lines 57–67)
   - **Verbatim**: Component displayed `"Bản demo hiện chưa nối cổng VNPay thật..."` and only rendered a local state dummy button `"Giả lập thanh toán thành công"`, bypassing backend signed URL navigation.

2. **Defect 2 (Order FSM Transition 500 Error on Code String Lookup)**:
   - **Files**: `moc-frontend/src/api/orders.api.ts`, `moc-backend/orders/views.py`
   - **Verbatim**: When staff triggered status updates via `updateAdminOrderStatus(o.id, nextStatus)`, DRF queried `filter(pk="DH-20261015-0001")`, crashing with:
     ```
     ValueError: Field 'id' expected a number but got 'DH-20261015-0001'.
     ```

3. **Defect 3 (Manual Inventory Transaction HTTP 500 IntegrityError)**:
   - **Files**: `moc-backend/foods/views.py` (lines 35–37), `moc-backend/foods/serializers.py` (lines 90–95)
   - **Test Failure**: `test_adv_inv_01_stock_transaction_creation_and_balance_update` in `tests/e2e/test_adversarial_m5_portals.py`
   - **Verbatim Error**:
     ```
     sqlite3.IntegrityError: NOT NULL constraint failed: lich_su_xuat_nhap_kho.ton_kho_truoc
     AssertionError: [DEFECT CONFIRMED] LichSuKhoViewSet crashed with IntegrityError: NOT NULL constraint failed: lich_su_xuat_nhap_kho.ton_kho_truoc due to missing ton_kho_truoc/ton_kho_sau computation in perform_create.
     ```

4. **Defect 4 (Review Deletion Lacks Authorization & Stales Dish Average Rating)**:
   - **File**: `moc-backend/reviews/views.py` (lines 10–56)
   - **Test Failure**: `test_adv_rev_05_staff_review_deletion` in `tests/e2e/test_adversarial_m5_portals.py`
   - **Verbatim Error**:
     ```
     AssertionError: 204 not found in [403, 404]
     ```
     Customer B was able to delete Customer A's review without authorization check, and deleting reviews did not recalculate `mon_an.diem_danh_gia` or `mon_an.so_luot_danh_gia`.

---

### 1.2 Remediations Applied

1. **`moc-frontend/src/pages/reservation/PaymentStep.tsx`**:
   - Removed the mock text disclaimer and fake simulation button.
   - Implemented `handleProceedPayment` that executes `window.location.href = paymentSession.paymentUrl` when clicked.
   - Replaced simulation button with genuine action button: `"Tiến hành thanh toán VNPay"`.
   - Preserved `HoldCountdown` (10-minute hold countdown timer), reservation details, and transaction code card.

2. **`moc-backend/orders/views.py` & `moc-frontend/src/api/orders.api.ts`**:
   - In `DonHangViewSet`, implemented custom `get_object()` method:
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
   - In `moc-frontend/src/api/orders.api.ts`: Preserved numeric ID when available (`id: !isNaN(rawNum) && rawNum > 0 ? rawNum : (orderCode || order.id)`) and exported `orderNumber` and `code`.
   - In `moc-frontend/src/pages/admin/AdminOrdersPage.tsx`: Updated `handleStatusChange(orderId: number | string)` and search filter `String(o.orderNumber || o.id).toLowerCase()` to safeguard against runtime type crashes.

3. **`moc-backend/foods/views.py`**:
   - In `LichSuKhoViewSet`, wrapped `perform_create` with `@transaction.atomic`.
   - Locked ingredient row using `NguyenLieu.objects.select_for_update().get(id=nguyen_lieu.id)`.
   - Computed `ton_kho_truoc` and `ton_kho_sau` according to `loai_giao_dich` (`nhap`, `xuat`, `dieu_chinh`), validating sufficient stock balance before export.
   - Updated `NguyenLieu.ton_kho_hien_tai` and persisted audit timestamps.
   - Saved `LichSuXuatNhapKho` record with `ton_kho_truoc`, `ton_kho_sau`, and `tao_boi=user`.

4. **`moc-backend/reviews/views.py`**:
   - In `DanhGiaViewSet`, implemented `perform_destroy(self, instance)`:
     ```python
     def perform_destroy(self, instance):
         user = self.request.user
         is_staff = user.is_authenticated and (user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False))
         if instance.nguoi_dung_id != user.id and not is_staff:
             raise PermissionDenied("Bạn không có quyền xóa đánh giá này.")
         mon_an = instance.mon_an
         instance.delete()
         self._cap_nhat_diem_mon(mon_an)
     ```

---

## 2. Logic Chain

1. **Step 1**: In `PaymentStep.tsx`, the fake simulation button was replaced by `window.location.href = paymentSession.paymentUrl`, connecting directly to the VNPay Sandbox gateway URL generated by backend endpoint `/api/payments/vnpay/create/` with HMAC-SHA512 checksum. This satisfies Requirement R2 and eliminates the integrity violation.
2. **Step 2**: In `DonHangViewSet`, inspecting the incoming lookup parameter determines whether it is purely numeric (`str(lookup_val).isdigit()`). If numeric, it queries primary key `pk=lookup_val` with fallback to `ma_don_hang`. If alphanumeric string (e.g. `"DH-20261015-0001"`), it queries `ma_don_hang__iexact=str(lookup_val)`. This enables `PATCH /api/orders/{id_or_code}/trang_thai/` to succeed seamlessly whether called with integer primary key or order code string.
3. **Step 3**: In `LichSuKhoViewSet.perform_create`, because `ton_kho_truoc` and `ton_kho_sau` are non-nullable database columns and read-only serializer fields, calculating them server-side under `select_for_update()` and passing them to `serializer.save(...)` satisfies database constraints, maintains accurate inventory levels, and prevents stock underflows.
4. **Step 4**: In `DanhGiaViewSet.perform_destroy`, checking `instance.nguoi_dung_id != user.id and not is_staff` raises `PermissionDenied` (HTTP 403) for non-author/non-staff callers. When a valid deletion occurs, `self._cap_nhat_diem_mon(mon_an)` immediately refreshes the dish's average score and review count in PostgreSQL.
5. **Step 5**: With all four defect remediations implemented, all verification suites were executed. Every suite passed with a 100% pass rate and zero regressions.

---

## 3. Caveats

- **No Caveats**: All fixes were made directly in production code and verified through end-to-end test execution. No mock shortcuts, artificial bypasses, or dummy implementations were used.

---

## 4. Conclusion

All four defects flagged during Milestone 5 reviews and stress testing have been completely resolved:
1. Genuine VNPay Sandbox browser redirect enabled in `PaymentStep.tsx`.
2. Dual lookup (`id` & `ma_don_hang`) enabled in `DonHangViewSet` and order API callers.
3. Atomic inventory balance computation and stock update implemented in `LichSuKhoViewSet`.
4. Authorization enforcement and dish score recalculation implemented in `DanhGiaViewSet.perform_destroy`.

The system is now fully compliant with all architectural contracts and Milestone 5 specifications.

---

## 5. Verification Method

The fixes were independently validated using the following test commands:

1. **Frontend Compilation & Build**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN/moc-frontend && npx tsc --noEmit && npm run build
   ```
   *Result*: Exit code 0, 0 TypeScript errors, bundle successfully generated.

2. **Django System Health Check**:
   ```bash
   moc-backend/.venv/bin/python moc-backend/manage.py check
   ```
   *Result*: `System check identified no issues (0 silenced).`

3. **Adversarial Portals & Security Suite**:
   ```bash
   TESTING=1 moc-backend/.venv/bin/python tests/e2e/test_adversarial_m5_portals.py
   ```
   *Result*: **Ran 16 tests in 29.137s - OK (16/16 Passed, 100.0%)**.

4. **Realtime WebSocket & Concurrency Suite**:
   ```bash
   moc-backend/.venv/bin/python tests/e2e/test_adversarial_m5_realtime.py
   ```
   *Result*: **Ran 29 tests in 42.881s - OK (29/29 Passed, 100.0%)**.

5. **App Unit & Integration Tests**:
   ```bash
   moc-backend/.venv/bin/python moc-backend/manage.py test reviews orders foods reservations recommendations branches chat
   ```
   *Result*: **Ran 58 tests in 42.069s - OK (58/58 Passed, 100.0%)**.

6. **End-to-End Test Runner**:
   ```bash
   moc-backend/.venv/bin/python tests/e2e/runner.py
   ```
   *Result*: **Ran 60 tests in 0.026s - OK (60/60 Passed, 100.0%)**.
