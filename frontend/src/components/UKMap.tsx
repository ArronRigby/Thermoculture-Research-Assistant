import React from 'react';
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { MapLocation } from '../types';

interface UKMapProps {
  locations: MapLocation[];
  height?: string;
  center?: [number, number];
  zoom?: number;
}

function sentimentToColor(avg: number): string {
  if (avg <= -0.4) return '#ef4444';
  if (avg <= -0.1) return '#f97316';
  if (avg <= 0.1) return '#eab308';
  if (avg <= 0.4) return '#84cc16';
  return '#22c55e';
}

function countToRadius(count: number, maxCount: number): number {
  if (maxCount === 0) return 5;
  const ratio = count / maxCount;
  return Math.max(5, Math.min(30, 5 + ratio * 25));
}

const UKMap: React.FC<UKMapProps> = ({
  locations,
  height = '500px',
  center = [54.5, -3.5],
  zoom = 6,
}) => {
  const maxCount = locations.reduce(
    (max, loc) => Math.max(max, loc.count),
    0
  );

  return (
    <div style={{ height, width: '100%' }} className="rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {locations.map((loc) => {
          const color = sentimentToColor(loc.avgSentiment);
          const radius = countToRadius(loc.count, maxCount);
          return (
            <CircleMarker
              key={`${loc.name}-${loc.lat}-${loc.lng}`}
              center={[loc.lat, loc.lng]}
              radius={radius}
              pathOptions={{
                color,
                fillColor: color,
                fillOpacity: 0.6,
                weight: 2,
              }}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-semibold text-gray-900">{loc.name}</p>
                  <p className="text-gray-600">
                    Samples: <span className="font-medium">{loc.count}</span>
                  </p>
                  <p className="text-gray-600">
                    Avg Sentiment:{' '}
                    <span
                      className="font-medium"
                      style={{ color }}
                    >
                      {loc.avgSentiment.toFixed(2)}
                    </span>
                  </p>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default UKMap;
