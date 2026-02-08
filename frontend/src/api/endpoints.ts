import apiClient from './client';
import type {
  AuthResponse,
  CitationCreate,
  CitationResponse,
  CollectionJobCreate,
  CollectionJobResponse,
  CollectionStats,
  DashboardStats,
  DiscourseSampleCreate,
  DiscourseSampleDetailResponse,
  DiscourseSampleResponse,
  DiscourseTypeResponse,
  ExportFormat,
  FilterParams,
  GeographicDistributionResponse,
  LocationCreate,
  LocationResponse,
  LoginRequest,
  MapLocation,
  PaginatedResponse,
  RegisterRequest,
  ResearchNoteCreate,
  ResearchNoteDetailResponse,
  ResearchNoteResponse,
  ResearchNoteUpdate,
  SampleAnalysisResponse,
  SavedQuote,
  SentimentDistributionResponse,
  SentimentOverTimeResponse,
  SourceCreate,
  SourceResponse,
  SourceUpdate,
  ThemeCoOccurrenceResponse,
  ThemeCreate,
  ThemeFrequencyResponse,
  ThemeResponse,
  TimelineResponse,
  TrendingThemesResponse,
  UserResponse,
} from '../types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Convert FilterParams to a flat query-string record, omitting undefined values. */
function buildFilterQuery(params?: FilterParams): Record<string, string> {
  if (!params) return {};
  const query: Record<string, string> = {};
  if (params.date_from) query.date_from = params.date_from;
  if (params.date_to) query.date_to = params.date_to;
  if (params.location_ids?.length) query.location_ids = params.location_ids.join(',');
  if (params.theme_ids?.length) query.theme_ids = params.theme_ids.join(',');
  if (params.sentiment_range) {
    query.sentiment_min = String(params.sentiment_range[0]);
    query.sentiment_max = String(params.sentiment_range[1]);
  }
  if (params.source_types?.length) query.source_types = params.source_types.join(',');
  if (params.discourse_types?.length)
    query.discourse_types = params.discourse_types.join(',');
  if (params.search_query) query.search_query = params.search_query;
  if (params.page !== undefined) query.page = String(params.page);
  if (params.page_size !== undefined) query.page_size = String(params.page_size);
  if (params.sort_by) query.sort_by = params.sort_by;
  if (params.sort_order) query.sort_order = params.sort_order;
  return query;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function login(data: LoginRequest): Promise<AuthResponse> {
  const formData = new URLSearchParams();
  formData.append('username', data.username);
  formData.append('password', data.password);
  const res = await apiClient.post<AuthResponse>('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return res.data;
}

export async function register(data: RegisterRequest): Promise<UserResponse> {
  const res = await apiClient.post<UserResponse>('/auth/register', data);
  return res.data;
}

export async function getCurrentUser(): Promise<UserResponse> {
  const res = await apiClient.get<UserResponse>('/auth/me');
  return res.data;
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>('/dashboard/stats');
  return data;
}

// ---------------------------------------------------------------------------
// Discourse Samples
// ---------------------------------------------------------------------------

export async function fetchSamples(
  filters?: FilterParams,
): Promise<PaginatedResponse<DiscourseSampleResponse>> {
  const { data } = await apiClient.get<
    PaginatedResponse<DiscourseSampleResponse>
  >('/samples/', { params: buildFilterQuery(filters) });
  return data;
}

export async function fetchSampleDetail(
  id: string,
): Promise<DiscourseSampleDetailResponse> {
  const { data } = await apiClient.get<DiscourseSampleDetailResponse>(
    `/samples/${id}/`,
  );
  return data;
}

export async function createSample(
  payload: DiscourseSampleCreate,
): Promise<DiscourseSampleResponse> {
  const { data } = await apiClient.post<DiscourseSampleResponse>(
    '/samples/',
    payload,
  );
  return data;
}

export async function deleteSample(id: string): Promise<void> {
  await apiClient.delete(`/samples/${id}`);
}

export async function fetchSampleAnalysis(
  sampleId: string,
): Promise<SampleAnalysisResponse> {
  const { data } = await apiClient.get<SampleAnalysisResponse>(
    `/samples/${sampleId}/analysis/`,
  );
  return data;
}

// ---------------------------------------------------------------------------
// Sources
// ---------------------------------------------------------------------------

export async function fetchSources(): Promise<SourceResponse[]> {
  const { data } = await apiClient.get<SourceResponse[]>('/sources/');
  return data;
}

export async function fetchSource(id: string): Promise<SourceResponse> {
  const { data } = await apiClient.get<SourceResponse>(`/sources/${id}/`);
  return data;
}

export async function createSource(
  payload: SourceCreate,
): Promise<SourceResponse> {
  const { data } = await apiClient.post<SourceResponse>('/sources/', payload);
  return data;
}

export async function updateSource(
  id: string,
  payload: SourceUpdate,
): Promise<SourceResponse> {
  const { data } = await apiClient.put<SourceResponse>(
    `/sources/${id}`,
    payload,
  );
  return data;
}

export async function deleteSource(id: string): Promise<void> {
  await apiClient.delete(`/sources/${id}`);
}

// ---------------------------------------------------------------------------
// Themes
// ---------------------------------------------------------------------------

export async function fetchThemes(): Promise<ThemeResponse[]> {
  const { data } = await apiClient.get<ThemeResponse[]>('/themes/');
  return data;
}

export async function createTheme(
  payload: ThemeCreate,
): Promise<ThemeResponse> {
  const { data } = await apiClient.post<ThemeResponse>('/themes/', payload);
  return data;
}

export async function fetchThemeSamples(
  themeId: string,
  filters?: FilterParams,
): Promise<PaginatedResponse<DiscourseSampleResponse>> {
  const { data } = await apiClient.get<
    PaginatedResponse<DiscourseSampleResponse>
  >(`/themes/${themeId}/samples/`, { params: buildFilterQuery(filters) });
  return data;
}

// ---------------------------------------------------------------------------
// Locations
// ---------------------------------------------------------------------------

export async function fetchLocations(): Promise<LocationResponse[]> {
  const { data } = await apiClient.get<LocationResponse[]>('/locations/');
  return data;
}

export async function createLocation(
  payload: LocationCreate,
): Promise<LocationResponse> {
  const { data } = await apiClient.post<LocationResponse>(
    '/locations/',
    payload,
  );
  return data;
}

export async function fetchLocationSamples(
  locationId: string,
  filters?: FilterParams,
): Promise<PaginatedResponse<DiscourseSampleResponse>> {
  const { data } = await apiClient.get<
    PaginatedResponse<DiscourseSampleResponse>
  >(`/locations/${locationId}/samples`, { params: buildFilterQuery(filters) });
  return data;
}

// ---------------------------------------------------------------------------
// Collection Jobs
// ---------------------------------------------------------------------------

export async function fetchCollectionJobs(): Promise<CollectionJobResponse[]> {
  const { data } = await apiClient.get<CollectionJobResponse[]>(
    '/jobs/',
  );
  return data;
}

export async function createCollectionJob(
  payload: CollectionJobCreate,
): Promise<CollectionJobResponse> {
  const { data } = await apiClient.post<CollectionJobResponse>(
    '/jobs/start',
    payload,
  );
  return data;
}

export async function fetchJobStatus(
  id: string,
): Promise<CollectionJobResponse> {
  const { data } = await apiClient.get<CollectionJobResponse>(
    `/jobs/${id}/status/`,
  );
  return data;
}

export async function fetchCollectionStats(): Promise<CollectionStats> {
  const { data } = await apiClient.get<CollectionStats>(
    '/jobs/stats',
  );
  return data;
}

// ---------------------------------------------------------------------------
// Research Notes
// ---------------------------------------------------------------------------

export async function fetchNotes(): Promise<ResearchNoteResponse[]> {
  const { data } = await apiClient.get<ResearchNoteResponse[]>('/notes/');
  return data;
}

export async function fetchNoteDetail(
  id: string,
): Promise<ResearchNoteDetailResponse> {
  const { data } = await apiClient.get<ResearchNoteDetailResponse>(
    `/notes/${id}`,
  );
  return data;
}

export async function createNote(
  payload: ResearchNoteCreate,
): Promise<ResearchNoteResponse> {
  const { data } = await apiClient.post<ResearchNoteResponse>(
    '/notes/',
    payload,
  );
  return data;
}

export async function updateNote(
  id: string,
  payload: ResearchNoteUpdate,
): Promise<ResearchNoteResponse> {
  const { data } = await apiClient.put<ResearchNoteResponse>(
    `/notes/${id}`,
    payload,
  );
  return data;
}

export async function deleteNote(id: string): Promise<void> {
  await apiClient.delete(`/notes/${id}`);
}

export async function linkSampleToNote(
  noteId: string,
  sampleId: string,
): Promise<void> {
  await apiClient.post(`/notes/${noteId}/link-sample/${sampleId}`);
}

export async function unlinkSampleFromNote(
  noteId: string,
  sampleId: string,
): Promise<void> {
  await apiClient.post(`/notes/${noteId}/unlink-sample/${sampleId}`);
}

// ---------------------------------------------------------------------------
// Citations
// ---------------------------------------------------------------------------

export async function createCitation(
  payload: CitationCreate,
): Promise<CitationResponse> {
  const { data } = await apiClient.post<CitationResponse>(
    '/citations',
    payload,
  );
  return data;
}

export async function fetchCitationsForSample(
  sampleId: string,
): Promise<CitationResponse[]> {
  const { data } = await apiClient.get<CitationResponse[]>(
    `/citations/sample/${sampleId}/`,
  );
  return data;
}

// ---------------------------------------------------------------------------
// Analysis Endpoints
// ---------------------------------------------------------------------------

export async function fetchSentimentOverTime(
  granularity: string = 'day',
  filters?: FilterParams,
): Promise<SentimentOverTimeResponse> {
  const { data } = await apiClient.get<SentimentOverTimeResponse>(
    '/analysis/sentiment-over-time',
    { params: { granularity, ...buildFilterQuery(filters) } },
  );
  return data;
}

export async function fetchThemeFrequencies(
  filters?: FilterParams,
): Promise<ThemeFrequencyResponse> {
  const { data } = await apiClient.get<ThemeFrequencyResponse>(
    '/analysis/theme-frequencies',
    { params: buildFilterQuery(filters) },
  );
  return data;
}

export async function fetchGeographicDistribution(
  filters?: FilterParams,
): Promise<GeographicDistributionResponse> {
  const { data } = await apiClient.get<GeographicDistributionResponse>(
    '/analysis/geographic-distribution',
    { params: buildFilterQuery(filters) },
  );
  return data;
}

export async function fetchDiscourseTypes(
  filters?: FilterParams,
): Promise<DiscourseTypeResponse> {
  const { data } = await apiClient.get<DiscourseTypeResponse>(
    '/analysis/discourse-types',
    { params: buildFilterQuery(filters) },
  );
  return data;
}

export async function fetchTrendingThemes(): Promise<TrendingThemesResponse> {
  const { data } = await apiClient.get<TrendingThemesResponse>(
    '/analysis/trending-themes',
  );
  return data;
}

export async function fetchTimeline(
  granularity: string = 'day',
  filters?: FilterParams,
): Promise<TimelineResponse> {
  const { data } = await apiClient.get<TimelineResponse>(
    '/analysis/timeline',
    { params: { granularity, ...buildFilterQuery(filters) } },
  );
  return data;
}

export async function fetchSentimentDistribution(
  filters?: FilterParams,
): Promise<SentimentDistributionResponse> {
  const { data } = await apiClient.get<SentimentDistributionResponse>(
    '/analysis/sentiment-distribution',
    { params: buildFilterQuery(filters) },
  );
  return data;
}

export async function fetchMapLocations(
  filters?: FilterParams,
): Promise<MapLocation[]> {
  const { data } = await apiClient.get<MapLocation[]>(
    '/analysis/map-locations',
    { params: buildFilterQuery(filters) },
  );
  return data;
}

export async function fetchThemeCoOccurrence(
  filters?: FilterParams,
): Promise<ThemeCoOccurrenceResponse> {
  const { data } = await apiClient.get<ThemeCoOccurrenceResponse>(
    '/analysis/theme-co-occurrence',
    { params: buildFilterQuery(filters) },
  );
  return data;
}

// ---------------------------------------------------------------------------
// Saved Quotes
// ---------------------------------------------------------------------------

export async function fetchSavedQuotes(): Promise<SavedQuote[]> {
  const { data } = await apiClient.get<SavedQuote[]>('/quotes/');
  return data;
}

export async function saveQuote(
  sampleId: string,
  text: string,
): Promise<SavedQuote> {
  const { data } = await apiClient.post<SavedQuote>('/quotes/', {
    sample_id: sampleId,
    text,
  });
  return data;
}

export async function deleteQuote(id: string): Promise<void> {
  await apiClient.delete(`/quotes/${id}`);
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export async function exportSamples(
  format: ExportFormat = 'csv',
  filters?: FilterParams,
): Promise<Blob> {
  const { data } = await apiClient.get('/export/samples', {
    params: { format, ...buildFilterQuery(filters) },
    responseType: 'blob',
  });
  return data as Blob;
}

export async function exportNotes(format: ExportFormat = 'json'): Promise<Blob> {
  const { data } = await apiClient.get('/export/notes', {
    params: { format },
    responseType: 'blob',
  });
  return data as Blob;
}
