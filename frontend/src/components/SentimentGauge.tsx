import React from 'react';
import clsx from 'clsx';

interface SentimentGaugeProps {
  value: number; // -1 to 1
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

function sentimentColor(v: number): string {
  if (v <= -0.6) return '#ef4444'; // red-500
  if (v <= -0.2) return '#f97316'; // orange-500
  if (v <= 0.2) return '#eab308'; // yellow-500
  if (v <= 0.6) return '#84cc16'; // lime-500
  return '#22c55e'; // green-500
}

function sentimentLabel(v: number): string {
  if (v <= -0.6) return 'Very Negative';
  if (v <= -0.2) return 'Negative';
  if (v <= 0.2) return 'Neutral';
  if (v <= 0.6) return 'Positive';
  return 'Very Positive';
}

const SentimentGauge: React.FC<SentimentGaugeProps> = ({
  value,
  label,
  size = 'md',
}) => {
  const clamped = Math.max(-1, Math.min(1, value));
  const pct = ((clamped + 1) / 2) * 100; // 0-100
  const color = sentimentColor(clamped);

  const barHeight = size === 'sm' ? 'h-3' : size === 'lg' ? 'h-6' : 'h-4';
  const markerSize =
    size === 'sm' ? 'w-3 h-5' : size === 'lg' ? 'w-5 h-8' : 'w-4 h-6';
  const textSize =
    size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-base' : 'text-sm';

  return (
    <div className="w-full">
      {label && (
        <div
          className={clsx(
            'mb-1 font-medium text-gray-700 dark:text-gray-300',
            textSize
          )}
        >
          {label}
        </div>
      )}

      {/* Gauge track */}
      <div className="relative">
        <div
          className={clsx(
            'w-full rounded-full overflow-hidden',
            barHeight
          )}
          style={{
            background:
              'linear-gradient(to right, #ef4444, #f97316, #eab308, #84cc16, #22c55e)',
          }}
        />

        {/* Marker */}
        <div
          className={clsx(
            'absolute top-1/2 -translate-y-1/2 -translate-x-1/2 rounded-sm border-2 border-white shadow-md',
            markerSize
          )}
          style={{
            left: `${pct}%`,
            backgroundColor: color,
          }}
        />
      </div>

      {/* Labels */}
      <div className="flex items-center justify-between mt-1.5">
        <span className={clsx('text-gray-400', textSize === 'text-xs' ? 'text-[10px]' : 'text-xs')}>
          -1.0
        </span>
        <div className="flex items-center gap-1.5">
          <span
            className={clsx('font-semibold', textSize)}
            style={{ color }}
          >
            {clamped.toFixed(2)}
          </span>
          <span
            className={clsx('text-gray-500', textSize === 'text-xs' ? 'text-[10px]' : 'text-xs')}
          >
            {sentimentLabel(clamped)}
          </span>
        </div>
        <span className={clsx('text-gray-400', textSize === 'text-xs' ? 'text-[10px]' : 'text-xs')}>
          +1.0
        </span>
      </div>
    </div>
  );
};

export default SentimentGauge;
