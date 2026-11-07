'use client';

import { useMemo } from 'react';
import { CircleMarker, MapContainer, Polygon, TileLayer, useMapEvents } from 'react-leaflet';
import { LatLng } from 'leaflet';
import 'leaflet/dist/leaflet.css';

export interface FarmMapProps {
  /** Polygon vertices in lat/lon (E4 wire format). */
  points: { lat: number; lon: number }[];
  onAddPoint: (lat: number, lon: number) => void;
  /** Optional single pin (home location selection). */
  pin?: { lat: number; lon: number } | null;
  onPin?: (lat: number, lon: number) => void;
  center?: [number, number];
  zoom?: number;
}

function ClickHandler({
  onAddPoint,
  onPin,
}: Pick<FarmMapProps, 'onAddPoint' | 'onPin'>) {
  useMapEvents({
    click(e) {
      if (onPin) onPin(e.latlng.lat, e.latlng.lng);
      else onAddPoint(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

/**
 * OSM/Leaflet map for polygon draw (land) or pin select (home location).
 * Tiles: OpenStreetMap (zero-cost, replaceable provider per directive §7 —
 * swap the TileLayer URL to change provider).
 */
export default function FarmMap({
  points,
  onAddPoint,
  pin,
  onPin,
  center,
  zoom = 15,
}: FarmMapProps) {
  const initialCenter = useMemo<[number, number]>(() => {
    if (center) return center;
    if (points.length > 0) return [points[0].lat, points[0].lon];
    if (pin) return [pin.lat, pin.lon];
    return [20.5937, 78.9629]; // India centroid as neutral default
  }, [center, points, pin]);

  const latlngs = points.map((p) => new LatLng(p.lat, p.lon));

  return (
    <MapContainer
      center={initialCenter}
      zoom={zoom}
      style={{ height: '320px', width: '100%' }}
      className="rounded-xl z-0"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ClickHandler onAddPoint={onAddPoint} onPin={onPin} />
      {latlngs.length >= 2 && (
        <Polygon positions={latlngs} pathOptions={{ color: '#2e7d32' }} />
      )}
      {latlngs.map((ll, i) => (
        <CircleMarker
          key={i}
          center={ll}
          radius={5}
          pathOptions={{ color: '#1b5e20', fillColor: '#4caf50', fillOpacity: 1 }}
        />
      ))}
      {pin && <CircleMarker center={[pin.lat, pin.lon]} radius={8} pathOptions={{ color: '#1565c0' }} />}
    </MapContainer>
  );
}
