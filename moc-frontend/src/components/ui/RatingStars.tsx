import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

export default function RatingStars({
  rating,
  size = 13,
  className,
}: {
  rating: number;
  size?: number;
  className?: string;
}) {
  return (
    <div className={cn("flex items-center gap-0.5", className)}>
      {Array.from({ length: 5 }).map((_, i) => {
        const filled = i < Math.round(rating);
        return (
          <Star
            key={i}
            width={size}
            height={size}
            className={filled ? "fill-accent stroke-accent" : "fill-none stroke-muted"}
          />
        );
      })}
    </div>
  );
}
