import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';
import {
  fetchNotes,
  fetchNoteDetail,
  createNote,
  updateNote,
  deleteNote,
  linkSampleToNote,
  unlinkSampleFromNote,
  fetchSamples,
  fetchSavedQuotes,
  deleteQuote,
} from '../api/endpoints';
import type {
  DiscourseSampleResponse,
} from '../types';

// ---------------------------------------------------------------------------
// Link Sample Modal
// ---------------------------------------------------------------------------

function LinkSampleModal({
  noteId,
  onClose,
}: {
  noteId: string;
  onClose: () => void;
}) {
  const [search, setSearch] = useState('');
  const queryClient = useQueryClient();

  const samplesQ = useQuery({
    queryKey: ['samples', 'linkModal', search],
    queryFn: () =>
      fetchSamples({
        search_query: search || undefined,
        page: 1,
        page_size: 10,
      }),
  });

  const linkMut = useMutation({
    mutationFn: (sampleId: string) => linkSampleToNote(noteId, sampleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['noteDetail', noteId] });
      onClose();
    },
  });

  const samples = samplesQ.data?.items ?? [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold text-gray-900 dark:text-white">
            Link Discourse Sample
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
        <div className="px-5 py-3">
          <input
            type="text"
            placeholder="Search samples..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
          />
        </div>
        <div className="flex-1 overflow-y-auto px-5 pb-5">
          {samplesQ.isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="animate-pulse h-12 bg-gray-100 dark:bg-gray-700 rounded" />
              ))}
            </div>
          ) : samples.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-8">
              No samples found.
            </p>
          ) : (
            <div className="space-y-2">
              {samples.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => linkMut.mutate(s.id)}
                  disabled={linkMut.isPending}
                  className="w-full text-left rounded-lg border border-gray-200 dark:border-gray-600 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <p className="text-sm font-medium text-gray-900 dark:text-white line-clamp-1">
                    {s.title}
                  </p>
                  <p className="text-xs text-gray-400 line-clamp-1 mt-0.5">
                    {s.content.slice(0, 100)}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Note Editor
// ---------------------------------------------------------------------------

function NoteEditor({
  noteId,
  onDeleted,
}: {
  noteId: string | null;
  onDeleted: () => void;
}) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [preview, setPreview] = useState(false);
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  const detailQ = useQuery({
    queryKey: ['noteDetail', noteId],
    queryFn: () => fetchNoteDetail(noteId!),
    enabled: !!noteId,
  });

  useEffect(() => {
    if (detailQ.data) {
      setTitle(detailQ.data.title);
      setContent(detailQ.data.content);
      setLastSaved(new Date(detailQ.data.updated_at));
    }
  }, [detailQ.data]);

  useEffect(() => {
    if (!noteId) {
      setTitle('');
      setContent('');
      setLastSaved(null);
    }
  }, [noteId]);

  const saveMut = useMutation({
    mutationFn: () => {
      if (noteId) {
        return updateNote(noteId, { title, content });
      }
      return createNote({ title, content });
    },
    onSuccess: () => {
      setLastSaved(new Date());
      queryClient.invalidateQueries({ queryKey: ['notes'] });
      if (noteId) {
        queryClient.invalidateQueries({ queryKey: ['noteDetail', noteId] });
      }
    },
  });

  const deleteMut = useMutation({
    mutationFn: () => deleteNote(noteId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
      onDeleted();
    },
  });

  const unlinkMut = useMutation({
    mutationFn: (sampleId: string) => unlinkSampleFromNote(noteId!, sampleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['noteDetail', noteId] });
    },
  });

  const linkedSamples: DiscourseSampleResponse[] =
    detailQ.data?.discourse_samples ?? [];

  return (
    <div className="flex flex-col h-full">
      {/* Title */}
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Note title..."
        className="text-xl font-semibold bg-transparent border-0 border-b border-gray-200 dark:border-gray-700 px-0 py-3 text-gray-900 dark:text-white focus:outline-none focus:ring-0 focus:border-blue-500 w-full"
      />

      {/* Toolbar */}
      <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setPreview(false)}
            className={clsx(
              'px-3 py-1 text-xs rounded-lg font-medium',
              !preview
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
            )}
          >
            Edit
          </button>
          <button
            type="button"
            onClick={() => setPreview(true)}
            className={clsx(
              'px-3 py-1 text-xs rounded-lg font-medium',
              preview
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
            )}
          >
            Preview
          </button>
        </div>
        {lastSaved && (
          <span className="text-xs text-gray-400">
            Last saved: {lastSaved.toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Editor / Preview */}
      <div className="flex-1 overflow-y-auto py-3">
        {preview ? (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown>{content || '*No content yet...*'}</ReactMarkdown>
          </div>
        ) : (
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write your research notes in Markdown..."
            className="w-full h-full min-h-[300px] bg-transparent border-0 text-sm text-gray-700 dark:text-gray-300 resize-none focus:outline-none focus:ring-0 font-mono"
          />
        )}
      </div>

      {/* Linked samples */}
      {noteId && (
        <div className="border-t border-gray-200 dark:border-gray-700 pt-3 mt-2">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Linked Samples ({linkedSamples.length})
            </h4>
            <button
              type="button"
              onClick={() => setShowLinkModal(true)}
              className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
            >
              + Link Sample
            </button>
          </div>
          {linkedSamples.length > 0 && (
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {linkedSamples.map((s) => (
                <div
                  key={s.id}
                  className="flex items-center justify-between text-sm bg-gray-50 dark:bg-gray-700/50 rounded-lg px-3 py-2"
                >
                  <span className="text-gray-700 dark:text-gray-300 line-clamp-1 flex-1">
                    {s.title}
                  </span>
                  <button
                    type="button"
                    onClick={() => unlinkMut.mutate(s.id)}
                    className="text-red-400 hover:text-red-600 ml-2 shrink-0"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3 border-t border-gray-200 dark:border-gray-700 pt-3 mt-3">
        <button
          type="button"
          onClick={() => saveMut.mutate()}
          disabled={saveMut.isPending || !title.trim()}
          className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saveMut.isPending ? 'Saving...' : 'Save'}
        </button>
        {noteId && (
          <button
            type="button"
            onClick={() => {
              if (window.confirm('Delete this note?')) {
                deleteMut.mutate();
              }
            }}
            disabled={deleteMut.isPending}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/40 dark:text-red-300"
          >
            {deleteMut.isPending ? 'Deleting...' : 'Delete'}
          </button>
        )}
      </div>

      {showLinkModal && noteId && (
        <LinkSampleModal
          noteId={noteId}
          onClose={() => setShowLinkModal(false)}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quote Library
// ---------------------------------------------------------------------------

function QuoteLibrary() {
  const [search, setSearch] = useState('');

  const quotesQ = useQuery({
    queryKey: ['savedQuotes'],
    queryFn: fetchSavedQuotes,
  });

  const queryClient = useQueryClient();
  const delMut = useMutation({
    mutationFn: deleteQuote,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['savedQuotes'] }),
  });

  const allQuotes = quotesQ.data ?? [];
  const filtered = search
    ? allQuotes.filter(
        (q) =>
          q.text.toLowerCase().includes(search.toLowerCase()) ||
          q.source_name.toLowerCase().includes(search.toLowerCase())
      )
    : allQuotes;

  async function handleExportQuotes() {
    const blob = new Blob(
      [JSON.stringify(filtered, null, 2)],
      { type: 'application/json' }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quotes-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search quotes..."
          className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
        />
        <button
          type="button"
          onClick={handleExportQuotes}
          className="px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          Export
        </button>
      </div>

      {quotesQ.isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="animate-pulse h-20 bg-gray-100 dark:bg-gray-700 rounded-lg" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-400 text-sm">No saved quotes yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((q) => (
            <div
              key={q.id}
              className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4"
            >
              <p className="text-sm text-gray-700 dark:text-gray-300 italic mb-2">
                "{q.text}"
              </p>
              <div className="flex items-center justify-between">
                <div className="text-xs text-gray-400">
                  <span className="font-medium">{q.source_name}</span>
                  {q.author && <span> -- {q.author}</span>}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(q.citation)}
                    className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
                  >
                    Copy Citation
                  </button>
                  <button
                    type="button"
                    onClick={() => delMut.mutate(q.id)}
                    className="text-xs text-red-400 hover:text-red-600"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

const ResearchWorkspace: React.FC = () => {
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null);
  const [noteSearch, setNoteSearch] = useState('');
  const [activeTab, setActiveTab] = useState<'notes' | 'quotes'>('notes');
  const queryClient = useQueryClient();

  const notesQ = useQuery({
    queryKey: ['notes'],
    queryFn: fetchNotes,
  });

  const createMut = useMutation({
    mutationFn: () => createNote({ title: 'Untitled Note', content: '' }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
      setSelectedNoteId(data.id);
    },
  });

  const allNotes = notesQ.data ?? [];
  const filteredNotes = noteSearch
    ? allNotes.filter((n) =>
        n.title.toLowerCase().includes(noteSearch.toLowerCase())
      )
    : allNotes;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Research Workspace
        </h1>
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5">
          <button
            type="button"
            onClick={() => setActiveTab('notes')}
            className={clsx(
              'px-4 py-1.5 text-sm font-medium rounded-md transition-colors',
              activeTab === 'notes'
                ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-500 dark:text-gray-400'
            )}
          >
            Notes
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('quotes')}
            className={clsx(
              'px-4 py-1.5 text-sm font-medium rounded-md transition-colors',
              activeTab === 'quotes'
                ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-500 dark:text-gray-400'
            )}
          >
            Quote Library
          </button>
        </div>
      </div>

      {activeTab === 'quotes' ? (
        <QuoteLibrary />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6" style={{ minHeight: '70vh' }}>
          {/* Note list */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 flex flex-col">
            <div className="flex items-center gap-2 mb-3">
              <input
                type="text"
                value={noteSearch}
                onChange={(e) => setNoteSearch(e.target.value)}
                placeholder="Search notes..."
                className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-700 dark:text-gray-200"
              />
              <button
                type="button"
                onClick={() => createMut.mutate()}
                disabled={createMut.isPending}
                className="shrink-0 px-3 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
              >
                + New
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2">
              {notesQ.isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="animate-pulse h-16 bg-gray-100 dark:bg-gray-700 rounded-lg" />
                ))
              ) : filteredNotes.length === 0 ? (
                <p className="text-gray-400 text-sm text-center py-8">
                  No notes yet. Create one!
                </p>
              ) : (
                filteredNotes.map((note) => (
                  <button
                    key={note.id}
                    type="button"
                    onClick={() => setSelectedNoteId(note.id)}
                    className={clsx(
                      'w-full text-left rounded-lg p-3 transition-colors border',
                      selectedNoteId === note.id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400'
                        : 'border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                    )}
                  >
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white line-clamp-1">
                      {note.title}
                    </h4>
                    <p className="text-xs text-gray-400 line-clamp-1 mt-0.5">
                      {note.content.slice(0, 80) || 'Empty note'}
                    </p>
                    <p className="text-[10px] text-gray-300 dark:text-gray-600 mt-1">
                      {new Date(note.updated_at).toLocaleDateString()}
                    </p>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Editor */}
          <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 flex flex-col">
            {selectedNoteId || !notesQ.data?.length ? (
              <NoteEditor
                noteId={selectedNoteId}
                onDeleted={() => setSelectedNoteId(null)}
              />
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <svg
                    className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  <p className="text-gray-400 text-sm">
                    Select a note to edit or create a new one.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResearchWorkspace;
