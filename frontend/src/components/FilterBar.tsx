import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import { fetchLocations, fetchThemes } from '../api/endpoints';
import { SourceType, ClassificationType } from '../types';
import type { FilterParams, LocationResponse, ThemeResponse } from '../types';

interface FilterBarProps {
  filters: FilterParams;
  onFiltersChange: (filters: FilterParams) => void;
  onReset: () => void;
}

const SOURCE_TYPE_OPTIONS: { value: SourceType; label: string }[] = [
  { value: SourceType.NEWS, label: 'News' },
  { value: SourceType.REDDIT, label: 'Reddit' },
  { value: SourceType.FORUM, label: 'Forum' },
  { value: SourceType.SOCIAL_MEDIA, label: 'Social Media' },
  { value: SourceType.MANUAL, label: 'Manual' },
];

const DISCOURSE_TYPE_OPTIONS: { value: ClassificationType; label: string }[] = [
  { value: ClassificationType.PRACTICAL_ADAPTATION, label: 'Practical Adaptation' },
  { value: ClassificationType.EMOTIONAL_RESPONSE, label: 'Emotional Response' },
  { value: ClassificationType.POLICY_DISCUSSION, label: 'Policy Discussion' },
  { value: ClassificationType.COMMUNITY_ACTION, label: 'Community Action' },
  { value: ClassificationType.DENIAL_DISMISSAL, label: 'Denial / Dismissal' },
];

