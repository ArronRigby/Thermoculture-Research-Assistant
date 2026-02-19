import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  fetchTrendingThemes,
  fetchSentimentOverTime,
  fetchThemeFrequencies,
  fetchDiscourseTypes,
  fetchCollectionStats,
  fetchSamples,
} from '../api/endpoints';
import LoadingSpinner from '../components/LoadingSpinner';

// ---------------------------------------------------------------------------
// Provenance bar
// ---------------------------------------------------------------------------

function ProvenanceBar({ thisMonth }: { thisMonth: number }) {
  return (
    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
      {thisMonth.toLocaleString()} articles collected this month
    </p>
  );
}

// ---------------------------------------------------------------------------
// Trend direction badge
// ---------------------------------------------------------------------------

function TrendBadge({ direction }: { direction: 'up' | 'down' | 'stable' }) {
  if (direction === 'up') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/40 dark:text-green-300">
        ↑ rising
      </span>
    );
  }
  if (direction === 'down') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/40 dark:text-red-300">
        ↓ falling
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300">
      → stable
    </span>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function TrendsPage() {
  const queryClient = useQueryClient();

  const trendingQ = useQuery({
    queryKey: ['trending-themes'],
    queryFn: fetchTrendingThemes,
  });
  const sentimentQ = useQuery({
    queryKey: ['sentiment-over-time'],
    queryFn: () => fetchSentimentOverTime('week'),
  });
  const themeFreqQ = useQuery({
    queryKey: ['theme-frequencies'],
    queryFn: fetchThemeFrequencies,
  });
  const discourseQ = useQuery({
    queryKey: ['discourse-types'],
    queryFn: fetchDiscourseTypes,
  });
  const statsQ = useQuery({
    queryKey: ['collection-stats'],
    queryFn: fetchCollectionStats,
  });
  const recentQ = useQuery({
    queryKey: ['recent-samples'],
    queryFn: () => fetchSamples({ page: 1, page_size: 20, sort_by: 'collected_at', sort_order: 'desc' }),
  });

  const isLoading = trendingQ.isLoading || sentimentQ.isLoading || themeFreqQ.isLoading;

  function handleRefresh() {
    queryClient.invalidateQueries({ queryKey: ['trending-themes'] });
    queryClient.invalidateQueries({ queryKey: ['sentiment-over-time'] });
    queryClient.invalidateQueries({ queryKey: ['theme-frequencies'] });
    queryClient.invalidateQueries({ queryKey: ['discourse-types'] });
    queryClient.invalidateQueries({ queryKey: ['collection-stats'] });
    queryClient.invalidateQueries({ queryKey: ['recent-samples'] });
  }

  const topTrend = trendingQ.data?.data?.[0];
  const thisMonth = statsQ.data?.this_month ?? 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Trends</h1>
        <button
          type="button"
          onClick={handleRefresh}
          className="flex items-center gap-2 rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          ↻ Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : (
        <>
          {/* 1. Headline insight */}
          {topTrend && (
            <div className="rounded-xl bg-primary-600 p-6 text-white">
              <p className="text-sm font-medium opacity-80">Top theme right now</p>
              <div className="mt-1 flex items-center gap-3">
                <p className="text-3xl font-bold">{topTrend.theme_name}</p>
                <TrendBadge direction={topTrend.trend_direction} />
              </div>
              <p className="mt-1 text-sm opacity-70">
                {topTrend.count.toLocaleString()} articles
              </p>
              <ProvenanceBar thisMonth={thisMonth} />
            </div>
          )}

          {/* 2. Trending themes bar chart */}
          <section className="rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
              Trending Themes
            </h2>
            <ProvenanceBar thisMonth={thisMonth} />
            <div className="mt-4 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={trendingQ.data?.data?.slice(0, 10) ?? []}
                  layout="vertical"
                  margin={{ left: 100 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis
                    type="category"
                    dataKey="theme_name"
                    tick={{ fontSize: 11 }}
                    width={100}
                  />
                  <Tooltip />
                  <Bar
                    dataKey="count"
                    name="Articles"
                    fill="#4f46e5"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* 3. Sentiment over time */}
          <section className="rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
              Sentiment Over Time
            </h2>
            <ProvenanceBar thisMonth={thisMonth} />
            <div className="mt-4 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sentimentQ.data?.data ?? []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis domain={[-1, 1]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="average_sentiment"
                    name="Avg. sentiment"
                    stroke="#4f46e5"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* 4. Theme frequency */}
          {themeFreqQ.data?.data && themeFreqQ.data.data.length > 0 && (
            <section className="rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                Theme Frequency
              </h2>
              <ProvenanceBar thisMonth={thisMonth} />
              <div className="mt-4 h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={themeFreqQ.data.data.slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="theme_name" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" name="Articles" fill="#7c3aed" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
          )}

          {/* 5. Discourse type breakdown */}
          {discourseQ.data?.data && discourseQ.data.data.length > 0 && (
            <section className="rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                Discourse Types
              </h2>
              <ProvenanceBar thisMonth={thisMonth} />
              <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {discourseQ.data.data.map((item) => (
                  <div
                    key={item.classification_type}
                    className="rounded-lg bg-gray-50 dark:bg-gray-700 p-4 text-center"
                  >
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {item.count}
                    </p>
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 leading-tight">
                      {item.classification_type.replace(/_/g, ' ')}
                    </p>
                    <p className="mt-0.5 text-[10px] text-gray-400">
                      {item.percentage.toFixed(1)}%
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* 6. Collection activity */}
          {statsQ.data && (
            <section className="rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Collection Activity
              </h2>
              <div className="grid grid-cols-3 gap-4">
                <div className="rounded-lg bg-blue-50 dark:bg-blue-900/20 p-4 text-center">
                  <p className="text-3xl font-bold text-blue-700 dark:text-blue-300">
                    {statsQ.data.today.toLocaleString()}
                  </p>
                  <p className="mt-1 text-xs text-blue-500 dark:text-blue-400">Today</p>
                </div>
                <div className="rounded-lg bg-indigo-50 dark:bg-indigo-900/20 p-4 text-center">
                  <p className="text-3xl font-bold text-indigo-700 dark:text-indigo-300">
                    {statsQ.data.this_week.toLocaleString()}
                  </p>
                  <p className="mt-1 text-xs text-indigo-500 dark:text-indigo-400">This week</p>
                </div>
                <div className="rounded-lg bg-violet-50 dark:bg-violet-900/20 p-4 text-center">
                  <p className="text-3xl font-bold text-violet-700 dark:text-violet-300">
                    {statsQ.data.this_month.toLocaleString()}
                  </p>
                  <p className="mt-1 text-xs text-violet-500 dark:text-violet-400">This month</p>
                </div>
              </div>
            </section>
          )}

          {/* 7. Recent articles feed */}
          <section className="rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Recently Collected
            </h2>
            {!recentQ.data?.items?.length ? (
              <p className="text-sm text-gray-400">No articles collected yet.</p>
            ) : (
              <ul className="divide-y divide-gray-100 dark:divide-gray-700">
                {recentQ.data.items.map((sample) => (
                  <li key={sample.id} className="py-3">
                    <p className="text-sm font-medium text-gray-900 dark:text-white line-clamp-1">
                      {sample.title}
                    </p>
                    <p className="mt-0.5 text-xs text-gray-400">
                      {sample.author ? `${sample.author} · ` : ''}
                      {new Date(sample.collected_at).toLocaleDateString()}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
