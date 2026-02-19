import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  fetchDashboardStats,
  fetchSamples,
  fetchSentimentDistribution,
  fetchTrendingThemes,
  fetchCollectionJobs,
} from '../api/endpoints';
import type {
  DiscourseSampleResponse,
  JobStatus,
} from '../types';

// ---------------------------------------------------------------------------
// Skeleton helpers
// ---------------------------------------------------------------------------

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-xl bg-white dark:bg-gray-800 p-5 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded mb-3" />
      <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded mb-2" />
      <div className="h-3 w-24 bg-gray-200 dark:bg-gray-700 rounded" />
    </div>
  );
}

function SkeletonRow() {
  return (
    <div className="animate-pulse flex gap-3 py-3">
      <div className="h-4 flex-1 bg-gray-200 dark:bg-gray-700 rounded" />
      <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const SENTIMENT_COLORS: Record<string, string> = {
  VERY_NEGATIVE: '#ef4444',
  NEGATIVE: '#f97316',
  NEUTRAL: '#eab308',
  POSITIVE: '#84cc16',
  VERY_POSITIVE: '#22c55e',
};

function statusBadge(status: JobStatus) {
  const map: Record<string, string> = {
    PENDING: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    RUNNING: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    COMPLETED: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    FAILED: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${map[status] ?? 'bg-gray-100 text-gray-800'}`}
    >
      {status.replace('_', ' ')}
    </span>
  );
}

function SampleCard({ sample }: { sample: DiscourseSampleResponse }) {
  return (
    <Link
      to={`/browse/${sample.id}`}
      className="block rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 hover:shadow-md transition-shadow"
    >
      <h4 className="font-semibold text-gray-900 dark:text-gray-100 line-clamp-1 mb-1">
        {sample.title}
      </h4>
      <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mb-2">
        {sample.content}
      </p>
      <div className="flex items-center justify-between text-xs text-gray-400 dark:text-gray-500">
        <span>{sample.author ?? 'Unknown author'}</span>
        <span>{new Date(sample.collected_at).toLocaleDateString()}</span>
      </div>
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Stats card configs
// ---------------------------------------------------------------------------

interface StatConfig {
  key: string;
  label: string;
  color: string;
  bgColor: string;
  icon: React.ReactNode;
}

const statConfigs: StatConfig[] = [
  {
    key: 'total_samples',
    label: 'Total Samples',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 dark:bg-blue-900/30',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
  },
  {
    key: 'active_sources',
    label: 'Active Sources',
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50 dark:bg-emerald-900/30',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    key: 'themes_identified',
    label: 'Themes Identified',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 dark:bg-purple-900/30',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
      </svg>
    ),
  },
  {
    key: 'running_jobs',
    label: 'Jobs Running',
    color: 'text-amber-600',
    bgColor: 'bg-amber-50 dark:bg-amber-900/30',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
  },
];

// ---------------------------------------------------------------------------
// Dashboard Page
// ---------------------------------------------------------------------------

const Dashboard: React.FC = () => {
  const statsQ = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: fetchDashboardStats,
  });

  const samplesQ = useQuery({
    queryKey: ['recentSamples'],
    queryFn: () => fetchSamples({ page: 1, page_size: 5, sort_by: 'collected_at', sort_order: 'desc' }),
  });

  const sentimentQ = useQuery({
    queryKey: ['sentimentDistribution'],
    queryFn: () => fetchSentimentDistribution(),
  });

  const trendingQ = useQuery({
    queryKey: ['trendingThemes'],
    queryFn: fetchTrendingThemes,
  });

  const jobsQ = useQuery({
    queryKey: ['recentJobs'],
    queryFn: fetchCollectionJobs,
  });

  const stats = statsQ.data;
  const recentSamples = samplesQ.data?.items ?? [];
  const sentimentData = sentimentQ.data?.data ?? [];
  const trendingData = (trendingQ.data?.data ?? []).slice(0, 5);
  const recentJobs = (jobsQ.data ?? []).slice(0, 3);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Thermoculture Research Assistant
        </h1>
        <p className="mt-2 text-gray-500 dark:text-gray-400 max-w-2xl">
          Monitor, collect, and analyse UK public discourse on climate change and thermal culture.
          Explore sentiment trends, geographic patterns, and emerging themes across diverse sources.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statsQ.isLoading
          ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
          : statConfigs.map((cfg) => {
              const value = stats
                ? (stats as unknown as Record<string, number>)[cfg.key] ?? 0
                : 0;
              return (
                <div
                  key={cfg.key}
                  className={`rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 ${cfg.bgColor}`}
                >
                  <div className={`mb-3 ${cfg.color}`}>{cfg.icon}</div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {value.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {cfg.label}
                  </p>
                </div>
              );
            })}
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Samples - spans 2 cols */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Recent Samples
              </h2>
              <Link
                to="/browse"
                className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                View all
              </Link>
            </div>
            {samplesQ.isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <SkeletonRow key={i} />
                ))}
              </div>
            ) : recentSamples.length === 0 ? (
              <p className="text-gray-400 text-sm py-8 text-center">
                No discourse samples collected yet.
              </p>
            ) : (
              <div className="space-y-3">
                {recentSamples.map((s) => (
                  <SampleCard key={s.id} sample={s} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Insights sidebar */}
        <div className="space-y-6">
          {/* Sentiment Distribution Pie */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
              Sentiment Distribution
            </h3>
            {sentimentQ.isLoading ? (
              <div className="animate-pulse flex justify-center py-8">
                <div className="w-32 h-32 rounded-full bg-gray-200 dark:bg-gray-700" />
              </div>
            ) : sentimentData.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-8">No data yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={sentimentData.map((d) => ({
                      name: d.label.replace(/_/g, ' '),
                      value: d.count,
                    }))}
                    cx="50%"
                    cy="50%"
                    innerRadius={35}
                    outerRadius={70}
                    dataKey="value"
                    paddingAngle={2}
                  >
                    {sentimentData.map((d) => (
                      <Cell
                        key={d.label}
                        fill={SENTIMENT_COLORS[d.label] ?? '#94a3b8'}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      borderRadius: '8px',
                      fontSize: '12px',
                      border: '1px solid #e5e7eb',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
            <div className="flex flex-wrap gap-2 mt-2">
              {sentimentData.map((d) => (
                <span
                  key={d.label}
                  className="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400"
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full inline-block"
                    style={{
                      backgroundColor: SENTIMENT_COLORS[d.label] ?? '#94a3b8',
                    }}
                  />
                  {d.label.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>

          {/* Trending Themes Bar */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
              Trending Themes
            </h3>
            {trendingQ.isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className="animate-pulse h-5 bg-gray-200 dark:bg-gray-700 rounded"
                    style={{ width: `${100 - i * 15}%` }}
                  />
                ))}
              </div>
            ) : trendingData.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-8">No themes yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart
                  data={trendingData}
                  layout="vertical"
                  margin={{ left: 0, right: 10, top: 0, bottom: 0 }}
                >
                  <XAxis type="number" hide />
                  <YAxis
                    dataKey="theme_name"
                    type="category"
                    width={100}
                    tick={{ fontSize: 11, fill: '#6b7280' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: '8px',
                      fontSize: '12px',
                      border: '1px solid #e5e7eb',
                    }}
                  />
                  <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Recent Collection Activity */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                Collection Activity
              </h3>
              <Link
                to="/collection"
                className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                View all
              </Link>
            </div>
            {jobsQ.isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <SkeletonRow key={i} />
                ))}
              </div>
            ) : recentJobs.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-4">
                No collection jobs yet
              </p>
            ) : (
              <div className="space-y-3">
                {recentJobs.map((job) => (
                  <div
                    key={job.id}
                    className="flex items-center justify-between text-sm"
                  >
                    <div>
                      <span className="text-gray-700 dark:text-gray-300 font-medium">
                        Source {job.source_id.slice(0, 8)}...
                      </span>
                      <div className="text-xs text-gray-400 mt-0.5">
                        {job.started_at
                          ? new Date(job.started_at).toLocaleString()
                          : 'Pending'}
                      </div>
                    </div>
                    {statusBadge(job.status)}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
