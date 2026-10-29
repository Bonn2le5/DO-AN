import { fmtShort } from "../lib";

export function LineChart({ data }: { data: { label: string; value: number }[] }) {
  const W = 600, H = 220, P = { l: 44, r: 12, t: 12, b: 28 };
  const max = Math.max(...data.map((d) => d.value), 1) * 1.1;
  const x = (i: number) => P.l + (i * (W - P.l - P.r)) / Math.max(1, data.length - 1);
  const y = (v: number) => P.t + (1 - v / max) * (H - P.t - P.b);
  const line = data.map((d, i) => `${i ? "L" : "M"}${x(i)},${y(d.value)}`).join(" ");
  const area = `${line} L${x(data.length - 1)},${H - P.b} L${x(0)},${H - P.b} Z`;
  const ticks = [0, 0.5, 1].map((t) => t * max);
  const step = Math.ceil(data.length / 6);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label="Biểu đồ doanh thu theo ngày">
      {ticks.map((t) => (
        <g key={t}>
          <line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} stroke="rgba(23,23,23,0.08)" />
          <text x={P.l - 8} y={y(t) + 4} textAnchor="end" fontSize="11" fill="var(--color-muted)">{fmtShort(t)}</text>
        </g>
      ))}
      <path d={area} fill="var(--color-primary)" opacity="0.1" />
      <path d={line} fill="none" stroke="var(--color-primary)" strokeWidth="2.5" strokeLinejoin="round" />
      {data.map((d, i) => (
        <g key={d.label + i}>
          <circle cx={x(i)} cy={y(d.value)} r="4" fill="white" stroke="var(--color-primary)" strokeWidth="2"><title>{`${d.label}: ${d.value.toLocaleString("vi-VN")}đ`}</title></circle>
          {i % step === 0 && <text x={x(i)} y={H - 8} textAnchor="middle" fontSize="11" fill="var(--color-muted)">{d.label}</text>}
        </g>
      ))}
    </svg>
  );
}

export function Donut({ parts }: { parts: { label: string; value: number; color: string }[] }) {
  const total = parts.reduce((s, p) => s + p.value, 0) || 1;
  const R = 54, C = 2 * Math.PI * R;
  let offset = 0;
  return (
    <div className="flex items-center gap-6 flex-wrap">
      <svg viewBox="0 0 140 140" className="w-36 h-36 -rotate-90 shrink-0" role="img" aria-label="Đơn hàng theo trạng thái">
        {parts.map((p) => {
          const len = (p.value / total) * C;
          const el = <circle key={p.label} cx="70" cy="70" r={R} fill="none" stroke={p.color} strokeWidth="18" strokeDasharray={`${len} ${C - len}`} strokeDashoffset={-offset} />;
          offset += len;
          return el;
        })}
      </svg>
      <ul className="space-y-1.5 text-sm">
        {parts.map((p) => (
          <li key={p.label} className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: p.color }} />
            <span className="text-muted">{p.label}</span><b className="ml-1">{p.value}</b>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function BarList({ items, unit = "" }: { items: readonly (readonly [string, number])[]; unit?: string }) {
  const max = Math.max(...items.map((i) => i[1]), 1);
  return (
    <ul className="space-y-3">
      {items.map(([label, value]) => (
        <li key={label}>
          <div className="flex justify-between text-sm mb-1"><span>{label}</span><b>{value.toLocaleString("vi-VN")}{unit}</b></div>
          <div className="h-2 rounded-full bg-black/6 overflow-hidden"><div className="h-full rounded-full bg-primary" style={{ width: `${(value / max) * 100}%` }} /></div>
        </li>
      ))}
    </ul>
  );
}