export default function FilterBar({
  filters,
  onFiltersChange,
  onReset,
}: FilterBarProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Local draft state so we can apply in batch
  const [draft, setDraft] = useState<FilterParams>(filters);

  // Keep draft in sync with external filter changes
  useEffect(() => {
    setDraft(filters);
  }, [filters]);

  // Fetch locations and themes for the multiselects
  const { data: locations = [] } = useQuery<LocationResponse[]>({
    queryKey: ['locations'],
    queryFn: fetchLocations,
    staleTime: 10 * 60 * 1000,
  });

  const { data: themes = [] } = useQuery<ThemeResponse[]>({
    queryKey: ['themes'],
    queryFn: fetchThemes,
    staleTime: 10 * 60 * 1000,
  });

  // --- Handlers ---

  function handleSearchChange(value: string) {
    setDraft((prev) => ({ ...prev, search_query: value || undefined }));
  }

  function handleDateChange(field: 'date_from' | 'date_to', value: string) {
    setDraft((prev) => ({ ...prev, [field]: value || undefined }));
  }

  function toggleSourceType(type: SourceType) {
    setDraft((prev) => {
      const current = prev.source_types || [];
      const next = current.includes(type)
        ? current.filter((t) => t !== type)
        : [...current, type];
      return { ...prev, source_types: next.length > 0 ? next : undefined };
    });
  }

  function toggleDiscourseType(type: ClassificationType) {
    setDraft((prev) => {
      const current = prev.discourse_types || [];
      const next = current.includes(type)
        ? current.filter((t) => t !== type)
        : [...current, type];
      return { ...prev, discourse_types: next.length > 0 ? next : undefined };
    });
  }

  function toggleLocation(id: string) {
    setDraft((prev) => {
      const current = prev.location_ids || [];
      const next = current.includes(id)
        ? current.filter((l) => l !== id)
        : [...current, id];
      return { ...prev, location_ids: next.length > 0 ? next : undefined };
    });
  }

  function toggleTheme(id: string) {
    setDraft((prev) => {
      const current = prev.theme_ids || [];
      const next = current.includes(id)
        ? current.filter((t) => t !== id)
        : [...current, id];
      return { ...prev, theme_ids: next.length > 0 ? next : undefined };
    });
  }

  function handleSentimentChange(
    endpoint: 'min' | 'max',
    value: number,
  ) {
    setDraft((prev) => {
      const current = prev.sentiment_range || [-1, 1];
      const next: [number, number] =
        endpoint === 'min' ? [value, current[1]] : [current[0], value];
      return { ...prev, sentiment_range: next };
    });
  }

  function handleApply() {
    onFiltersChange({ ...draft, page: 1 });
  }

  function handleReset() {
    onReset();
    setIsOpen(false);
  }

  const sentimentMin = draft.sentiment_range?.[0] ?? -1;
  const sentimentMax = draft.sentiment_range?.[1] ?? 1;

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      {/* Always-visible search + toggle row */}
      <div className="flex flex-wrap items-center gap-3 p-4">
        {/* Search input */}
        <div className="relative flex-1 min-w-[200px]">
          <svg
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder="Search discourse samples..."
            value={draft.search_query || ''}
            onChange={(e) => handleSearchChange(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleApply()}
            className="w-full rounded-md border border-gray-300 py-2 pl-10 pr-3 text-sm placeholder:text-gray-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
        </div>

        {/* Toggle filters button */}
        <button
          onClick={() => setIsOpen((prev) => !prev)}
          className={clsx(
            'flex items-center gap-1.5 rounded-md border px-3 py-2 text-sm font-medium transition-colors',
            isOpen
              ? 'border-primary-500 bg-primary-50 text-primary-700'
              : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
          )}
        >
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
            />
          </svg>
          Filters
          {isOpen ? (
            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          ) : (
            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          )}
        </button>

        {/* Quick apply */}
        <button
          onClick={handleApply}
          className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
        >
          Search
        </button>
      </div>

      {/* Collapsible filter panel */}
      {isOpen && (
        <div className="border-t border-gray-200 p-4 fade-in">
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
            {/* Date Range */}
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                Date Range
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="date"
                  value={draft.date_from || ''}
                  onChange={(e) => handleDateChange('date_from', e.target.value)}
                  className="flex-1 rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
                <span className="text-xs text-gray-400">to</span>
                <input
                  type="date"
                  value={draft.date_to || ''}
                  onChange={(e) => handleDateChange('date_to', e.target.value)}
                  className="flex-1 rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
            </div>

            {/* Locations multiselect */}
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                Locations
              </label>
              <div className="max-h-32 overflow-y-auto rounded-md border border-gray-300 p-2 custom-scrollbar">
                {locations.length === 0 && (
                  <p className="text-xs text-gray-400">No locations available</p>
                )}
                {locations.map((loc) => (
                  <label
                    key={loc.id}
                    className="flex cursor-pointer items-center gap-2 rounded px-1 py-0.5 text-sm hover:bg-gray-50"
                  >
                    <input
                      type="checkbox"
                      checked={draft.location_ids?.includes(loc.id) ?? false}
                      onChange={() => toggleLocation(loc.id)}
                      className="h-3.5 w-3.5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-gray-700">{loc.name}</span>
                    <span className="ml-auto text-xs text-gray-400">
                      {loc.region}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Themes multiselect */}
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                Themes
              </label>
              <div className="max-h-32 overflow-y-auto rounded-md border border-gray-300 p-2 custom-scrollbar">
                {themes.length === 0 && (
                  <p className="text-xs text-gray-400">No themes available</p>
                )}
                {themes.map((theme) => (
                  <label
                    key={theme.id}
                    className="flex cursor-pointer items-center gap-2 rounded px-1 py-0.5 text-sm hover:bg-gray-50"
                  >
                    <input
                      type="checkbox"
                      checked={draft.theme_ids?.includes(theme.id) ?? false}
                      onChange={() => toggleTheme(theme.id)}
                      className="h-3.5 w-3.5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-gray-700">{theme.name}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Source Types */}
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                Source Type
              </label>
              <div className="flex flex-wrap gap-2">
                {SOURCE_TYPE_OPTIONS.map((opt) => {
                  const active = draft.source_types?.includes(opt.value) ?? false;
                  return (
                    <button
                      key={opt.value}
                      onClick={() => toggleSourceType(opt.value)}
                      className={clsx(
                        'rounded-full border px-3 py-1 text-xs font-medium transition-colors',
                        active
                          ? 'border-primary-500 bg-primary-50 text-primary-700'
                          : 'border-gray-300 text-gray-600 hover:border-gray-400',
                      )}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Discourse Types */}
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                Discourse Type
              </label>
              <div className="flex flex-wrap gap-2">
                {DISCOURSE_TYPE_OPTIONS.map((opt) => {
                  const active =
                    draft.discourse_types?.includes(opt.value) ?? false;
                  return (
                    <button
                      key={opt.value}
                      onClick={() => toggleDiscourseType(opt.value)}
                      className={clsx(
                        'rounded-full border px-3 py-1 text-xs font-medium transition-colors',
                        active
                          ? 'border-primary-500 bg-primary-50 text-primary-700'
                          : 'border-gray-300 text-gray-600 hover:border-gray-400',
                      )}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Sentiment Range */}
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                Sentiment Range
              </label>
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <span className="w-8 text-right text-xs text-gray-500">
                    {sentimentMin.toFixed(1)}
                  </span>
                  <input
                    type="range"
                    min={-1}
                    max={1}
                    step={0.1}
                    value={sentimentMin}
                    onChange={(e) =>
                      handleSentimentChange('min', parseFloat(e.target.value))
                    }
                    className="flex-1 accent-primary-600"
                  />
                </div>
                <div className="flex items-center gap-3">
                  <span className="w-8 text-right text-xs text-gray-500">
                    {sentimentMax.toFixed(1)}
                  </span>
                  <input
                    type="range"
                    min={-1}
                    max={1}
                    step={0.1}
                    value={sentimentMax}
                    onChange={(e) =>
                      handleSentimentChange('max', parseFloat(e.target.value))
                    }
                    className="flex-1 accent-primary-600"
                  />
                </div>
                <div className="flex justify-between text-[10px] text-gray-400">
                  <span>Negative</span>
                  <span>Neutral</span>
                  <span>Positive</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="mt-5 flex items-center justify-end gap-3 border-t border-gray-100 pt-4">
            <button
              onClick={handleReset}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Reset All
            </button>
            <button
              onClick={handleApply}
              className="rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
            >
              Apply Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
