import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import clsx from 'clsx';
import toast from 'react-hot-toast';
import {
  fetchSources,
  createSource,
  updateSource,
  deleteSource,
  fetchCollectionJobs,
  createCollectionJob,
  fetchCollectionStats,
  createSample,
} from '../api/endpoints';
import type {
  SourceType,
  SourceCreate,
  JobStatus,
} from '../types';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SOURCE_TYPES: SourceType[] = [
  'NEWS',
  'REDDIT',
  'FORUM',
  'SOCIAL_MEDIA',
  'MANUAL',
] as SourceType[];

function statusBadgeClass(status: JobStatus): string {
  const map: Record<string, string> = {
    PENDING: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    RUNNING: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    COMPLETED: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    FAILED: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  };
  return map[status] ?? 'bg-gray-100 text-gray-800';
}

function sourceTypeBadge(t: SourceType): string {
  const map: Record<string, string> = {
    NEWS: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    REDDIT: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    FORUM: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    SOCIAL_MEDIA: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
    MANUAL: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  };
  return map[t] ?? 'bg-gray-100 text-gray-800';
}

// ---------------------------------------------------------------------------
// Add Source Modal
// ---------------------------------------------------------------------------

function AddSourceModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<SourceCreate>({
    name: '',
    source_type: 'NEWS' as SourceType,
    url: '',
    description: '',
    is_active: true,
  });

  const createMut = useMutation({
    mutationFn: () => createSource(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      toast.success('Source created');
      onClose();
    },
    onError: () => toast.error('Failed to create source'),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Add Source
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMut.mutate();
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Name
            </label>
            <input
              type="text"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Type
            </label>
            <select
              value={form.source_type}
              onChange={(e) =>
                setForm({ ...form, source_type: e.target.value as SourceType })
              }
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            >
              {SOURCE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              URL
            </label>
            <input
              type="url"
              value={form.url ?? ''}
              onChange={(e) => setForm({ ...form, url: e.target.value })}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              value={form.description ?? ''}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMut.isPending || !form.name.trim()}
              className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createMut.isPending ? 'Creating...' : 'Create Source'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Manual Entry Modal
// ---------------------------------------------------------------------------

function ManualEntryModal({
  onClose,
  sourceId,
}: {
  onClose: () => void;
  sourceId?: string;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    title: '',
    content: '',
    source_url: '',
    author: '',
  });

  const sourcesQ = useQuery({
    queryKey: ['sources'],
    queryFn: fetchSources,
  });

  const [selectedSource, setSelectedSource] = useState(sourceId ?? '');

  const createMut = useMutation({
    mutationFn: () =>
      createSample({
        title: form.title,
        content: form.content,
        source_id: selectedSource,
        source_url: form.source_url || undefined,
        author: form.author || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples'] });
      toast.success('Sample created');
      onClose();
    },
    onError: () => toast.error('Failed to create sample'),
  });

  const sources = sourcesQ.data ?? [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Manual Entry
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMut.mutate();
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Title
            </label>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Content
            </label>
            <textarea
              required
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              rows={6}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Source
            </label>
            <select
              required
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            >
              <option value="">Select source...</option>
              {sources.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Source URL
            </label>
            <input
              type="url"
              value={form.source_url}
              onChange={(e) => setForm({ ...form, source_url: e.target.value })}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Author
            </label>
            <input
              type="text"
              value={form.author}
              onChange={(e) => setForm({ ...form, author: e.target.value })}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMut.isPending || !form.title.trim() || !form.content.trim() || !selectedSource}
              className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createMut.isPending ? 'Submitting...' : 'Submit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Start Collection Modal
// ---------------------------------------------------------------------------

function StartCollectionModal({ onClose }: { onClose: () => void }) {
  const [sourceId, setSourceId] = useState('');
  const queryClient = useQueryClient();

  const sourcesQ = useQuery({
    queryKey: ['sources'],
    queryFn: fetchSources,
  });

  const startMut = useMutation({
    mutationFn: () => createCollectionJob({ source_id: sourceId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collectionJobs'] });
      toast.success('Collection job started');
      onClose();
    },
    onError: () => toast.error('Failed to start collection'),
  });

  const sources = (sourcesQ.data ?? []).filter((s) => s.is_active);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm mx-4 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Start Collection
        </h3>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Select Source
          </label>
          <select
            value={sourceId}
            onChange={(e) => setSourceId(e.target.value)}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
          >
            <option value="">Choose a source...</option>
            {sources.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => startMut.mutate()}
            disabled={!sourceId || startMut.isPending}
            className="px-4 py-2 text-sm rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
          >
            {startMut.isPending ? 'Starting...' : 'Start'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

const CollectionDashboard: React.FC = () => {
  const [showAddSource, setShowAddSource] = useState(false);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [showStartCollection, setShowStartCollection] = useState(false);
  const queryClient = useQueryClient();

  const sourcesQ = useQuery({
    queryKey: ['sources'],
    queryFn: fetchSources,
  });

  const jobsQ = useQuery({
    queryKey: ['collectionJobs'],
    queryFn: fetchCollectionJobs,
    refetchInterval: 10000,
  });

  const statsQ = useQuery({
    queryKey: ['collectionStats'],
    queryFn: fetchCollectionStats,
  });

  const toggleMut = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      updateSource(id, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
  });

  const deleteMut = useMutation({
    mutationFn: deleteSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      toast.success('Source deleted');
    },
    onError: () => toast.error('Failed to delete source'),
  });

  const sources = sourcesQ.data ?? [];
  const jobs = jobsQ.data ?? [];
  const stats = statsQ.data;

  function formatDuration(startedAt: string | null, completedAt: string | null): string {
    if (!startedAt) return '-';
    const start = new Date(startedAt).getTime();
    const end = completedAt ? new Date(completedAt).getTime() : Date.now();
    const seconds = Math.round((end - start) / 1000);
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Data Collection
        </h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setShowManualEntry(true)}
            className="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Manual Entry
          </button>
          <button
            type="button"
            onClick={() => setShowAddSource(true)}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            + Add Source
          </button>
        </div>
      </div>

      {/* Collection Stats */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
            <p className="text-sm text-gray-500 dark:text-gray-400">Today</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {stats.today}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
            <p className="text-sm text-gray-500 dark:text-gray-400">This Week</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {stats.this_week}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
            <p className="text-sm text-gray-500 dark:text-gray-400">This Month</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {stats.this_month}
            </p>
          </div>
        </div>
      )}

      {/* Sources Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Active Sources
        </h2>
        {sourcesQ.isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="animate-pulse h-12 bg-gray-100 dark:bg-gray-700 rounded" />
            ))}
          </div>
        ) : sources.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">
            No sources configured. Add one to get started.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-3 font-medium text-gray-500 dark:text-gray-400">
                    Name
                  </th>
                  <th className="text-left py-3 px-3 font-medium text-gray-500 dark:text-gray-400">
                    Type
                  </th>
                  <th className="text-left py-3 px-3 font-medium text-gray-500 dark:text-gray-400 hidden md:table-cell">
                    URL
                  </th>
                  <th className="text-center py-3 px-3 font-medium text-gray-500 dark:text-gray-400">
                    Status
                  </th>
                  <th className="text-left py-3 px-3 font-medium text-gray-500 dark:text-gray-400 hidden lg:table-cell">
                    Created
                  </th>
                  <th className="text-right py-3 px-3 font-medium text-gray-500 dark:text-gray-400">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {sources.map((src) => (
                  <tr
                    key={src.id}
                    className="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30"
                  >
                    <td className="py-3 px-3 font-medium text-gray-900 dark:text-white">
                      {src.name}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${sourceTypeBadge(src.source_type)}`}
                      >
                        {src.source_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-gray-500 dark:text-gray-400 hidden md:table-cell truncate max-w-[200px]">
                      {src.url ? (
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          {src.url}
                        </a>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <button
                        type="button"
                        onClick={() =>
                          toggleMut.mutate({
                            id: src.id,
                            is_active: !src.is_active,
                          })
                        }
                        className={clsx(
                          'relative inline-flex h-5 w-9 rounded-full transition-colors',
                          src.is_active
                            ? 'bg-green-500'
                            : 'bg-gray-300 dark:bg-gray-600'
                        )}
                      >
                        <span
                          className={clsx(
                            'inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform mt-0.5',
                            src.is_active
                              ? 'translate-x-4.5 ml-0.5'
                              : 'translate-x-0.5'
                          )}
                          style={{
                            transform: src.is_active
                              ? 'translateX(18px)'
                              : 'translateX(2px)',
                          }}
                        />
                      </button>
                    </td>
                    <td className="py-3 px-3 text-gray-400 hidden lg:table-cell">
                      {new Date(src.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        type="button"
                        onClick={() => {
                          if (window.confirm(`Delete source "${src.name}"?`)) {
                            deleteMut.mutate(src.id);
                          }
                        }}
                        className="text-red-400 hover:text-red-600 text-xs"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Collection Jobs */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Collection Jobs
          </h2>
          <button
            type="button"
            onClick={() => setShowStartCollection(true)}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-green-600 text-white hover:bg-green-700"
          >
            Start Collection
          </button>
        </div>
        {jobsQ.isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="animate-pulse h-12 bg-gray-100 dark:bg-gray-700 rounded" />
            ))}
          </div>
        ) : jobs.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">
            No collection jobs yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-3 font-medium text-gray-500 dark:text-gray-400">
                    Source
                  </th>
                  <th className="text-left py-3 px-3 font-medium text-gray-500 dark:text-gray-400">
                    Started
                  </th>
                  <th className="text-center py-3 px-3 font-medium text-gray-500 dark:text-gray-400">
                    Status
                  </th>
                  <th className="text-right py-3 px-3 font-medium text-gray-500 dark:text-gray-400">
                    Items
                  </th>
                  <th className="text-right py-3 px-3 font-medium text-gray-500 dark:text-gray-400 hidden sm:table-cell">
                    Duration
                  </th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => {
                  const src = sources.find((s) => s.id === job.source_id);
                  return (
                    <tr
                      key={job.id}
                      className="border-b border-gray-100 dark:border-gray-700/50"
                    >
                      <td className="py-3 px-3 font-medium text-gray-900 dark:text-white">
                        {src?.name ?? job.source_id.slice(0, 8) + '...'}
                      </td>
                      <td className="py-3 px-3 text-gray-500 dark:text-gray-400">
                        {job.started_at
                          ? new Date(job.started_at).toLocaleString()
                          : 'Pending'}
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${statusBadgeClass(job.status)}`}
                        >
                          {job.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right text-gray-600 dark:text-gray-300">
                        {job.items_collected}
                      </td>
                      <td className="py-3 px-3 text-right text-gray-400 hidden sm:table-cell">
                        {formatDuration(job.started_at, job.completed_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        <p className="text-xs text-gray-400 mt-3">
          Auto-refreshes every 10 seconds.
        </p>
      </div>

      {/* Modals */}
      {showAddSource && <AddSourceModal onClose={() => setShowAddSource(false)} />}
      {showManualEntry && <ManualEntryModal onClose={() => setShowManualEntry(false)} />}
      {showStartCollection && (
        <StartCollectionModal onClose={() => setShowStartCollection(false)} />
      )}
    </div>
  );
};

export default CollectionDashboard;
