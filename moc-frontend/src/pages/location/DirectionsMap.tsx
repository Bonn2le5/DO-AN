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
import type { ChiNhanh, ThongTinTuyenDuong } from "@/types";
import type { UserCoords } from "@/api/locations.api";

interface DirectionsMapProps {
  branches: ChiNhanh[];
  selectedBranchId: string | null;
  userLocation: UserCoords | null;
  route: ThongTinTuyenDuong | null;
}

export default function DirectionsMap({
  branches,
  selectedBranchId,
  userLocation,
  route,
}: DirectionsMapProps) {
  const center: [number, number] = userLocation
    ? [userLocation.lat, userLocation.lng]
    : [branches[0]?.viDo ?? 10.7769, branches[0]?.kinhDo ?? 106.7009];

  return (
    <div className="rounded-[20px] overflow-hidden border border-black/8 h-[420px] md:h-140">
      <MapContainer
        center={center}
        zoom={13}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom
      >
        <TileLayer
          // tile.openstreetmap.org is unreachable on some networks; OSM France mirror needs no API key.
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, tiles by <a href="https://www.openstreetmap.fr">OSM France</a>'
          url="https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png"
          maxZoom={20}
        />

        {branches.map((b) => (
          <Marker
            key={b.id}
            position={[b.viDo, b.kinhDo]}
            icon={b.id === selectedBranchId ? branchIconActive : branchIcon}
          >
            <Popup>
              <strong>{b.tenChiNhanh}</strong>
              <br />
              {b.diaChi}
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

        {route && route.toaDoTuyenDuong.length > 0 && (
          <Polyline
            positions={route.toaDoTuyenDuong}
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
  branches: ChiNhanh[];
  userLocation: UserCoords | null;
  route: ThongTinTuyenDuong | null;
}) {
  const map = useMap();

  useEffect(() => {
    const points: [number, number][] = route?.toaDoTuyenDuong.length
      ? route.toaDoTuyenDuong
      : [
          ...branches.map((b) => [b.viDo, b.kinhDo] as [number, number]),
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
