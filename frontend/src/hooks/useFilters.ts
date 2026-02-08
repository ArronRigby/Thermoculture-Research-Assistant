import { useState, useCallback, useMemo, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { FilterParams, SourceType, ClassificationType } from '../types';

interface UseFiltersReturn {
  filters: FilterParams;
  setSearch: (query: string) => void;
  setDateRange: (from?: string, to?: string) => void;
  setSourceTypes: (types: SourceType[]) => void;
  setDiscourseTypes: (types: ClassificationType[]) => void;
  setSentimentRange: (range: [number, number]) => void;
  setLocationIds: (ids: string[]) => void;
  setThemeIds: (ids: string[]) => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  setSortBy: (field: string) => void;
  setSortOrder: (order: 'asc' | 'desc') => void;
  resetFilters: () => void;
  hasActiveFilters: boolean;
}

const DEFAULT_FILTERS: FilterParams = {
  page: 1,
  page_size: 20,
  sort_order: 'desc',
};

/** Parse a comma-separated string back into an array, or return undefined. */
function parseArray(value: string | null): string[] | undefined {
  if (!value) return undefined;
  const items = value.split(',').filter(Boolean);
  return items.length > 0 ? items : undefined;
}

/** Parse a sentiment range "min,max" string back into a tuple. */
function parseSentimentRange(
  value: string | null,
): [number, number] | undefined {
  if (!value) return undefined;
  const parts = value.split(',').map(Number);
  if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
    return [parts[0], parts[1]];
  }
  return undefined;
}

export function useFilters(): UseFiltersReturn {
  const [searchParams, setSearchParams] = useSearchParams();

  // Hydrate initial state from URL search params
  const initialFilters = useMemo<FilterParams>(() => {
    return {
      search_query: searchParams.get('search_query') || undefined,
      date_from: searchParams.get('date_from') || undefined,
      date_to: searchParams.get('date_to') || undefined,
      source_types: parseArray(searchParams.get('source_types')) as
        | SourceType[]
        | undefined,
      discourse_types: parseArray(searchParams.get('discourse_types')) as
        | ClassificationType[]
        | undefined,
      sentiment_range: parseSentimentRange(
        searchParams.get('sentiment_range'),
      ),
      location_ids: parseArray(searchParams.get('location_ids')),
      theme_ids: parseArray(searchParams.get('theme_ids')),
      page: searchParams.get('page')
        ? Number(searchParams.get('page'))
        : DEFAULT_FILTERS.page,
      page_size: searchParams.get('page_size')
        ? Number(searchParams.get('page_size'))
        : DEFAULT_FILTERS.page_size,
      sort_by: searchParams.get('sort_by') || undefined,
      sort_order:
        (searchParams.get('sort_order') as 'asc' | 'desc') ||
        DEFAULT_FILTERS.sort_order,
    };
    // We only use this for initialization, not as a reactive dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const [filters, setFilters] = useState<FilterParams>(initialFilters);

  // Sync filters to URL search params whenever they change
  useEffect(() => {
    const params = new URLSearchParams();

    if (filters.search_query) params.set('search_query', filters.search_query);
    if (filters.date_from) params.set('date_from', filters.date_from);
    if (filters.date_to) params.set('date_to', filters.date_to);
    if (filters.source_types?.length)
      params.set('source_types', filters.source_types.join(','));
    if (filters.discourse_types?.length)
      params.set('discourse_types', filters.discourse_types.join(','));
    if (filters.sentiment_range)
      params.set('sentiment_range', filters.sentiment_range.join(','));
    if (filters.location_ids?.length)
      params.set('location_ids', filters.location_ids.join(','));
    if (filters.theme_ids?.length)
      params.set('theme_ids', filters.theme_ids.join(','));
    if (filters.page && filters.page !== DEFAULT_FILTERS.page)
      params.set('page', String(filters.page));
    if (filters.page_size && filters.page_size !== DEFAULT_FILTERS.page_size)
      params.set('page_size', String(filters.page_size));
    if (filters.sort_by) params.set('sort_by', filters.sort_by);
    if (filters.sort_order && filters.sort_order !== DEFAULT_FILTERS.sort_order)
      params.set('sort_order', filters.sort_order);

    setSearchParams(params, { replace: true });
  }, [filters, setSearchParams]);

  // --- Individual setters ---

  const setSearch = useCallback((query: string) => {
    setFilters((prev) => ({
      ...prev,
      search_query: query || undefined,
      page: 1,
    }));
  }, []);

  const setDateRange = useCallback((from?: string, to?: string) => {
    setFilters((prev) => ({
      ...prev,
      date_from: from || undefined,
      date_to: to || undefined,
      page: 1,
    }));
  }, []);

  const setSourceTypes = useCallback((types: SourceType[]) => {
    setFilters((prev) => ({
      ...prev,
      source_types: types.length > 0 ? types : undefined,
      page: 1,
    }));
  }, []);

  const setDiscourseTypes = useCallback((types: ClassificationType[]) => {
    setFilters((prev) => ({
      ...prev,
      discourse_types: types.length > 0 ? types : undefined,
      page: 1,
    }));
  }, []);

  const setSentimentRange = useCallback((range: [number, number]) => {
    setFilters((prev) => ({
      ...prev,
      sentiment_range: range,
      page: 1,
    }));
  }, []);

  const setLocationIds = useCallback((ids: string[]) => {
    setFilters((prev) => ({
      ...prev,
      location_ids: ids.length > 0 ? ids : undefined,
      page: 1,
    }));
  }, []);

  const setThemeIds = useCallback((ids: string[]) => {
    setFilters((prev) => ({
      ...prev,
      theme_ids: ids.length > 0 ? ids : undefined,
      page: 1,
    }));
  }, []);

  const setPage = useCallback((page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  }, []);

  const setPageSize = useCallback((size: number) => {
    setFilters((prev) => ({ ...prev, page_size: size, page: 1 }));
  }, []);

  const setSortBy = useCallback((field: string) => {
    setFilters((prev) => ({ ...prev, sort_by: field }));
  }, []);

  const setSortOrder = useCallback((order: 'asc' | 'desc') => {
    setFilters((prev) => ({ ...prev, sort_order: order }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({ ...DEFAULT_FILTERS });
  }, []);

  const hasActiveFilters = useMemo(() => {
    return !!(
      filters.search_query ||
      filters.date_from ||
      filters.date_to ||
      filters.source_types?.length ||
      filters.discourse_types?.length ||
      filters.sentiment_range ||
      filters.location_ids?.length ||
      filters.theme_ids?.length
    );
  }, [filters]);

  return {
    filters,
    setSearch,
    setDateRange,
    setSourceTypes,
    setDiscourseTypes,
    setSentimentRange,
    setLocationIds,
    setThemeIds,
    setPage,
    setPageSize,
    setSortBy,
    setSortOrder,
    resetFilters,
    hasActiveFilters,
  };
}

export default useFilters;
