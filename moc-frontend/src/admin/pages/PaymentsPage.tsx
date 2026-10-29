import { useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "@/hooks/useAsync";
import { formatCurrency } from "@/lib/utils";
import { needsRefund, paymentsStore, refundBucket, reservationsStore } from "../api/admin.api";
import DataTable from "../components/DataTable";
import ConfirmModal from "../components/ConfirmModal";
import { PageHeader, StatusBadge, Tabs } from "../components/primitives";
import { useToast } from "../components/toast";
import { useCan } from "../permissions";
import { fmtDateTime } from "../lib";
import type { AdminPayment } from "../types";

const STATUS = { pending: { label: "Chờ xử lý", tone: "warn" }, success: { label: "Thành công", tone: "ok" }, failed: { label: "Thất bại", tone: "danger" }, refunded: { label: "Đã hoàn", tone: "info" } } as const;
const METHOD = { cod: "Tiền mặt", bank: "Chuyển khoản", vnpay: "VNPay" };
const BUCKET = { ">24h": "Huỷ >24h", "6-24h": "Huỷ 6–24h", "<6h": "Huỷ <6h", no_show: "Không đến" };

export default function PaymentsPage() {
  const can = useCan();
  const push = useToast((s) => s.push);
  const [tab, setTab] = useState<"refund" | "all">("refund");
  const [confirming, setConfirming] = useState<AdminPayment | null>(null);
  const { data: payments, loading, refetch } = useAsync(() => paymentsStore.list());
  const { data: reservations, loading: loadingRes } = useAsync(() => reservationsStore.list());
  const queue = reservations?.filter(needsRefund);

  const markPaid = async () => {
    if (!confirming) return;
    await paymentsStore.update(confirming.id, { status: "success" });
    push("Đã xác nhận thanh toán"); setConfirming(null); refetch();
  };

  return (
    <div>
      <PageHeader title="Thanh toán & hoàn cọc" subtitle="Hoàn cọc làm thủ công qua lễ tân/CSKH: xác minh, chuyển khoản, rồi ghi nhận tại đây." />
      <div className="mb-4"><Tabs value={tab} onChange={setTab} items={[{ key: "refund", label: "Cọc chờ hoàn", count: queue?.length ?? 0 }, { key: "all", label: "Tất cả giao dịch" }]} /></div>
      {tab === "refund" ? (
        <DataTable
          loading={loadingRes} rows={queue} emptyTitle="Không có khoản cọc nào đang chờ hoàn" emptyHint="Khi khách huỷ hoặc không đến, khoản cọc đã thanh toán sẽ xuất hiện ở đây."
          columns={[
            { header: "Đặt bàn", cell: (r) => <div><b>{r.code}</b><div className="text-xs text-muted">{r.customer} · {r.phone}</div></div> },
            { header: "Giờ hẹn", cell: (r) => `${r.time} · ${r.date.split("-").reverse().join("/")}` },
            { header: "Mốc huỷ", cell: (r) => <StatusBadge tone="warn">{BUCKET[refundBucket(r)]}</StatusBadge> },
            { header: "Tiền cọc", cell: (r) => <b>{formatCurrency(r.depositAmount)}</b> },
            { header: "", className: "text-right", cell: (r) => <Link to={`/admin/reservations?open=${r.id}`} className="btn btn-outline py-2! px-4! text-[13px]!">Xử lý hoàn cọc</Link> },
          ]}
        />
      ) : (
        <DataTable
          loading={loading} rows={payments}
          columns={[
            { header: "Mã giao dịch", cell: (p) => <b>{p.code}</b> },
            { header: "Loại", cell: (p) => (p.kind === "deposit" ? "Tiền cọc" : "Đơn hàng") },
            { header: "Tham chiếu", cell: (p) => p.ref },
            { header: "Phương thức", cell: (p) => METHOD[p.method] },
            { header: "Số tiền", cell: (p) => <b>{formatCurrency(p.amount)}</b> },
            { header: "Trạng thái", cell: (p) => <StatusBadge tone={STATUS[p.status].tone}>{STATUS[p.status].label}</StatusBadge> },
            { header: "Thời gian", cell: (p) => <span className="text-muted">{fmtDateTime(p.createdAt)}</span> },
            { header: "", className: "text-right", cell: (p) => p.status === "pending" && can("payments", "update") && <button className="btn btn-outline py-2! px-4! text-[13px]!" onClick={() => setConfirming(p)}>Đã nhận tiền</button> },
          ]}
        />
      )}
      <ConfirmModal
        open={!!confirming} confirmLabel="Xác nhận" title="Xác nhận đã nhận tiền?"
        message={confirming ? `${confirming.code} · ${formatCurrency(confirming.amount)}. Chỉ xác nhận khi đã đối chiếu sao kê.` : ""}
        onConfirm={markPaid} onCancel={() => setConfirming(null)}
      />
    </div>
  );
}
