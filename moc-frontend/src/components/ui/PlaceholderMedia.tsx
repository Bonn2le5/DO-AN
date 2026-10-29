import type { LucideIcon } from "lucide-react";
import { toneGradient, cn } from "@/lib/utils";

interface PlaceholderMediaProps {
  tone: number;
  icon: LucideIcon;
  className?: string;
  iconClassName?: string;
}

/**
 * Stand-in for real food photography until actual restaurant images are
 * uploaded through the admin Food Management screen (see backend `foods` app).
 */
export default function PlaceholderMedia({
  tone,
  icon: Icon,
  className,
  iconClassName,
}: PlaceholderMediaProps) {
  return (
    <div
      className={cn("flex items-center justify-center", className)}
      style={{ background: toneGradient(tone) }}
    >
      <Icon className={cn("text-white/90", iconClassName ?? "w-10 h-10")} strokeWidth={1.4} />
    </div>
  );
}
