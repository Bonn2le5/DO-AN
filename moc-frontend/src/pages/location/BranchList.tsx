import { MapPin, Phone, Clock, Navigation, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Branch, RouteInfo } from "@/types";

interface BranchListProps {
  branches: Branch[];
  selectedBranchId: string | null;
  onSelect: (branch: Branch) => void;
  route: RouteInfo | null;
  routeLoading: boolean;
  hasUserLocation: boolean;
}

export default function BranchList({
  branches,
  selectedBranchId,
  onSelect,
  route,
  routeLoading,
  hasUserLocation,
}: BranchListProps) {
  return (
    <div className="space-y-3">
      {branches.map((branch) => {
        const active = branch.id === selectedBranchId;
        return (
          <button
            key={branch.id}
            onClick={() => onSelect(branch)}
            className={cn(
              "w-full text-left card p-5 transition-colors",
              active ? "border-primary bg-primary/5" : "hover:border-black/20",
            )}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-display text-lg">{branch.name}</h3>
                  {branch.isMain && (
                    <span className="text-[10px] font-bold uppercase bg-accent/15 text-accent px-2 py-0.5 rounded-full">
                      Trụ sở
                    </span>
                  )}
                </div>
              </div>
              <Navigation
                width={16}
                height={16}
                className={cn(
                  "shrink-0 mt-1",
                  active ? "text-primary" : "text-muted",
                )}
              />
            </div>

            <div className="mt-3 space-y-1.5 text-[13px] text-muted">
              <div className="flex items-start gap-2">
                <MapPin width={13} height={13} className="mt-0.5 shrink-0" />
                <span>{branch.address}</span>
              </div>
              <div className="flex items-center gap-2">
                <Phone width={13} height={13} className="shrink-0" />
                <span>{branch.phone}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock width={13} height={13} className="shrink-0" />
                <span>{branch.openHours}</span>
              </div>
            </div>

            {active && (
              <div className="mt-3 pt-3 border-t border-black/8 flex items-center justify-between">
                {!hasUserLocation ? (
                  <span className="text-xs text-muted">
                    Bật định vị để xem khoảng cách
                  </span>
                ) : routeLoading ? (
                  <span className="text-xs text-muted">
                    Đang tính đường đi...
                  </span>
                ) : route ? (
                  <span className="text-sm font-semibold text-primary">
                    {route.distanceKm} km · ~{route.durationMinutes} phút lái xe
                  </span>
                ) : (
                  <span className="text-xs text-muted">
                    Không tính được khoảng cách
                  </span>
                )}
                <a
                  href={`https://www.google.com/maps/dir/?api=1&destination=${branch.lat},${branch.lng}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="text-xs font-semibold text-primary flex items-center gap-1 hover:underline shrink-0"
                >
                  Google Maps <ExternalLink width={11} height={11} />
                </a>
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
