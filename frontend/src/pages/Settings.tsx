import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { fetchThemes, exportSamples, exportNotes } from '../api/endpoints';
import type { ExportFormat } from '../types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getStoredKeywords(): string[] {
  try {
    const raw = localStorage.getItem('thermoculture_keywords');
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function setStoredKeywords(keywords: string[]) {
  localStorage.setItem('thermoculture_keywords', JSON.stringify(keywords));
}

// ---------------------------------------------------------------------------
// Analysis Configuration Section
// ---------------------------------------------------------------------------

function AnalysisConfig() {
  const [keywordsInput, setKeywordsInput] = useState('');
  const [savedKeywords, setSavedKeywords] = useState<string[]>([]);

  const themesQ = useQuery({
    queryKey: ['themes'],
    queryFn: fetchThemes,
  });

  useEffect(() => {
    const kw = getStoredKeywords();
    setSavedKeywords(kw);
    setKeywordsInput(kw.join(', '));
  }, []);

  function saveKeywords() {
    const parsed = keywordsInput
      .split(',')
      .map((k) => k.trim())
      .filter(Boolean);
    setStoredKeywords(parsed);
    setSavedKeywords(parsed);
    toast.success(`Saved ${parsed.length} keywords`);
  }

  const themes = themesQ.data ?? [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Analysis Configuration
      </h2>

      {/* Custom keywords */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Custom Keywords
        </label>
        <p className="text-xs text-gray-400 mb-2">
          Comma-separated list of keywords to monitor. Saved to browser storage.
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            value={keywordsInput}
            onChange={(e) => setKeywordsInput(e.target.value)}
            placeholder="climate, heatwave, flooding, energy bills..."
            className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
          />
          <button
            type="button"
            onClick={saveKeywords}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            Save
          </button>
        </div>
        {savedKeywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {savedKeywords.map((kw, i) => (
              <span
                key={i}
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300"
              >
                {kw}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Themes */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Existing Themes ({themes.length})
        </h3>
        {themesQ.isLoading ? (
          <div className="animate-pulse space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-6 bg-gray-100 dark:bg-gray-700 rounded w-1/3" />
            ))}
          </div>
        ) : themes.length === 0 ? (
          <p className="text-gray-400 text-sm">No themes found.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {themes.map((t) => (
              <span
                key={t.id}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300"
                title={t.description ?? undefined}
              >
                {t.name}
                {t.category && (
                  <span className="ml-1.5 text-purple-500 dark:text-purple-400">
                    ({t.category})
                  </span>
                )}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Export Section
// ---------------------------------------------------------------------------

function ExportSection() {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [loading, setLoading] = useState<string | null>(null);

  async function handleExport(type: 'samples' | 'notes', format: 'csv' | 'json') {
    setLoading(`${type}-${format}`);
    try {
      let blob: Blob;
      if (type === 'samples') {
        blob = await exportSamples(format as ExportFormat, {
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
        });
      } else {
        blob = await exportNotes(format as ExportFormat);
      }
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${type}-export-${new Date().toISOString().slice(0, 10)}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success(`Exported ${type} as ${format.toUpperCase()}`);
    } catch {
      toast.error(`Failed to export ${type}`);
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Export Data
      </h2>

      {/* Date range for samples export */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Date Range (for samples export)
        </label>
        <div className="flex gap-3">
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
          />
          <span className="flex items-center text-gray-400 text-sm">to</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
          />
        </div>
      </div>

      {/* Export samples */}
      <div className="mb-4">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Export All Samples
        </h3>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => handleExport('samples', 'csv')}
            disabled={loading === 'samples-csv'}
            className="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            {loading === 'samples-csv' ? (
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Exporting...
              </span>
            ) : (
              'Export CSV'
            )}
          </button>
          <button
            type="button"
            onClick={() => handleExport('samples', 'json')}
            disabled={loading === 'samples-json'}
            className="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            {loading === 'samples-json' ? (
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Exporting...
              </span>
            ) : (
              'Export JSON'
            )}
          </button>
        </div>
      </div>

      {/* Export notes */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Export Research Notes
        </h3>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => handleExport('notes', 'csv')}
            disabled={loading === 'notes-csv'}
            className="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            {loading === 'notes-csv' ? 'Exporting...' : 'Export CSV'}
          </button>
          <button
            type="button"
            onClick={() => handleExport('notes', 'json')}
            disabled={loading === 'notes-json'}
            className="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            {loading === 'notes-json' ? 'Exporting...' : 'Export JSON'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// About Section
// ---------------------------------------------------------------------------

function AboutSection() {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        About
      </h2>

      <dl className="space-y-3 text-sm">
        <div>
          <dt className="text-gray-500 dark:text-gray-400">Application</dt>
          <dd className="font-medium text-gray-900 dark:text-white">
            Thermoculture Research Assistant
          </dd>
        </div>
        <div>
          <dt className="text-gray-500 dark:text-gray-400">Version</dt>
          <dd className="font-medium text-gray-900 dark:text-white">1.0.0</dd>
        </div>
        <div>
          <dt className="text-gray-500 dark:text-gray-400">Description</dt>
          <dd className="text-gray-700 dark:text-gray-300">
            A research tool for collecting, analysing, and exploring UK public discourse
            on climate change and thermal culture. Features include discourse collection
            from multiple sources, NLP-driven sentiment analysis and classification,
            geographic mapping, theme extraction, and a research note-taking workspace.
          </dd>
        </div>
        <div>
          <dt className="text-gray-500 dark:text-gray-400">Tech Stack</dt>
          <dd className="text-gray-700 dark:text-gray-300">
            <ul className="list-disc list-inside space-y-1 mt-1">
              <li>
                <span className="font-medium">Frontend:</span> React 18, TypeScript, TailwindCSS,
                Recharts, react-leaflet, @tanstack/react-query
              </li>
              <li>
                <span className="font-medium">Backend:</span> FastAPI, SQLAlchemy, PostgreSQL, Celery
              </li>
              <li>
                <span className="font-medium">NLP:</span> Sentiment analysis, discourse classification,
                theme extraction
              </li>
              <li>
                <span className="font-medium">Infrastructure:</span> Docker, Vite, nginx
              </li>
            </ul>
          </dd>
        </div>
        <div>
          <dt className="text-gray-500 dark:text-gray-400">Documentation</dt>
          <dd>
            <a
              href="https://github.com/thermoculture/research-assistant"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              View Documentation on GitHub
            </a>
          </dd>
        </div>
      </dl>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

const Settings: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Settings
      </h1>

      <div className="space-y-6">
        <AnalysisConfig />
        <ExportSection />
        <AboutSection />
      </div>
    </div>
  );
};

export default Settings;
