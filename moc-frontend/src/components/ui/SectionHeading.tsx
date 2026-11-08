import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

export default function SectionHeading({
  eyebrow,
  title,
  linkTo,
  linkLabel = "Xem tất cả",
  align = "left",
  children,
}: {
  eyebrow?: string;
  title: string;
  linkTo?: string;
  linkLabel?: string;
  align?: "left" | "center";
  children?: ReactNode;
}) {
  if (align === "center") {
    return (
      <div className="text-center max-w-170 mx-auto mb-14">
        {eyebrow && (
          <div className="text-[12.5px] font-bold uppercase tracking-[0.2em] text-primary mb-3">
            {eyebrow}
          </div>
        )}
        <h2 className="font-display text-[34px] sm:text-[46px] leading-tight">{title}</h2>
        <div className="w-16 h-0.5 bg-primary mx-auto mt-5" />
        {children && <div className="text-muted text-[16px] leading-relaxed mt-5">{children}</div>}
      </div>
    );
  }

  return (
    <div className="flex items-end justify-between gap-6 flex-wrap mb-11">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h2 className="font-display text-[32px] sm:text-[38px]">{title}</h2>
        {children}
      </div>
      {linkTo && (
        <Link
          to={linkTo}
          className={cn(
            "text-sm font-semibold flex items-center gap-1.5 border-b-[1.5px] border-dark pb-0.5 hover:text-primary hover:border-primary transition-colors",
          )}
        >
          {linkLabel} <ArrowRight width={15} height={15} />
        </Link>
      )}
    </div>
  );
}
