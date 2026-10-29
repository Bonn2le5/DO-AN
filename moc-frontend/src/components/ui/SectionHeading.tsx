import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

export default function SectionHeading({
  eyebrow,
  title,
  linkTo,
  linkLabel = "Xem tất cả",
  children,
}: {
  eyebrow: string;
  title: string;
  linkTo?: string;
  linkLabel?: string;
  children?: ReactNode;
}) {
  return (
    <div className="flex items-end justify-between gap-6 flex-wrap mb-11">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h2 className="font-display text-[32px] sm:text-[38px]">{title}</h2>
        {children}
      </div>
      {linkTo && (
        <Link
          to={linkTo}
          className="text-sm font-semibold flex items-center gap-1.5 border-b-[1.5px] border-dark pb-0.5 hover:text-primary hover:border-primary transition-colors"
        >
          {linkLabel} <ArrowRight width={15} height={15} />
        </Link>
      )}
    </div>
  );
}
