import { useEffect, useState } from "react";
import { Clock } from "lucide-react";
import { cn } from "@/lib/utils";

export default function HoldCountdown({ until, label }: { until: string; label: string }) {
  const [remaining, setRemaining] = useState(() => Math.max(0, new Date(until).getTime() - Date.now()));

  useEffect(() => {
    const interval = setInterval(() => {
      setRemaining(Math.max(0, new Date(until).getTime() - Date.now()));
    }, 1000);
    return () => clearInterval(interval);
  }, [until]);

  const minutes = Math.floor(remaining / 60000);
  const seconds = Math.floor((remaining % 60000) / 1000);
  const low = remaining < 60000;

  return (
    <div className={cn("inline-flex items-center gap-2 px-3.5 py-2 rounded-full text-[13px] font-semibold", low ? "bg-primary/10 text-primary" : "bg-accent/10 text-accent")}>
      <Clock width={14} height={14} />
      {label}: {minutes}:{String(seconds).padStart(2, "0")}
    </div>
  );
}
