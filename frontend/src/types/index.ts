// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export enum SourceType {
  NEWS = 'NEWS',
  REDDIT = 'REDDIT',
  FORUM = 'FORUM',
  SOCIAL_MEDIA = 'SOCIAL_MEDIA',
  MANUAL = 'MANUAL',
}

export enum Region {
  LONDON = 'LONDON',
  SOUTH_EAST = 'SOUTH_EAST',
  SOUTH_WEST = 'SOUTH_WEST',
  EAST = 'EAST',
  WEST_MIDLANDS = 'WEST_MIDLANDS',
  EAST_MIDLANDS = 'EAST_MIDLANDS',
  NORTH_WEST = 'NORTH_WEST',
  NORTH_EAST = 'NORTH_EAST',
  YORKSHIRE = 'YORKSHIRE',
  SCOTLAND = 'SCOTLAND',
  WALES = 'WALES',
  NORTHERN_IRELAND = 'NORTHERN_IRELAND',
}

export enum SentimentLabel {
  VERY_NEGATIVE = 'VERY_NEGATIVE',
  NEGATIVE = 'NEGATIVE',
  NEUTRAL = 'NEUTRAL',
  POSITIVE = 'POSITIVE',
  VERY_POSITIVE = 'VERY_POSITIVE',
}

export enum ClassificationType {
  PRACTICAL_ADAPTATION = 'PRACTICAL_ADAPTATION',
  EMOTIONAL_RESPONSE = 'EMOTIONAL_RESPONSE',
  POLICY_DISCUSSION = 'POLICY_DISCUSSION',
  COMMUNITY_ACTION = 'COMMUNITY_ACTION',
  DENIAL_DISMISSAL = 'DENIAL_DISMISSAL',
}

export enum CitationFormat {
  APA = 'APA',
  MLA = 'MLA',
  CHICAGO = 'CHICAGO',
}

export enum JobStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
}

// ---------------------------------------------------------------------------
// Pagination
// ---------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ---------------------------------------------------------------------------
// Filter Params
// ---------------------------------------------------------------------------

