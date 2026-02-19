import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { format } from 'date-fns';
import type {
  DiscourseSampleResponse,
  SourceResponse,
  LocationResponse,
  ThemeResponse,
  SentimentAnalysisResponse,
  DiscourseClassificationResponse,
} from '../types';
import { SentimentLabel } from '../types';

interface SampleCardProps {
  sample: DiscourseSampleResponse & {
    source?: SourceResponse | null;
    location?: LocationResponse | null;
    themes?: ThemeResponse[];
    sentiment?: SentimentAnalysisResponse | null;
    classification?: DiscourseClassificationResponse | null;
  };
}

/** Truncate text to a maximum character length. */
function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  return text.slice(0, max).trimEnd() + '...';
}

/** Map sentiment label to a display color config. */
function sentimentColor(label?: SentimentLabel): {
  dot: string;
  bg: string;
  text: string;
} {
  switch (label) {
    case SentimentLabel.VERY_POSITIVE:
    case SentimentLabel.POSITIVE:
      return {
        dot: 'bg-sentiment-positive',
        bg: 'bg-sentiment-positive-light',
        text: 'text-green-800',
      };
    case SentimentLabel.NEUTRAL:
      return {
        dot: 'bg-sentiment-neutral',
        bg: 'bg-sentiment-neutral-light',
        text: 'text-yellow-800',
      };
    case SentimentLabel.NEGATIVE:
    case SentimentLabel.VERY_NEGATIVE:
      return {
        dot: 'bg-sentiment-negative',
        bg: 'bg-sentiment-negative-light',
        text: 'text-red-800',
      };
    default:
      return {
        dot: 'bg-gray-400',
        bg: 'bg-gray-100',
        text: 'text-gray-700',
      };
  }
}

/** Format a classification type enum value to a human-readable string. */
function formatClassification(raw: string): string {
  return raw
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
}

export default function SampleCard({ sample }: SampleCardProps) {
  const navigate = useNavigate();
  const colors = sentimentColor(sample.sentiment?.sentiment_label);

  const publishedDate = sample.published_at
    ? format(new Date(sample.published_at), 'dd MMM yyyy')
    : format(new Date(sample.collected_at), 'dd MMM yyyy');

  return (
    <article
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/samples/${sample.id}`)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          navigate(`/samples/${sample.id}`);
        }
      }}
      className="group cursor-pointer rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-all hover:border-primary-300 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary-500"
    >
      {/* Header row */}
      <div className="mb-2 flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-gray-900 group-hover:text-primary-700 line-clamp-2">
          {sample.title}
        </h3>

        {/* Sentiment indicator dot */}
        {sample.sentiment && (
          <span
            className={clsx(
              'mt-1 h-2.5 w-2.5 shrink-0 rounded-full',
              colors.dot,
            )}
            title={`Sentiment: ${sample.sentiment.sentiment_label}`}
          />
        )}
      </div>

      {/* Content preview */}
      <p className="mb-3 text-xs leading-relaxed text-gray-600">
        {truncate(sample.content, 200)}
      </p>

      {/* Badges row */}
      <div className="mb-3 flex flex-wrap items-center gap-1.5">
        {/* Source badge */}
        {sample.source && (
          <span className="inline-flex items-center rounded-full bg-uk-royal/10 px-2 py-0.5 text-[10px] font-medium text-uk-royal">
            {sample.source.source_type}
          </span>
        )}

        {/* Location badge */}
        {sample.location && (
          <span className="inline-flex items-center rounded-full bg-uk-heritage/10 px-2 py-0.5 text-[10px] font-medium text-uk-heritage">
            {sample.location.name}
          </span>
        )}

        {/* Classification badge */}
        {sample.classification && (
          <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-700">
            {formatClassification(sample.classification.classification_type)}
          </span>
        )}

        {/* Sentiment badge */}
        {sample.sentiment && (
          <span
            className={clsx(
              'inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium',
              colors.bg,
              colors.text,
            )}
          >
            {sample.sentiment.sentiment_label.replace('_', ' ')}
          </span>
        )}
      </div>

      {/* Theme tags */}
      {sample.themes && sample.themes.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1">
          {sample.themes.slice(0, 4).map((theme) => (
            <span
              key={theme.id}
              className="inline-block rounded bg-primary-50 px-1.5 py-0.5 text-[10px] font-medium text-primary-700"
            >
              ⚙ {theme.name}
            </span>
          ))}
          {sample.themes.length > 4 && (
            <span className="inline-block rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">
              +{sample.themes.length - 4} more
            </span>
          )}
        </div>
      )}

      {/* Footer: date + author */}
      <div className="flex items-center justify-between text-[11px] text-gray-400">
        <time dateTime={sample.published_at || sample.collected_at}>
          {publishedDate}
        </time>
        {sample.author && (
          <span className="truncate max-w-[120px]">{sample.author}</span>
        )}
      </div>
    </article>
  );
}
