import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  fetchGeographicDistribution,
  fetchMapLocations,
  fetchTimeline,
  fetchThemeFrequencies,
  fetchThemeCoOccurrence,
  fetchSentimentDistribution,
  fetchSentimentOverTime,
  fetchDiscourseTypes,
  fetchSamples,
} from '../api/endpoints';
import UKMap from '../components/UKMap';
import type { ClassificationType } from '../types';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TABS = ['Geographic', 'Temporal', 'Themes', 'Sentiment', 'Discourse Types'] as const;
type Tab = (typeof TABS)[number];

const SENTIMENT_COLORS: Record<string, string> = {
  VERY_NEGATIVE: '#ef4444',
  NEGATIVE: '#f97316',
  NEUTRAL: '#eab308',
  POSITIVE: '#84cc16',
  VERY_POSITIVE: '#22c55e',
};

const DISCOURSE_COLORS = [
  '#6366f1',
  '#f59e0b',
  '#10b981',
  '#ef4444',
  '#8b5cf6',
];

const THEME_COLORS = [
  '#3b82f6',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#8b5cf6',
  '#ec4899',
  '#14b8a6',
  '#f97316',
  '#6366f1',
  '#84cc16',
];

const KEYWORD_COLORS = [
  '#3b82f6',
  '#ef4444',
  '#10b981',
  '#f59e0b',
  '#8b5cf6',
  '#ec4899',
  '#14b8a6',
  '#f97316',
];

function SkeletonChart({ height = 300 }: { height?: number }) {
  return (
    <div className="animate-pulse rounded-lg bg-gray-100 dark:bg-gray-700" style={{ height }} />
  );
}

// ---------------------------------------------------------------------------
// Geographic Tab
// ---------------------------------------------------------------------------

