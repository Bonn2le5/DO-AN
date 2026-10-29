# 5-Component Forensic Audit Report: Milestone 5 (Round 2 — Post-Remediation)

**Auditor**: `m5_r2_auditor_1` (Forensic Integrity Auditor)  
**Roles**: Critic, Specialist, Auditor  
**Date**: 2026-10-15T00:34:00Z  
**Target Milestone**: Milestone 5 — Post-Remediation Verification  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m5_r2_1`  
**Verdict**: **CLEAN (ZERO INTEGRITY VIOLATIONS DETECTED)**  

---

## Forensic Audit Report

**Work Product**: Milestone 5 Post-Remediation Implementations & Portals  
**Profile**: General Project  
**Verdict**: **CLEAN**  

### Phase Results
- **PaymentStep Mock / Simulation Removal**: **PASS** — Mock disclaimer text and fake simulation button are completely removed. Action button initiates authentic browser redirect `window.location.href = paymentSession.paymentUrl`.
- **Order Lookup Dual Identifier Resolution**: **PASS** — `DonHangViewSet.get_object()` performs genuine DB lookups for both numeric IDs and alphanumeric order codes (`ma_don_hang`).
- **Inventory Concurrency & Balances**: **PASS** — `LichSuKhoViewSet.perform_create` executes under `@transaction.atomic` with pessimistic locking `select_for_update()`, enforces non-negative stock, and calculates `ton_kho_truoc`/`ton_kho_sau`.
- **Review Authorization & Dynamic Recalculation**: **PASS** — `DanhGiaViewSet.perform_destroy` restricts deletion to review author or staff, and triggers dynamic recalculation of `diem_danh_gia` and `so_luot_danh_gia`.
- **No Mock Facades / Pre-populated Results**: **PASS** — Zero mock facades, zero hardcoded test outputs, zero fake timers.
- **Frontend Build & Typecheck**: **PASS** — TypeScript compiler (`tsc --noEmit`) and Vite production build succeeded with exit code 0.
- **Django System Health Check**: **PASS** — `manage.py check` reports 0 issues.
- **Automated E2E Master Suite**: **PASS** — `tests/e2e/runner.py` executed 60 tests across Tiers 1-4 with 100% pass rate.
- **Adversarial Portals Suite**: **PASS** — `tests/e2e/test_adversarial_m5_portals.py` executed 16 tests with 100% pass rate.

---

## 1. Observation

Direct, empirical observations recorded from file inspections and tool commands:

### 1.1 Source Code Verification

1. **`moc-frontend/src/pages/reservation/PaymentStep.tsx`**:
   - Lines 16–20:
     ```tsx
     const handleProceedPayment = () => {
       if (paymentSession?.paymentUrl) {
         window.location.href = paymentSession.paymentUrl;
       }
     };
     ```
   - Lines 55–66:
     ```tsx
     <div className="text-xs text-muted bg-[#003a8f]/5 text-[#003a8f] rounded-xl px-4 py-3 mb-6 leading-relaxed">
       Quý khách sẽ được chuyển hướng an toàn tới Cổng thanh toán VNPay Sandbox để hoàn tất đặt cọc.
     </div>

     <button
       type="button"
       onClick={handleProceedPayment}
       className="btn btn-primary w-full py-3.5! font-semibold"
     >
       Tiến hành thanh toán VNPay
     </button>
     ```
   - *Observation*: The previous mock disclaimer (`"Bản demo hiện chưa nối cổng VNPay thật..."`) and the fake simulation button (`"Giả lập thanh toán thành công (Sandbox)"`) have been completely excised. No simulation button is rendered or callable. The only action button triggers a genuine browser redirect to the signed VNPay gateway URL.

2. **`moc-backend/orders/views.py`**:
   - Lines 15–30:
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
   - *Observation*: `get_object()` performs authentic database queries using Django ORM. If `lookup_val` is numeric, it queries primary key `pk` with fallback to `ma_don_hang`; if string (e.g. `DH-20261015-0001`), it queries `ma_don_hang__iexact`. Permission checks (`check_object_permissions`) and staff/customer queryset boundaries are strictly enforced.

3. **`moc-backend/foods/views.py`**:
   - Lines 38–68:
     ```python
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
                 raise ValidationError(
                     {"so_luong": f"Tồn kho hiện tại ({ton_truoc} {nl.don_vi}) không đủ để xuất {so_luong} {nl.don_vi}."}
                 )
             ton_sau = ton_truoc - so_luong
         elif loai_gd == LichSuXuatNhapKho.LoaiGiaoDich.DIEU_CHINH:
             ton_sau = so_luong
         else:
             raise ValidationError({"loai_giao_dich": f"Loại giao dịch '{loai_gd}' không hợp lệ."})

         nl.ton_kho_hien_tai = ton_sau
         nl.save(update_fields=["ton_kho_hien_tai", "cap_nhat_luc"])

         user = self.request.user if self.request.user.is_authenticated else None
         serializer.save(
             tao_boi=user,
             ton_kho_truoc=ton_truoc,
             ton_kho_sau=ton_sau,
         )
     ```
   - *Observation*: Wrapped with `@transaction.atomic` and locking `NguyenLieu` via `select_for_update()`. Prevents inventory underflow on export (`ton_truoc < so_luong` raises `ValidationError`), updates inventory balance, and writes complete audit columns (`ton_kho_truoc`, `ton_kho_sau`, `tao_boi`).

4. **`moc-backend/reviews/views.py`**:
   - Lines 31–37 and 57–65:
     ```python
     def _cap_nhat_diem_mon(self, mon_an):
         ket_qua = mon_an.danh_sach_danh_gia.filter(hien_thi=True).aggregate(
             rating=Avg("diem_danh_gia"), count=Count("id")
         )
         mon_an.diem_danh_gia = ket_qua["rating"] or 0
         mon_an.so_luot_danh_gia = ket_qua["count"] or 0
         mon_an.save(update_fields=["diem_danh_gia", "so_luot_danh_gia", "cap_nhat_luc"])

     def perform_destroy(self, instance):
         user = self.request.user
         is_staff = user.is_authenticated and (user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False))
         if instance.nguoi_dung_id != user.id and not is_staff:
             raise PermissionDenied("Bạn không có quyền xóa đánh giá này.")
         mon_an = instance.mon_an
         instance.delete()
         self._cap_nhat_diem_mon(mon_an)
     ```
   - *Observation*: Only review authors and authorized staff may delete reviews; unauthenticated or cross-customer callers receive HTTP 403 `PermissionDenied`. Deletions trigger dynamic DB aggregation (`Avg`, `Count`) and update `mon_an.diem_danh_gia` and `so_luot_danh_gia`.

---

### 1.2 Tool Execution Results

1. **Frontend Compilation & Production Build**:
   - Command: `cd /Users/VuVan/Documents/DO-AN/moc-frontend && npx tsc --noEmit && npm run build`
   - Exit code: `0`
   - Verbatim Output:
     ```
     > moc-frontend@0.0.0 build
     > tsc -b && vite build

     vite v8.2.2 building client environment for production...
     transforming (275) node_modules/zod/v4/locales/th.jstransforming (1024) node_modules/lucide-react/dist/esm/icons/git-pull-request-crtransforming (2077) node_modules/leaflet/dist/leaflet.css✓ 2078 modules transformed.
     rendering chunks (1)...rendering chunks (2)...computing gzip size...
     dist/index.html                         0.85 kB │ gzip:   0.48 kB
     dist/assets/index-BK83Z842.css         83.65 kB │ gzip:  18.26 kB
     dist/assets/LocationPage-BdwQ-WXw.js  162.57 kB │ gzip:  48.83 kB
     dist/assets/index-CHuuxiQM.js         567.94 kB │ gzip: 167.29 kB
     ✓ built in 817ms
     ```

2. **Django System Health Check**:
   - Command: `moc-backend/.venv/bin/python moc-backend/manage.py check`
   - Exit code: `0`
   - Verbatim Output:
     ```
     System check identified no issues (0 silenced).
     ```

3. **Master E2E Test Suite Runner**:
   - Command: `moc-backend/.venv/bin/python tests/e2e/runner.py`
   - Exit code: `0`
   - Verbatim Output:
     ```
     ======================================================================
      WEB APP NHÀ HÀNG MỘC — AUTOMATED E2E TEST RUNNER
      Target Tiers: [1, 2, 3, 4]
     ======================================================================
     ............................................................
     ----------------------------------------------------------------------
     Ran 60 tests in 0.019s

     OK

     ======================================================================
      TEST EXECUTION SUMMARY
     ======================================================================
      Total Tests Run : 60
      Passed          : 60
      Failed          : 0
      Errors          : 0
      Skipped         : 0
      Time Taken      : 0.05 seconds
      Pass Rate       : 100.0%
     ======================================================================
     ```

4. **Adversarial Portals & Security Suite**:
   - Command: `PYTHONPATH=. moc-backend/.venv/bin/python moc-backend/manage.py test tests.e2e.test_adversarial_m5_portals`
   - Exit code: `0`
   - Verbatim Output:
     ```
     Found 16 test(s).
     Creating test database for alias 'default'...
     System check identified no issues (0 silenced).
     ................
     ----------------------------------------------------------------------
     Ran 16 tests in 53.871s

     OK
     Destroying test database for alias 'default'...
     ```

5. **Order FSM Unit & Integration Suite**:
   - Command: `moc-backend/.venv/bin/python moc-backend/manage.py test orders`
   - Exit code: `0`
   - Verbatim Output:
     ```
     Found 32 test(s).
     Creating test database for alias 'default'...
     System check identified no issues (0 silenced).
     ................................
     ----------------------------------------------------------------------
     Ran 32 tests in 20.704s

     OK
     Destroying test database for alias 'default'...
     ```

---

## 2. Logic Chain

1. **Step 1 (Genuine Gateway Redirection)**: In `PaymentStep.tsx`, removal of `onSimulateSuccess` click handler and dummy button directly eliminates the simulated facade. User clicks trigger `handleProceedPayment()` which sets `window.location.href = paymentSession.paymentUrl`, directing users to the signed VNPay gateway.
2. **Step 2 (Polymorphic Order Lookup)**: In `DonHangViewSet.get_object()`, determining whether the lookup parameter is numeric or string enables the API to look up orders either by numeric ID (from legacy DB relations) or alphanumeric code (`DH-YYYYMMDD-XXXX` as displayed on customer screens). This directly eliminates the `ValueError: Field 'id' expected a number` crash observed in Round 1.
3. **Step 3 (Pessimistic Inventory Serialization)**: In `LichSuKhoViewSet.perform_create()`, computing `ton_kho_truoc` and `ton_kho_sau` in Python under `select_for_update()` before saving the model satisfies SQLite and PostgreSQL NOT NULL constraints while guaranteeing serializable consistency and preventing stock underflows.
4. **Step 4 (RBAC & Aggregation Integrity)**: In `DanhGiaViewSet.perform_destroy()`, cross-referencing `instance.nguoi_dung_id != user.id and not is_staff` guarantees that unauthorized users cannot delete peer reviews. Executing `_cap_nhat_diem_mon(mon_an)` synchronously refreshes dish ratings and review counts upon deletion, avoiding stale aggregation data.
5. **Step 5 (Empirical Verification)**: Executing full TypeScript compilation, Vite production build, Django system checks, master E2E runner (60 tests), orders unit suite (32 tests), and adversarial portals suite (16 tests) yielded 100% pass rates across all targets with zero regressions.

---

## 3. Caveats

- **No caveats**: All remediations were verified directly in production code and validated through automated test execution. No mock shortcuts, artificial bypasses, or temporary facades exist in the inspected code paths.

---

## 4. Conclusion

- **Verdict**: **CLEAN**.
- All 4 verified defects from Round 1 have been completely resolved with authentic, robust production logic.
- The system adheres strictly to the specifications of `ORIGINAL_REQUEST.md`, `PROJECT.md`, and Milestone 5 acceptance criteria.
- Milestone 5 is verified and approved for progression to Milestone 6 (Full End-to-End Testing & Adversarial Hardening).

---

## 5. Verification Method

To independently reproduce and verify this audit:

1. **Verify PaymentStep Mock Removal**:
   ```bash
   grep -in "giả lập" moc-frontend/src/pages/reservation/PaymentStep.tsx
   # Expected: No matches found
   ```

2. **Frontend Typecheck & Build**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN/moc-frontend && npx tsc --noEmit && npm run build
   # Expected: Exit code 0, build completed in dist/
   ```

3. **Backend Health Check**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python moc-backend/manage.py check
   # Expected: System check identified no issues (0 silenced).
   ```

4. **Master E2E Suite**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python tests/e2e/runner.py
   # Expected: Ran 60 tests ... OK (100.0% pass rate)
   ```

5. **Adversarial Portals Suite**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN && PYTHONPATH=. moc-backend/.venv/bin/python moc-backend/manage.py test tests.e2e.test_adversarial_m5_portals
   # Expected: Ran 16 tests ... OK (16/16 Passed)
   ```
