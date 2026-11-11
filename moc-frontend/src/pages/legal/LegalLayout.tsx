import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";

/** Chỗ chủ site phải tự điền: hiện nổi bật để không lọt lên bản chính thức. */
export function Dien({ children }: { children: ReactNode }) {
  return <mark className="bg-yellow-200 text-black px-1 rounded">[ĐIỀN: {children}]</mark>;
}

/** Hiện giá trị nếu đã có, chưa có thì hiện ô [ĐIỀN]. */
export function GiaTri({ value, ten }: { value: string | null; ten: string }) {
  return value ? <>{value}</> : <Dien>{ten}</Dien>;
}

export function Muc({ id, title, children }: { id?: string; title: string; children: ReactNode }) {
  return (
    <section id={id} className="scroll-mt-24">
      <h2 className="font-display text-[22px] leading-snug mb-3">{title}</h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

export function Bang({ head, rows }: { head: string[]; rows: ReactNode[][] }) {
  return (
    <div className="overflow-x-auto -mx-1 px-1">
      <table className="w-full min-w-[520px] text-sm border-collapse">
        <thead>
          <tr className="text-left border-b border-black/15">
            {head.map((h) => <th key={h} className="py-2 pr-4 font-semibold">{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-black/[0.07] align-top">
              {r.map((c, j) => <td key={j} className="py-2.5 pr-4">{c}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function LegalLayout({ title, updated, version, children }: {
  title: string; updated: string; version?: string; children: ReactNode;
}) {
  return (
    <div className="max-w-[820px] mx-auto px-5 md:px-8 py-12">
      <div className="flex items-center gap-1.5 text-[13px] text-muted mb-8">
        <Link to="/" className="hover:text-primary">Trang chủ</Link>
        <ChevronRight width={13} height={13} />
        <span>{title}</span>
      </div>
      <h1 className="font-display text-[30px] sm:text-[38px] leading-tight mb-3">{title}</h1>
      <p className="text-sm text-muted mb-10">
        Cập nhật lần cuối: {updated}{version && <> · Phiên bản {version}</>}
      </p>
      <div className="text-[15.5px] leading-[1.8] text-text space-y-10 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-1.5 [&_a]:text-primary [&_a]:underline [&_a]:underline-offset-2">
        {children}
      </div>
    </div>
  );
}
