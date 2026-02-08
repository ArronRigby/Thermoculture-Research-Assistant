import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {
  fetchSampleDetail,
  fetchSampleAnalysis,
  createCitation,
  saveQuote,
} from '../api/endpoints';
import SentimentGauge from '../components/SentimentGauge';
import type { CitationFormat } from '../types';

// Fix default Leaflet marker icon
const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function classificationLabel(t: string): string {
  return t.replace(/_/g, ' ');
}

function formatDate(d: string | null): string {
  if (!d) return 'N/A';
  return new Date(d).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

function generateCitationText(
  format: CitationFormat,
  author: string | null,
  title: string,
  sourceName: string | null,
  publishedAt: string | null,
  url: string | null
): string {
  const yr = publishedAt ? new Date(publishedAt).getFullYear() : 'n.d.';
  const auth = author ?? 'Unknown Author';
  const src = sourceName ?? 'Unknown Source';

  switch (format) {
    case 'APA':
      return `${auth} (${yr}). ${title}. ${src}. ${url ? `Retrieved from ${url}` : ''}`.trim();
    case 'MLA':
      return `${auth}. "${title}." ${src}, ${yr}. ${url ? `Web. ${url}` : ''}`.trim();
    case 'CHICAGO':
      return `${auth}. "${title}." ${src}. ${url ? `${url}` : ''} (accessed ${new Date().toLocaleDateString('en-GB')}).`.trim();
    default:
      return `${auth} (${yr}). ${title}. ${src}.`;
  }
}

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

function DetailSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-pulse">
      <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded mb-6" />
      <div className="h-8 w-3/4 bg-gray-200 dark:bg-gray-700 rounded mb-4" />
      <div className="space-y-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-4 bg-gray-200 dark:bg-gray-700 rounded" style={{ width: `${90 - i * 5}%` }} />
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const SampleDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [citationFormat, setCitationFormat] = useState<CitationFormat>('APA' as CitationFormat);
  const [showCitation, setShowCitation] = useState(false);

  const sampleQ = useQuery({
    queryKey: ['sample', id],
    queryFn: () => fetchSampleDetail(id!),
    enabled: !!id,
  });

  const analysisQ = useQuery({
    queryKey: ['sampleAnalysis', id],
    queryFn: () => fetchSampleAnalysis(id!),
    enabled: !!id,
  });

  const citationMut = useMutation({
    mutationFn: (fmt: CitationFormat) =>
      createCitation({ sample_id: id!, format: fmt }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sample', id] });
    },
  });

  const quoteMut = useMutation({
    mutationFn: (text: string) => saveQuote(id!, text),
  });

  const sample = sampleQ.data;
  const analysis = analysisQ.data;

  if (sampleQ.isLoading) return <DetailSkeleton />;

  if (sampleQ.isError || !sample) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <p className="text-red-500 text-lg">Failed to load sample.</p>
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="mt-4 text-blue-600 hover:text-blue-700"
        >
          Go back
        </button>
      </div>
    );
  }

  const latestSentiment = analysis?.sentiments?.[0];
  const latestClassification = analysis?.classifications?.[0];
  const themes = analysis?.themes ?? sample.themes ?? [];

  const citationText = generateCitationText(
    citationFormat,
    sample.author,
    sample.title,
    sample.source?.name ?? null,
    sample.published_at,
    sample.source_url
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back button */}
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 mb-6"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to browser
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Title & content */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              {sample.title}
            </h1>
            <div className="prose prose-gray dark:prose-invert max-w-none text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
              {sample.content}
            </div>
          </div>

          {/* Analysis section */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Analysis
            </h2>

            {analysisQ.isLoading ? (
              <div className="animate-pulse space-y-4">
                <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
              </div>
            ) : (
              <div className="space-y-6">
                {/* Sentiment */}
                {latestSentiment && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                      Sentiment
                    </h3>
                    <SentimentGauge
                      value={latestSentiment.overall_sentiment}
                      label={latestSentiment.sentiment_label.replace(/_/g, ' ')}
                      size="lg"
                    />
                    <p className="text-xs text-gray-400 mt-1">
                      Confidence: {(latestSentiment.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                )}

                {/* Classification */}
                {latestClassification && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                      Discourse Classification
                    </h3>
                    <div className="flex items-center gap-3">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200">
                        {classificationLabel(latestClassification.classification_type)}
                      </span>
                    </div>
                    <div className="mt-2">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                          <div
                            className="h-full bg-indigo-500 rounded-full transition-all"
                            style={{ width: `${latestClassification.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 w-10 text-right">
                          {(latestClassification.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Themes */}
                {themes.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                      Themes
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {themes.map((t) => (
                        <span
                          key={t.id}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300"
                        >
                          {t.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Key phrases from metadata */}
                {sample.raw_metadata && Array.isArray((sample.raw_metadata as Record<string, unknown>).key_phrases) && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                      Key Phrases
                    </h3>
                    <ul className="flex flex-wrap gap-2">
                      {((sample.raw_metadata as Record<string, unknown>).key_phrases as string[]).map(
                        (phrase, i) => (
                          <li
                            key={i}
                            className="px-2.5 py-1 rounded bg-gray-100 dark:bg-gray-700 text-xs text-gray-600 dark:text-gray-300"
                          >
                            {phrase}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Citation generator */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Citation
              </h2>
              <button
                type="button"
                onClick={() => setShowCitation(!showCitation)}
                className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                {showCitation ? 'Hide' : 'Generate Citation'}
              </button>
            </div>

            {showCitation && (
              <div className="space-y-3">
                <div className="flex gap-2">
                  {(['APA', 'MLA', 'CHICAGO'] as CitationFormat[]).map((fmt) => (
                    <button
                      key={fmt}
                      type="button"
                      onClick={() => setCitationFormat(fmt)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                        citationFormat === fmt
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      {fmt}
                    </button>
                  ))}
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-700 dark:text-gray-300 italic leading-relaxed">
                    {citationText}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(citationText)}
                    className="px-3 py-1.5 text-sm rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
                  >
                    Copy to Clipboard
                  </button>
                  <button
                    type="button"
                    onClick={() => citationMut.mutate(citationFormat)}
                    disabled={citationMut.isPending}
                    className="px-3 py-1.5 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {citationMut.isPending ? 'Saving...' : 'Save Citation'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => {
                const selectedText = window.getSelection()?.toString() || sample.content.slice(0, 200);
                quoteMut.mutate(selectedText);
              }}
              disabled={quoteMut.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-amber-100 text-amber-800 hover:bg-amber-200 dark:bg-amber-900/40 dark:text-amber-300 dark:hover:bg-amber-900/60"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
              </svg>
              {quoteMut.isPending ? 'Saving...' : 'Add to Quote Library'}
            </button>
            <Link
              to="/workspace"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900/40 dark:text-green-300 dark:hover:bg-green-900/60"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              Link to Note
            </Link>
          </div>
        </div>

        {/* Metadata sidebar */}
        <div className="space-y-6">
          {/* Source info */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
              Metadata
            </h3>
            <dl className="space-y-3 text-sm">
              {sample.source && (
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Source</dt>
                  <dd className="font-medium text-gray-900 dark:text-white">
                    {sample.source.name}
                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                      {sample.source.source_type.replace(/_/g, ' ')}
                    </span>
                  </dd>
                </div>
              )}
              {sample.source_url && (
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Source URL</dt>
                  <dd>
                    <a
                      href={sample.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 dark:text-blue-400 hover:underline break-all text-xs"
                    >
                      {sample.source_url}
                    </a>
                  </dd>
                </div>
              )}
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Author</dt>
                <dd className="font-medium text-gray-900 dark:text-white">
                  {sample.author ?? 'Unknown'}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Published</dt>
                <dd className="font-medium text-gray-900 dark:text-white">
                  {formatDate(sample.published_at)}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Collected</dt>
                <dd className="font-medium text-gray-900 dark:text-white">
                  {formatDate(sample.collected_at)}
                </dd>
              </div>
            </dl>
          </div>

          {/* Location mini map */}
          {sample.location && sample.location.latitude && sample.location.longitude && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                Location
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                {sample.location.name} ({sample.location.region.replace(/_/g, ' ')})
              </p>
              <div className="rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700" style={{ height: '200px' }}>
                <MapContainer
                  center={[sample.location.latitude, sample.location.longitude]}
                  zoom={10}
                  scrollWheelZoom={false}
                  dragging={false}
                  zoomControl={false}
                  style={{ height: '100%', width: '100%' }}
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; OpenStreetMap contributors'
                  />
                  <Marker
                    position={[sample.location.latitude, sample.location.longitude]}
                    icon={defaultIcon}
                  >
                    <Popup>{sample.location.name}</Popup>
                  </Marker>
                </MapContainer>
              </div>
            </div>
          )}

          {/* Related notes placeholder */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
              Related Notes
            </h3>
            <p className="text-xs text-gray-400 dark:text-gray-500">
              Link this sample to research notes in the{' '}
              <Link to="/workspace" className="text-blue-600 hover:underline dark:text-blue-400">
                Research Workspace
              </Link>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SampleDetail;
