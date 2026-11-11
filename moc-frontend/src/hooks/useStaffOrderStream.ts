/**
 * Luồng realtime cho màn hình nhân viên: một kết nối /ws/don-hang/nhan-vien/ cho cả khu admin
 * (mở ở AdminLayout), phát lại sự kiện cho các trang qua window event.
 *
 * Sự kiện chỉ báo "cái gì đổi ở chi nhánh nào"; trang nhận tự tải lại qua REST (useKhiVanHanhDoi).
 */
import { useEffect, useRef, useState } from "react";
import { openAuthenticatedWebSocket, scheduleCurrentWebSocketRenewal } from "@/services/websocket";
import { refreshAccessToken } from "@/api/client";

export type DoiTuongVanHanh = "ban_an" | "phien_phuc_vu" | "dat_ban" | "don_hang";

export interface SuKienVanHanh {
  doiTuong: DoiTuongVanHanh;
  id: number | null;
  chiNhanhId: number | null;
}

const SU_KIEN = "moc:van-hanh";
/** Phát khi kết nối lại sau khi mất: các trang tải lại để bù sự kiện đã lỡ. */
const KET_NOI_LAI = "moc:van-hanh-ket-noi-lai";

function phat(chiTiet: SuKienVanHanh) {
  window.dispatchEvent(new CustomEvent<SuKienVanHanh>(SU_KIEN, { detail: chiTiet }));
}

/** Mở kết nối khi `batDau` = true. Trả về trạng thái kết nối. */
export function useStaffOrderStream(batDau: boolean) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!batDau) return;

    let dangDong = false;
    let daTungMo = false;
    let lanThu = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let huyGiaHan: (() => void) | undefined;

    async function connect() {
      if (dangDong) return;
      const ws = await openAuthenticatedWebSocket("/ws/don-hang/nhan-vien/");
      if (!ws) return; // chưa đăng nhập / token hết hạn
      if (dangDong) {
        ws.close();
        return;
      }
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        lanThu = 0;
        huyGiaHan = scheduleCurrentWebSocketRenewal(ws);
        if (daTungMo) window.dispatchEvent(new Event(KET_NOI_LAI));
        daTungMo = true;
      };

      ws.onmessage = (event) => {
        try {
          const d = JSON.parse(event.data);
          if (d.type === "van_hanh_cap_nhat") {
            phat({ doiTuong: d.doi_tuong, id: d.id ?? null, chiNhanhId: d.chi_nhanh_id ?? null });
          } else if (d.type === "order_status_update" || d.type === "order_created") {
            const don = d.order ?? d.data ?? d;
            phat({ doiTuong: "don_hang", id: d.order_id ?? don.id ?? null, chiNhanhId: don.chi_nhanh_id ?? null });
          }
        } catch {
          /* bỏ qua khung lỗi */
        }
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        huyGiaHan?.();
        if (dangDong || event.code === 4403) return; // không có quyền: không thử lại
        if (event.code === 4401) {
          void refreshAccessToken().then((token) => { if (token && !dangDong) void connect(); });
        } else if (event.code === 4001) {
          void connect(); // vừa làm mới token
        } else {
          timer = setTimeout(() => void connect(), Math.min(1000 * 2 ** lanThu++, 15_000));
        }
      };
    }

    void connect();
    return () => {
      dangDong = true;
      clearTimeout(timer);
      huyGiaHan?.();
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [batDau]);

  return { isConnected };
}

/**
 * Gọi `taiLai` khi một trong `doiTuong` đổi (ở `chiNhanhId` nếu có) hoặc khi vừa kết nối lại.
 * Nhiều sự kiện liền nhau (một thao tác lưu nhiều bảng) được gom thành một lần tải sau `doTre` ms.
 */
export function useKhiVanHanhDoi(
  doiTuong: DoiTuongVanHanh[],
  taiLai: () => void,
  { chiNhanhId, doTre = 400 }: { chiNhanhId?: string | null; doTre?: number } = {},
) {
  const taiLaiRef = useRef(taiLai);
  useEffect(() => { taiLaiRef.current = taiLai; }, [taiLai]);
  const khoa = doiTuong.join(",");

  useEffect(() => {
    const ds = khoa.split(",");
    let hen: ReturnType<typeof setTimeout> | undefined;
    const lenLich = () => {
      clearTimeout(hen);
      hen = setTimeout(() => taiLaiRef.current(), doTre);
    };
    const nghe = (e: Event) => {
      const d = (e as CustomEvent<SuKienVanHanh>).detail;
      if (!ds.includes(d.doiTuong)) return;
      if (chiNhanhId && d.chiNhanhId != null && String(d.chiNhanhId) !== String(chiNhanhId)) return;
      lenLich();
    };
    window.addEventListener(SU_KIEN, nghe);
    window.addEventListener(KET_NOI_LAI, lenLich);
    return () => {
      clearTimeout(hen);
      window.removeEventListener(SU_KIEN, nghe);
      window.removeEventListener(KET_NOI_LAI, lenLich);
    };
  }, [khoa, chiNhanhId, doTre]);
}
