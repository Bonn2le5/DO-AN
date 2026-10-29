import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
} from "react-leaflet";
import { branchIcon, branchIconActive, userIcon } from "./mapIcons";
import type { Branch, RouteInfo } from "@/types";
import type { UserCoords } from "@/api/locations.api";

interface DirectionsMapProps {
  branches: Branch[];
  selectedBranchId: string | null;
  userLocation: UserCoords | null;
  route: RouteInfo | null;
}

export default function DirectionsMap({
  branches,
  selectedBranchId,
  userLocation,
  route,
}: DirectionsMapProps) {
  const center: [number, number] = userLocation
    ? [userLocation.lat, userLocation.lng]
    : [branches[0]?.lat ?? 10.7769, branches[0]?.lng ?? 106.7009];

  return (
    <div className="rounded-[20px] overflow-hidden border border-black/820px] md:h-140">
      <MapContainer
        center={center}
        zoom={13}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {branches.map((b) => (
          <Marker
            key={b.id}
            position={[b.lat, b.lng]}
            icon={b.id === selectedBranchId ? branchIconActive : branchIcon}
          >
            <Popup>
              <strong>{b.name}</strong>
              <br />
              {b.address}
            </Popup>
          </Marker>
        ))}

        {userLocation && (
          <Marker
            position={[userLocation.lat, userLocation.lng]}
            icon={userIcon}
          >
            <Popup>Vị trí của bạn</Popup>
          </Marker>
        )}

        {route && route.geometry.length > 0 && (
          <Polyline
            positions={route.geometry}
            pathOptions={{ color: "#B85C38", weight: 4, opacity: 0.85 }}
          />
        )}

        <FitBounds
          branches={branches}
          userLocation={userLocation}
          route={route}
        />
      </MapContainer>
    </div>
  );
}

/** Re-fits the map viewport whenever the route or marker set changes. */
function FitBounds({
  branches,
  userLocation,
  route,
}: {
  branches: Branch[];
  userLocation: UserCoords | null;
  route: RouteInfo | null;
}) {
  const map = useMap();

  useEffect(() => {
    const points: [number, number][] = route?.geometry.length
      ? route.geometry
      : [
          ...branches.map((b) => [b.lat, b.lng] as [number, number]),
          ...(userLocation
            ? [[userLocation.lat, userLocation.lng] as [number, number]]
            : []),
        ];
    if (points.length === 0) return;
    if (points.length === 1) {
      map.setView(points[0], 14);
      return;
    }
    map.fitBounds(points, { padding: [40, 40] });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [branches, userLocation, route]);

  return null;
}
