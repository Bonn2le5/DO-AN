import { useState } from "react";
import { LocateFixed, AlertCircle } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import {
  getBranches,
  getUserLocation,
  getRoute,
  type UserCoords,
} from "@/api/locations.api";
import DirectionsMap from "./DirectionsMap";
import BranchList from "./BranchList";
import type { Branch, RouteInfo } from "@/types";

export default function LocationPage() {
  const { data: branches, loading: branchesLoading } = useAsync(getBranches);

  const [userLocation, setUserLocation] = useState<UserCoords | null>(null);
  const [locating, setLocating] = useState(false);
  const [locationError, setLocationError] = useState("");

  const [selectedBranchId, setSelectedBranchId] = useState<string | null>(null);
  const [route, setRoute] = useState<RouteInfo | null>(null);
  const [routeLoading, setRouteLoading] = useState(false);

  const handleLocate = async () => {
    setLocating(true);
    setLocationError("");
    try {
      const coords = await getUserLocation();
      setUserLocation(coords);
      if (selectedBranchId && branches) {
        const branch = branches.find((b) => b.id === selectedBranchId);
        if (branch) await fetchRoute(coords, branch);
      }
    } catch (err) {
      setLocationError(
        err instanceof Error ? err.message : "Không thể lấy vị trí của bạn.",
      );
    } finally {
      setLocating(false);
    }
  };

  const fetchRoute = async (from: UserCoords, branch: Branch) => {
    setRouteLoading(true);
    setRoute(null);
    try {
      const result = await getRoute(from, { lat: branch.lat, lng: branch.lng });
      setRoute(result);
    } catch {
      setRoute(null);
    } finally {
      setRouteLoading(false);
    }
  };

  const handleSelectBranch = async (branch: Branch) => {
    setSelectedBranchId(branch.id);
    if (userLocation) await fetchRoute(userLocation, branch);
  };

  return (
    <div className="max-w-310 mx-auto px-5 md:px-8 py-12">
      <div className="mb-8 flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="eyebrow">Chi nhánh</div>
          <h1 className="font-display text-[32px] sm:text-[38px]">
            Tìm đường đến MỘC
          </h1>
          <p className="text-muted mt-2 max-w-lg">
            Bật định vị để xem chi nhánh gần bạn nhất và chỉ đường trực tiếp
            trên bản đồ.
          </p>
        </div>
        <button
          onClick={handleLocate}
          disabled={locating}
          className="btn btn-primary disabled:opacity-60"
        >
          <LocateFixed width={16} height={16} />
          {locating
            ? "Đang định vị..."
            : userLocation
              ? "Định vị lại"
              : "Dùng vị trí của tôi"}
        </button>
      </div>

      {locationError && (
        <div className="flex items-start gap-2.5 bg-primary/5 border border-primary/20 text-primary text-sm rounded-xl px-4 py-3.5 mb-6">
          <AlertCircle width={16} height={16} className="shrink-0.5" />
          {locationError}
        </div>
      )}

      <div className="grid md:grid-cols-[380px_1fr] gap-8">
        <div className="order-2 md:order-1 max-h-140rflow-y-auto pr-1">
          {branchesLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="h-40 rounded-card bg-black/5 animate-pulse"
                />
              ))}
            </div>
          ) : (
            <BranchList
              branches={branches ?? []}
              selectedBranchId={selectedBranchId}
              onSelect={handleSelectBranch}
              route={route}
              routeLoading={routeLoading}
              hasUserLocation={!!userLocation}
            />
          )}
        </div>

        <div className="order-1 md:order-2">
          <DirectionsMap
            branches={branches ?? []}
            selectedBranchId={selectedBranchId}
            userLocation={userLocation}
            route={route}
          />
        </div>
      </div>
    </div>
  );
}