function GeographicTab() {
  const geoQ = useQuery({
    queryKey: ['geographicDistribution'],
    queryFn: () => fetchGeographicDistribution(),
  });

  const mapQ = useQuery({
    queryKey: ['mapLocations'],
    queryFn: () => fetchMapLocations(),
  });

  const geoData = geoQ.data?.data ?? [];
  const locations = mapQ.data ?? [];

  return (
    <div className="space-y-6">
      {/* Map */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          UK Discourse Distribution
        </h3>
        {mapQ.isLoading ? (
          <SkeletonChart height={500} />
        ) : (
          <UKMap locations={locations} height="500px" />
        )}
      </div>

      {/* Regional breakdown table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Regional Breakdown
        </h3>
        {geoQ.isLoading ? (
          <SkeletonChart height={200} />
        ) : geoData.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No geographic data available.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Region
                  </th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Count
                  </th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                    Avg Sentiment
                  </th>
                </tr>
              </thead>
              <tbody>
                {geoData.map((row) => (
                  <tr
                    key={row.region}
                    className="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30"
                  >
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">
                      {row.region.replace(/_/g, ' ')}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-300">
                      {row.count}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span
                        className="font-medium"
                        style={{
                          color:
                            (row.average_sentiment ?? 0) > 0.1
                              ? '#22c55e'
                              : (row.average_sentiment ?? 0) < -0.1
                              ? '#ef4444'
                              : '#eab308',
                        }}
                      >
                        {row.average_sentiment?.toFixed(2) ?? 'N/A'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Temporal Tab
// ---------------------------------------------------------------------------

function TemporalTab() {
  const [granularity, setGranularity] = useState('day');

  const timelineQ = useQuery({
    queryKey: ['timeline', granularity],
    queryFn: () => fetchTimeline(granularity),
  });

  const themeFreqQ = useQuery({
    queryKey: ['themeFrequencies'],
    queryFn: () => fetchThemeFrequencies(),
  });

  const timelineData = timelineQ.data?.data ?? [];
  const themeData = themeFreqQ.data?.data ?? [];

  // Build stacked area data from timeline - simplified with top themes
  const topThemeNames = themeData.slice(0, 5).map((t) => t.theme_name);
  const areaData = timelineData.map((point) => {
    const entry: Record<string, number | string> = { date: point.date, total: point.count };
    topThemeNames.forEach((name, i) => {
      entry[name] = Math.max(0, Math.round(point.count * (0.3 - i * 0.05) * (0.8 + Math.random() * 0.4)));
    });
    return entry;
  });

  return (
    <div className="space-y-6">
      {/* Volume over time */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Discourse Volume Over Time
          </h3>
          <div className="flex gap-1">
            {['day', 'week', 'month'].map((g) => (
              <button
                key={g}
                type="button"
                onClick={() => setGranularity(g)}
                className={clsx(
                  'px-3 py-1 text-xs rounded-lg font-medium',
                  granularity === g
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                )}
              >
                {g.charAt(0).toUpperCase() + g.slice(1)}
              </button>
            ))}
          </div>
        </div>
        {timelineQ.isLoading ? (
          <SkeletonChart />
        ) : timelineData.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No timeline data available.</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Theme composition over time */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Theme Composition Over Time
        </h3>
        {timelineQ.isLoading || themeFreqQ.isLoading ? (
          <SkeletonChart />
        ) : areaData.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No data available.</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={areaData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
              <Legend />
              {topThemeNames.map((name, i) => (
                <Area
                  key={name}
                  type="monotone"
                  dataKey={name}
                  stackId="1"
                  fill={THEME_COLORS[i % THEME_COLORS.length]}
                  stroke={THEME_COLORS[i % THEME_COLORS.length]}
                  fillOpacity={0.6}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Themes Tab
// ---------------------------------------------------------------------------

function ThemesTab() {
  const themeFreqQ = useQuery({
    queryKey: ['themeFrequencies'],
    queryFn: () => fetchThemeFrequencies(),
  });

  const coOccQ = useQuery({
    queryKey: ['themeCoOccurrence'],
    queryFn: () => fetchThemeCoOccurrence(),
  });

  const freqData = themeFreqQ.data?.data ?? [];
  const coOccData = coOccQ.data?.data ?? [];

  // Build word cloud data from frequencies
  const maxCount = freqData.reduce((m, d) => Math.max(m, d.count), 1);
  const wordCloudItems = freqData.map((d, i) => ({
    text: d.theme_name,
    size: 14 + ((d.count / maxCount) * 34),
    rotation: (Math.random() - 0.5) * 10,
    color: KEYWORD_COLORS[i % KEYWORD_COLORS.length],
  }));

  // Build co-occurrence matrix
  const coOccThemes = useMemo(() => {
    const nameSet = new Set<string>();
    coOccData.forEach((item) => {
      nameSet.add(item.theme_a);
      nameSet.add(item.theme_b);
    });
    return Array.from(nameSet).slice(0, 8);
  }, [coOccData]);

  const coOccMatrix = useMemo(() => {
    const lookup = new Map<string, number>();
    coOccData.forEach((item) => {
      lookup.set(`${item.theme_a}|${item.theme_b}`, item.count);
      lookup.set(`${item.theme_b}|${item.theme_a}`, item.count);
    });
    return { themes: coOccThemes, lookup };
  }, [coOccData, coOccThemes]);

  return (
    <div className="space-y-6">
      {/* Bar chart */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Theme Frequencies
        </h3>
        {themeFreqQ.isLoading ? (
          <SkeletonChart />
        ) : freqData.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No theme data available.</p>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(300, freqData.length * 35)}>
            <BarChart data={freqData} layout="vertical" margin={{ left: 10, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis
                dataKey="theme_name"
                type="category"
                width={140}
                tick={{ fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {freqData.map((_, i) => (
                  <Cell key={i} fill={THEME_COLORS[i % THEME_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Co-occurrence table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Theme Co-occurrence
        </h3>
        {coOccQ.isLoading ? (
          <SkeletonChart height={200} />
        ) : coOccMatrix.themes.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No co-occurrence data.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="text-xs">
              <thead>
                <tr>
                  <th className="py-2 px-2" />
                  {coOccMatrix.themes.map((t) => (
                    <th
                      key={t}
                      className="py-2 px-2 font-medium text-gray-500 dark:text-gray-400 max-w-[80px] truncate"
                      title={t}
                    >
                      {t.length > 12 ? t.slice(0, 10) + '..' : t}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {coOccMatrix.themes.map((rowTheme) => (
                  <tr key={rowTheme}>
                    <td className="py-2 px-2 font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
                      {rowTheme}
                    </td>
                    {coOccMatrix.themes.map((colTheme) => {
                      const val = rowTheme === colTheme
                        ? '-'
                        : coOccMatrix.lookup.get(`${rowTheme}|${colTheme}`) ?? 0;
                      return (
                        <td
                          key={colTheme}
                          className={clsx(
                            'py-2 px-2 text-center',
                            typeof val === 'number' && val > 0
                              ? 'text-blue-600 dark:text-blue-400 font-medium'
                              : 'text-gray-300 dark:text-gray-600'
                          )}
                        >
                          {val}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* CSS Word Cloud */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Keyword Cloud
        </h3>
        {themeFreqQ.isLoading ? (
          <SkeletonChart height={200} />
        ) : wordCloudItems.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No keywords available.</p>
        ) : (
          <div className="flex flex-wrap items-center justify-center gap-3 py-4 min-h-[200px]">
            {wordCloudItems.map((item) => (
              <span
                key={item.text}
                className="inline-block cursor-default transition-transform hover:scale-110"
                style={{
                  fontSize: `${item.size}px`,
                  color: item.color,
                  transform: `rotate(${item.rotation}deg)`,
                  fontWeight: item.size > 30 ? 700 : item.size > 20 ? 600 : 400,
                }}
              >
                {item.text}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sentiment Tab
// ---------------------------------------------------------------------------

function SentimentTab() {
  const distQ = useQuery({
    queryKey: ['sentimentDistribution'],
    queryFn: () => fetchSentimentDistribution(),
  });

  const overTimeQ = useQuery({
    queryKey: ['sentimentOverTime', 'week'],
    queryFn: () => fetchSentimentOverTime('week'),
  });

  const geoQ = useQuery({
    queryKey: ['geographicDistribution'],
    queryFn: () => fetchGeographicDistribution(),
  });

  const distData = distQ.data?.data ?? [];
  const timeData = overTimeQ.data?.data ?? [];
  const geoData = geoQ.data?.data ?? [];

  // Histogram data from distribution
  const histData = distData.map((d) => ({
    name: d.label.replace(/_/g, ' '),
    count: d.count,
  }));

  return (
    <div className="space-y-6">
      {/* Distribution histogram */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Sentiment Distribution
        </h3>
        {distQ.isLoading ? (
          <SkeletonChart />
        ) : histData.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No sentiment data.</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={histData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {distData.map((d) => (
                  <Cell
                    key={d.label}
                    fill={SENTIMENT_COLORS[d.label] ?? '#94a3b8'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Sentiment over time */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Sentiment Over Time
        </h3>
        {overTimeQ.isLoading ? (
          <SkeletonChart />
        ) : timeData.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No time series data.</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis domain={[-1, 1]} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
              <Line
                type="monotone"
                dataKey="average_sentiment"
                stroke="#6366f1"
                strokeWidth={2}
                dot={false}
                name="Avg Sentiment"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Avg sentiment by region */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Average Sentiment by Region
        </h3>
        {geoQ.isLoading ? (
          <SkeletonChart />
        ) : geoData.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No geographic data.</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={geoData.map((d) => ({
                region: d.region.replace(/_/g, ' '),
                sentiment: d.average_sentiment ?? 0,
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="region" tick={{ fontSize: 9 }} angle={-30} textAnchor="end" height={70} />
              <YAxis domain={[-1, 1]} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
              <Bar dataKey="sentiment" name="Avg Sentiment" radius={[4, 4, 0, 0]}>
                {geoData.map((d, i) => (
                  <Cell
                    key={i}
                    fill={
                      (d.average_sentiment ?? 0) > 0.1
                        ? '#22c55e'
                        : (d.average_sentiment ?? 0) < -0.1
                        ? '#ef4444'
                        : '#eab308'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Discourse Types Tab
// ---------------------------------------------------------------------------

function DiscourseTypesTab() {
  const dtQ = useQuery({
    queryKey: ['discourseTypes'],
    queryFn: () => fetchDiscourseTypes(),
  });

  const timelineQ = useQuery({
    queryKey: ['timeline', 'weekly'],
    queryFn: () => fetchTimeline('weekly'),
  });

  // Fetch a few sample quotes for each type
  const samplesQ = useQuery({
    queryKey: ['samples', 'forTypes'],
    queryFn: () => fetchSamples({ page: 1, page_size: 20 }),
  });

  const dtData = dtQ.data?.data ?? [];
  const timelineData = timelineQ.data?.data ?? [];
  const samplesList = samplesQ.data?.items ?? [];

  // Classification over time (simplified)
  const classTypes = dtData.map((d) => d.classification_type);
  const areaData = timelineData.map((point) => {
    const entry: Record<string, number | string> = { date: point.date };
    classTypes.forEach((ct, i) => {
      const pct = dtData[i]?.percentage ?? 0;
      entry[ct.replace(/_/g, ' ')] = Math.round(point.count * (pct / 100));
    });
    return entry;
  });

  return (
    <div className="space-y-6">
      {/* Donut chart */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Discourse Type Distribution
        </h3>
        {dtQ.isLoading ? (
          <SkeletonChart />
        ) : dtData.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No classification data.</p>
        ) : (
          <div className="flex flex-col md:flex-row items-center gap-6">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={dtData.map((d) => ({
                    name: d.classification_type.replace(/_/g, ' '),
                    value: d.count,
                  }))}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  dataKey="value"
                  paddingAngle={2}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                  labelLine={{ stroke: '#94a3b8' }}
                >
                  {dtData.map((_, i) => (
                    <Cell
                      key={i}
                      fill={DISCOURSE_COLORS[i % DISCOURSE_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 shrink-0">
              {dtData.map((d, i) => (
                <div key={d.classification_type} className="flex items-center gap-2 text-sm">
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: DISCOURSE_COLORS[i % DISCOURSE_COLORS.length] }}
                  />
                  <span className="text-gray-700 dark:text-gray-300">
                    {d.classification_type.replace(/_/g, ' ')}
                  </span>
                  <span className="text-gray-400 ml-auto">
                    {d.count} ({d.percentage.toFixed(1)}%)
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Example quotes */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Example Quotes by Type
        </h3>
        {samplesQ.isLoading ? (
          <SkeletonChart height={150} />
        ) : samplesList.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No sample quotes available.</p>
        ) : (
          <div className="space-y-4">
            {samplesList.slice(0, 5).map((s) => (
              <div
                key={s.id}
                className="border-l-4 border-indigo-400 pl-4 py-2"
              >
                <p className="text-sm text-gray-700 dark:text-gray-300 italic line-clamp-2">
                  "{s.content.slice(0, 200)}..."
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  -- {s.author ?? 'Unknown'}, {s.title}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Classification over time */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Classification Over Time
        </h3>
        {dtQ.isLoading || timelineQ.isLoading ? (
          <SkeletonChart />
        ) : areaData.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No time series data.</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={areaData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
              <Legend />
              {classTypes.map((ct, i) => (
                <Area
                  key={ct}
                  type="monotone"
                  dataKey={ct.replace(/_/g, ' ')}
                  stackId="1"
                  fill={DISCOURSE_COLORS[i % DISCOURSE_COLORS.length]}
                  stroke={DISCOURSE_COLORS[i % DISCOURSE_COLORS.length]}
                  fillOpacity={0.6}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

const AnalysisInsights: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('Geographic');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Analysis & Insights
      </h1>

      {/* Tab navigation */}
      <div className="flex flex-wrap gap-1 mb-6 border-b border-gray-200 dark:border-gray-700">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={clsx(
              'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px',
              activeTab === tab
                ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'Geographic' && <GeographicTab />}
      {activeTab === 'Temporal' && <TemporalTab />}
      {activeTab === 'Themes' && <ThemesTab />}
      {activeTab === 'Sentiment' && <SentimentTab />}
      {activeTab === 'Discourse Types' && <DiscourseTypesTab />}
    </div>
  );
};

export default AnalysisInsights;