export interface FilterParams {
  date_from?: string;
  date_to?: string;
  location_ids?: string[];
  theme_ids?: string[];
  sentiment_range?: [number, number];
  source_types?: SourceType[];
  discourse_types?: ClassificationType[];
  search_query?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// ---------------------------------------------------------------------------
// Source
// ---------------------------------------------------------------------------

export interface SourceCreate {
  name: string;
  source_type: SourceType;
  url?: string;
  description?: string;
  is_active?: boolean;
}

export interface SourceUpdate {
  name?: string;
  source_type?: SourceType;
  url?: string;
  description?: string;
  is_active?: boolean;
}

export interface SourceResponse {
  id: string;
  name: string;
  source_type: SourceType;
  url: string | null;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Location
// ---------------------------------------------------------------------------

export interface LocationCreate {
  name: string;
  region: Region;
  latitude?: number;
  longitude?: number;
}

export interface LocationResponse {
  id: string;
  name: string;
  region: Region;
  latitude: number | null;
  longitude: number | null;
}

// ---------------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------------

export interface ThemeCreate {
  name: string;
  description?: string;
  category?: string;
}

export interface ThemeResponse {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// DiscourseSample
// ---------------------------------------------------------------------------

export interface DiscourseSampleCreate {
  title: string;
  content: string;
  source_id: string;
  source_url?: string;
  author?: string;
  published_at?: string;
  location_id?: string;
  raw_metadata?: Record<string, unknown>;
  theme_ids?: string[];
}

export interface DiscourseSampleResponse {
  id: string;
  title: string;
  content: string;
  source_id: string;
  source_url: string | null;
  author: string | null;
  published_at: string | null;
  collected_at: string;
  location_id: string | null;
  raw_metadata: Record<string, unknown> | null;
}

export interface DiscourseSampleDetailResponse extends DiscourseSampleResponse {
  source: SourceResponse | null;
  location: LocationResponse | null;
  themes: ThemeResponse[];
}

// ---------------------------------------------------------------------------
// SentimentAnalysis
// ---------------------------------------------------------------------------

export interface SentimentAnalysisResponse {
  id: string;
  sample_id: string;
  overall_sentiment: number;
  sentiment_label: SentimentLabel;
  confidence: number;
  analyzed_at: string;
}

// ---------------------------------------------------------------------------
// DiscourseClassification
// ---------------------------------------------------------------------------

export interface DiscourseClassificationResponse {
  id: string;
  sample_id: string;
  classification_type: ClassificationType;
  confidence: number;
  classified_at: string;
}

// ---------------------------------------------------------------------------
// ResearchNote
// ---------------------------------------------------------------------------

export interface ResearchNoteCreate {
  title: string;
  content: string;
}

export interface ResearchNoteUpdate {
  title?: string;
  content?: string;
}

export interface ResearchNoteResponse {
  id: string;
  title: string;
  content: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface ResearchNoteDetailResponse extends ResearchNoteResponse {
  discourse_samples: DiscourseSampleResponse[];
}

// ---------------------------------------------------------------------------
// Citation
// ---------------------------------------------------------------------------

export interface CitationCreate {
  sample_id: string;
  note_id?: string;
  format?: CitationFormat;
}

export interface CitationResponse {
  id: string;
  sample_id: string;
  note_id: string | null;
  citation_text: string;
  format: CitationFormat;
  created_at: string;
}

// ---------------------------------------------------------------------------
// CollectionJob
// ---------------------------------------------------------------------------

export interface CollectionJobCreate {
  source_id: string;
}

export interface CollectionJobResponse {
  id: string;
  source_id: string;
  status: JobStatus;
  started_at: string | null;
  completed_at: string | null;
  items_collected: number;
  error_message: string | null;
}

// ---------------------------------------------------------------------------
// Analysis response types
// ---------------------------------------------------------------------------

export interface SentimentOverTimePoint {
  date: string;
  average_sentiment: number;
  sample_count: number;
}

export interface SentimentOverTimeResponse {
  data: SentimentOverTimePoint[];
  granularity: string;
}

export interface ThemeFrequencyItem {
  theme_id: string;
  theme_name: string;
  count: number;
}

export interface ThemeFrequencyResponse {
  data: ThemeFrequencyItem[];
}

export interface GeographicDistributionItem {
  region: string;
  count: number;
  average_sentiment: number | null;
}

export interface GeographicDistributionResponse {
  data: GeographicDistributionItem[];
}

export interface DiscourseTypeItem {
  classification_type: string;
  count: number;
  percentage: number;
}

export interface DiscourseTypeResponse {
  data: DiscourseTypeItem[];
}

export interface TrendingThemeItem {
  theme_id: string;
  theme_name: string;
  count: number;
  trend_direction: 'up' | 'down' | 'stable';
}

export interface TrendingThemesResponse {
  data: TrendingThemeItem[];
}

export interface TimelinePoint {
  date: string;
  count: number;
}

export interface TimelineResponse {
  data: TimelinePoint[];
  granularity: string;
}

export interface SampleAnalysisResponse {
  sentiments: SentimentAnalysisResponse[];
  classifications: DiscourseClassificationResponse[];
  themes: ThemeResponse[];
}

// ---------------------------------------------------------------------------
// Dashboard stats
// ---------------------------------------------------------------------------

export interface DashboardStats {
  total_samples: number;
  active_sources: number;
  themes_identified: number;
  running_jobs: number;
}

// ---------------------------------------------------------------------------
// Sentiment distribution
// ---------------------------------------------------------------------------

export interface SentimentDistributionItem {
  label: SentimentLabel;
  count: number;
}

export interface SentimentDistributionResponse {
  data: SentimentDistributionItem[];
}

// ---------------------------------------------------------------------------
// Quote library
// ---------------------------------------------------------------------------

export interface SavedQuote {
  id: string;
  sample_id: string;
  text: string;
  source_name: string;
  author: string | null;
  citation: string;
  saved_at: string;
}

// ---------------------------------------------------------------------------
// UK Map location data
// ---------------------------------------------------------------------------

export interface MapLocation {
  name: string;
  lat: number;
  lng: number;
  count: number;
  avgSentiment: number;
}

// ---------------------------------------------------------------------------
// Theme co-occurrence
// ---------------------------------------------------------------------------

export interface ThemeCoOccurrenceItem {
  theme_a: string;
  theme_b: string;
  count: number;
}

export interface ThemeCoOccurrenceResponse {
  data: ThemeCoOccurrenceItem[];
}

// ---------------------------------------------------------------------------
// Collection stats
// ---------------------------------------------------------------------------

export interface CollectionStats {
  today: number;
  this_week: number;
  this_month: number;
}

// ---------------------------------------------------------------------------
// Auth types
// ---------------------------------------------------------------------------

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Export types
// ---------------------------------------------------------------------------

export type ExportFormat = 'csv' | 'json' | 'bibtex';
