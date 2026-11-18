import { cn } from "@/lib/utils";

/** Tin hệ thống (kết thúc / mở lại cuộc tư vấn) hiện thành dòng phân cách giữa khung chat. */
export default function SystemDivider({ text, time, className }: { text: string; time?: string; className?: string }) {
  return (
    <div role="separator" aria-label={text} className={cn("my-2 flex items-center gap-3 text-xs text-muted", className)}>
      <span className="h-px flex-1 bg-current opacity-25" />
      <span className="shrink-0 text-center">
        {text}
        {time && <span className="ml-1.5 opacity-70 tabular-nums">{time}</span>}
      </span>
      <span className="h-px flex-1 bg-current opacity-25" />
    </div>
  );
}
