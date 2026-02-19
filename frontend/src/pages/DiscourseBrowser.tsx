import React, { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { fetchSamples, exportSamples } from '../api/endpoints';
import ExportButton from '../components/ExportButton';
import TagPills from '../components/TagPills';
import type {
  FilterParams,
  SourceType,
  ClassificationType,
  DiscourseSampleResponse,
} from '../types';

// ---------------------------------------------------------------------------
// Filter bar
// ---------------------------------------------------------------------------

interface FilterBarProps {
  filters: FilterParams;
  onChange: (f: FilterParams) => void;
}

const SOURCE_TYPES: SourceType[] = ['NEWS', 'REDDIT', 'FORUM', 'SOCIAL_MEDIA', 'MANUAL'] as SourceType[];
const DISCOURSE_TYPES: ClassificationType[] = [
  'PRACTICAL_ADAPTATION',
  'EMOTIONAL_RESPONSE',
  'POLICY_DISCUSSION',
  'COMMUNITY_ACTION',
  'DENIAL_DISMISSAL',
] as ClassificationType[];

function FilterBar({ filters, onChange }: FilterBarProps) {
  const [open, setOpen] = useState(false);

  function set<K extends keyof FilterParams>(key: K, value: FilterParams[K]) {
    onChange({ ...filters, [key]: value, page: 1 });
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 mb-4">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full px-5 py-3 text-sm font-medium text-gray-700 dark:text-gray-300"
      >
        <span className="flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filters
        </span>
        <svg
          className={clsx('w-4 h-4 transition-transform', open && 'rotate-180')}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="px-5 pb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Date From */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Date From
            </label>
            <input
              type="date"
              value={filters.date_from ?? ''}
              onChange={(e) => set('date_from', e.target.value || undefined)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            />
          </div>
          {/* Date To */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Date To
            </label>
            <input
              type="date"
              value={filters.date_to ?? ''}
              onChange={(e) => set('date_to', e.target.value || undefined)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            />
          </div>
          {/* Source Type */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Source Type
            </label>
            <select
              value={filters.source_types?.[0] ?? ''}
              onChange={(e) =>
                set(
                  'source_types',
                  e.target.value ? [e.target.value as SourceType] : undefined
                )
              }
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            >
              <option value="">All</option>
              {SOURCE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>
          {/* Discourse Type */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Discourse Type
            </label>
            <select
              value={filters.discourse_types?.[0] ?? ''}
              onChange={(e) =>
                set(
                  'discourse_types',
                  e.target.value
                    ? [e.target.value as ClassificationType]
                    : undefined
                )
              }
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            >
              <option value="">All</option>
              {DISCOURSE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>
          {/* Sentiment Range */}
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              Sentiment Range ({(filters.sentiment_range?.[0] ?? -1).toFixed(1)} to{' '}
              {(filters.sentiment_range?.[1] ?? 1).toFixed(1)})
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min={-1}
                max={1}
                step={0.1}
                value={filters.sentiment_range?.[0] ?? -1}
                onChange={(e) =>
                  set('sentiment_range', [
                    parseFloat(e.target.value),
                    filters.sentiment_range?.[1] ?? 1,
                  ])
                }
                className="flex-1"
              />
              <input
                type="range"
                min={-1}
                max={1}
                step={0.1}
                value={filters.sentiment_range?.[1] ?? 1}
                onChange={(e) =>
                  set('sentiment_range', [
                    filters.sentiment_range?.[0] ?? -1,
                    parseFloat(e.target.value),
                  ])
                }
                className="flex-1"
              />
            </div>
          </div>
          {/* Clear */}
          <div className="flex items-end">
            <button
              type="button"
              onClick={() =>
                onChange({ page: 1, page_size: 20, sort_by: 'collected_at', sort_order: 'desc' })
              }
              className="text-sm text-red-500 hover:text-red-600"
            >
              Clear Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sample cards
// ---------------------------------------------------------------------------

function SampleCardGrid({ sample }: { sample: DiscourseSampleResponse }) {
  return (
    <Link
      to={`/browse/${sample.id}`}
      className="block bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 hover:shadow-md transition-shadow"
    >
      <h3 className="font-semibold text-gray-900 dark:text-white line-clamp-2 mb-2">
        {sample.title}
      </h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-3 mb-3">
        {sample.content}
      </p>
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>{sample.author ?? 'Unknown'}</span>
        <span>{new Date(sample.collected_at).toLocaleDateString()}</span>
      </div>
    </Link>
  );
}

function SampleCardList({ sample }: { sample: DiscourseSampleResponse }) {
  return (
    <Link
      to={`/browse/${sample.id}`}
      className="flex gap-4 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 hover:shadow-md transition-shadow"
    >
      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-gray-900 dark:text-white line-clamp-1 mb-1">
          {sample.title}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
          {sample.content}
        </p>
      </div>
      <div className="flex flex-col items-end justify-between text-xs text-gray-400 shrink-0">
        <span>{sample.author ?? 'Unknown'}</span>
        <span>{new Date(sample.collected_at).toLocaleDateString()}</span>
      </div>
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const DiscourseBrowser: React.FC = () => {
  const [filters, setFilters] = useState<FilterParams>({
    page: 1,
    page_size: 20,
    sort_by: 'collected_at',
    sort_order: 'desc',
  });
  const [searchInput, setSearchInput] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const queryKey = useMemo(() => ['samples', filters], [filters]);

  const { data, isLoading, isError } = useQuery({
    queryKey,
    queryFn: () => fetchSamples(filters),
    placeholderData: (prev) => prev,
  });

  const handleSearch = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      setFilters((f) => ({ ...f, search_query: searchInput || undefined, page: 1 }));
    },
    [searchInput]
  );

  const handleTagToggle = useCallback((id: string) => {
    setFilters((f) => {
      const current = f.theme_ids ?? [];
      const next = current.includes(id)
        ? current.filter((t) => t !== id)
        : [...current, id];
      return { ...f, theme_ids: next.length ? next : undefined, page: 1 };
    });
  }, []);

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;
  const currentPage = filters.page ?? 1;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Search bar */}
      <form onSubmit={handleSearch} className="mb-4">
        <div className="relative">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search discourse samples..."
            className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 pl-12 pr-4 py-3 text-sm text-gray-700 dark:text-gray-200 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <svg
            className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </form>

      {/* Tag Pills */}
      <TagPills activeIds={filters.theme_ids ?? []} onToggle={handleTagToggle} />

      {/* Filters */}
      <FilterBar filters={filters} onChange={setFilters} />

      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {isLoading ? 'Loading...' : `${total.toLocaleString()} results`}
        </p>
        <div className="flex items-center gap-3">
          {/* Sort */}
          <select
            value={`${filters.sort_by ?? 'collected_at'}:${filters.sort_order ?? 'desc'}`}
            onChange={(e) => {
              const [sort_by, sort_order] = e.target.value.split(':') as [
                string,
                'asc' | 'desc',
              ];
              setFilters((f) => ({ ...f, sort_by, sort_order }));
            }}
            className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
          >
            <option value="collected_at:desc">Newest First</option>
            <option value="collected_at:asc">Oldest First</option>
            <option value="sentiment:desc">Sentiment (High)</option>
            <option value="sentiment:asc">Sentiment (Low)</option>
            <option value="relevance:desc">Relevance</option>
          </select>

          {/* View toggle */}
          <div className="flex rounded-lg border border-gray-300 dark:border-gray-600 overflow-hidden">
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={clsx(
                'px-3 py-2 text-sm',
                viewMode === 'grid'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300'
              )}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={clsx(
                'px-3 py-2 text-sm',
                viewMode === 'list'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300'
              )}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>

          {/* Export */}
          <ExportButton onExport={exportSamples} filters={filters} />
        </div>
      </div>

      {/* Results */}
      {isError ? (
        <div className="text-center py-16">
          <p className="text-red-500">Failed to load samples. Please try again.</p>
        </div>
      ) : isLoading ? (
        <div
          className={clsx(
            viewMode === 'grid'
              ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4'
              : 'space-y-3'
          )}
        >
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="animate-pulse bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-5"
            >
              <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-700 rounded mb-3" />
              <div className="h-3 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2" />
              <div className="h-3 w-2/3 bg-gray-200 dark:bg-gray-700 rounded" />
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-20">
          <svg
            className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-500 dark:text-gray-400 mb-1">
            No samples found
          </h3>
          <p className="text-sm text-gray-400 dark:text-gray-500">
            Try adjusting your filters or search query.
          </p>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((s) => (
            <SampleCardGrid key={s.id} sample={s} />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((s) => (
            <SampleCardList key={s.id} sample={s} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <button
            type="button"
            disabled={currentPage <= 1}
            onClick={() => setFilters((f) => ({ ...f, page: currentPage - 1 }))}
            className="px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Previous
          </button>
          {Array.from({ length: Math.min(totalPages, 7) }).map((_, i) => {
            let page: number;
            if (totalPages <= 7) {
              page = i + 1;
            } else if (currentPage <= 4) {
              page = i + 1;
            } else if (currentPage >= totalPages - 3) {
              page = totalPages - 6 + i;
            } else {
              page = currentPage - 3 + i;
            }
            return (
              <button
                key={page}
                type="button"
                onClick={() => setFilters((f) => ({ ...f, page }))}
                className={clsx(
                  'px-3 py-2 text-sm rounded-lg border',
                  page === currentPage
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                )}
              >
                {page}
              </button>
            );
          })}
          <button
            type="button"
            disabled={currentPage >= totalPages}
            onClick={() => setFilters((f) => ({ ...f, page: currentPage + 1 }))}
            className="px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default DiscourseBrowser;
