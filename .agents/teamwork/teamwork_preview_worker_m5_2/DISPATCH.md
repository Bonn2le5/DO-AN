# Dispatch Assignment: Milestone 5 Remediation Worker (m5_worker_2)

## Context
You are Worker `m5_worker_2` assigned to remediate the verified defects identified during Milestone 5 Verification Squad reviews and empirical stress testing for Web App Nhà hàng Mộc.

Your Working Directory: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m5_2`

## Authoritative Documents to Read First
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (MANDATORY)
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen5/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m5_1/handoff.md`
4. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m5_2/handoff.md`

## MANDATORY INTEGRITY WARNING
> DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Remediation Tasks

### Task 1: Connect `PaymentStep.tsx` Genuinely to VNPay Sandbox
- **File**: `moc-frontend/src/pages/reservation/PaymentStep.tsx`
- **Issue**: Component contains a mock disclaimer claiming backend signing is not connected and a dummy simulation button (`Giả lập thanh toán thành công`).
- **Fix**:
  - Remove the mock text disclaimer and fake simulation button.
  - Implement a genuine primary payment button: "Tiến hành thanh toán VNPay".
  - When clicked (or when `paymentSession?.paymentUrl` is available), redirect the browser via `window.location.href = paymentSession.paymentUrl`.
  - Maintain the 10-minute hold countdown timer and reservation details display.

### Task 2: Support Dual Lookup (`id` & `ma_don_hang`) in `DonHangViewSet` for Order FSM Transitions
- **Files**: `moc-backend/orders/views.py`, `moc-frontend/src/api/orders.api.ts`
- **Issue**: When staff triggers FSM transitions in `AdminOrdersPage.tsx`, `updateAdminOrderStatus` sends `PATCH /api/orders/{code}/trang_thai/`. DRF's `DonHangViewSet` queries `pk` directly on string code and crashes with `ValueError: Field 'id' expected a number`.
- **Fix**:
  - In `moc-backend/orders/views.py`, override `get_object(self)` in `DonHangViewSet`:
    ```python
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_val = self.kwargs.get(lookup_url_kwarg)
        if lookup_val is None:
            return super().get_object()
        if str(lookup_val).isdigit():
            obj = get_object_or_404(queryset, pk=lookup_val)
        else:
            obj = get_object_or_404(queryset, ma_don_hang=lookup_val)
        self.check_object_permissions(self.request, obj)
        return obj
    ```
  - In `moc-frontend/src/api/orders.api.ts`: Ensure both numeric `id` and string `ma_don_hang` are properly exposed (`id: Number(order.id) || order.id`).

### Task 3: Fix Manual Inventory Transaction in `LichSuKhoViewSet`
- **Files**: `moc-backend/foods/views.py`, `moc-backend/foods/serializers.py`
- **Issue**: `LichSuKhoSerializer` treats `ton_kho_truoc` and `ton_kho_sau` as read-only. `LichSuKhoViewSet.perform_create` crashes with `IntegrityError: NOT NULL constraint failed: lich_su_xuat_nhap_kho.ton_kho_truoc` and fails to update `NguyenLieu.ton_kho_hien_tai`.
- **Fix**:
  - In `moc-backend/foods/views.py`, implement atomic transaction in `LichSuKhoViewSet.perform_create`:
    ```python
    from decimal import Decimal
    from django.db import transaction
    from rest_framework.exceptions import ValidationError

    class LichSuKhoViewSet(viewsets.ModelViewSet):
        queryset = LichSuXuatNhapKho.objects.select_related("nguyen_lieu")
        serializer_class = LichSuKhoSerializer
        permission_classes = [LaNhanVienHoacChiDoc]

        @transaction.atomic
        def perform_create(self, serializer):
            nguyen_lieu = serializer.validated_data["nguyen_lieu"]
            nl = NguyenLieu.objects.select_for_update().get(id=nguyen_lieu.id)
            so_luong = Decimal(str(serializer.validated_data["so_luong"]))
            loai_gd = serializer.validated_data["loai_giao_dich"]

            ton_truoc = nl.ton_kho_hien_tai
            if loai_gd == LichSuXuatNhapKho.LoaiGiaoDich.NHAP:
                ton_sau = ton_truoc + so_luong
            elif loai_gd == LichSuXuatNhapKho.LoaiGiaoDich.XUAT:
                if ton_truoc < so_luong:
                    raise ValidationError({"so_luong": f"Tồn kho hiện tại ({ton_truoc} {nl.don_vi}) không đủ để xuất {so_luong} {nl.don_vi}."})
                ton_sau = ton_truoc - so_luong
            elif loai_gd == LichSuXuatNhapKho.LoaiGiaoDich.DIEU_CHINH:
                ton_sau = so_luong
            else:
                raise ValidationError({"loai_giao_dich": f"Loại giao dịch '{loai_gd}' không hợp lệ."})

            nl.ton_kho_hien_tai = ton_sau
            nl.save(update_fields=["ton_kho_hien_tai", "cap_nhat_luc"])

            serializer.save(
                tao_boi=self.request.user,
                ton_kho_truoc=ton_truoc,
                ton_kho_sau=ton_sau,
            )
    ```

### Task 4: Fix Review Deletion Authorization and Dish Score Refresh
- **File**: `moc-backend/reviews/views.py` (`DanhGiaViewSet`)
- **Issue**: Missing `perform_destroy` authorization checks allow any customer to delete any review, and dish ratings are not updated upon review deletion.
- **Fix**:
  - In `moc-backend/reviews/views.py`, add `perform_destroy` to `DanhGiaViewSet`:
    ```python
    def perform_destroy(self, instance):
        user = self.request.user
        is_staff = user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)
        if instance.nguoi_dung_id != user.id and not is_staff:
            raise PermissionDenied("Bạn không có quyền xóa đánh giá này.")
        mon_an = instance.mon_an
        instance.delete()
        self._cap_nhat_diem_mon(mon_an)
    ```

## Verification Commands
After implementing, execute and verify:
1. `cd /Users/VuVan/Documents/DO-AN/moc-frontend && npx tsc --noEmit && npm run build` (Exit code 0)
2. `moc-backend/.venv/bin/python moc-backend/manage.py check` (0 issues)
3. `TESTING=1 moc-backend/.venv/bin/python tests/e2e/test_adversarial_m5_portals.py` (Must pass 16/16, 100%)
4. `moc-backend/.venv/bin/python tests/e2e/test_adversarial_m5_realtime.py` (29/29 PASS)
5. `moc-backend/.venv/bin/python moc-backend/manage.py test reviews orders foods reservations recommendations branches chat`
6. `moc-backend/.venv/bin/python tests/e2e/runner.py` (60/60 PASS)

## Deliverables
Write your 5-component handoff report (Observation, Logic Chain, Caveats, Conclusion, Verification Method) to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m5_2/handoff.md`


## 2026-10-15T00:08:44Z
Assignment received from orchestrator 4569185e-dbd8-4811-a385-d58c3b35b3ca.
