# feat/tags-and-trends Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Surface existing NLP theme tags throughout the UI and add a `/trends` page showing theme trends, sentiment over time, and recent articles.

**Architecture:** Frontend-only work. All backend analysis endpoints already exist. Uses TanStack React Query for data fetching, Recharts for charts (already installed). No new API routes needed.

**Tech Stack:** React 18, TypeScript, TailwindCSS, TanStack React Query, Recharts, React Router

**Pre-requisite:** `fix/foundation` must be merged to master before starting this branch.

---

## Pre-flight

```bash
git checkout master
git pull origin master
git checkout -b feat/tags-and-trends
cd frontend
npm install  # confirm all deps present
npm run dev  # confirm app starts
```

---

### Task 1: Add tag pills above the sample list

**Files:**
- Create: `frontend/src/components/TagPills.tsx`
- Modify: `frontend/src/pages/SamplesPage.tsx` (or wherever the sample list lives — check `src/App.tsx` for the route that renders samples)

**Step 1: Find the samples list page**

```bash
grep -r "SampleCard\|sample.*list\|discourse.*sample" frontend/src --include="*.tsx" -l
```

Note the file that renders the list of samples — this is where TagPills will be inserted above the FilterBar.

**Step 2: Write the component test**

Create `frontend/src/components/__tests__/TagPills.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import TagPills from '../TagPills';

const themes = [
  { id: '1', name: 'Flooding', sample_count: 42 },
  { id: '2', name: 'Policy', sample_count: 18 },
  { id: '3', name: 'Heatwave', sample_count: 7 },
];

test('renders top 15 theme pills with counts', () => {
  render(<TagPills themes={themes} selectedIds={[]} onToggle={() => {}} />);
  expect(screen.getByText('Flooding')).toBeInTheDocument();
  expect(screen.getByText('42')).toBeInTheDocument();
});

test('highlights selected theme', () => {
  render(<TagPills themes={themes} selectedIds={['1']} onToggle={() => {}} />);
  const pill = screen.getByText('Flooding').closest('button');
  expect(pill).toHaveClass('bg-primary-600');
});

test('calls onToggle with theme id when clicked', () => {
  const onToggle = jest.fn();
  render(<TagPills themes={themes} selectedIds={[]} onToggle={onToggle} />);
  fireEvent.click(screen.getByText('Flooding'));
  expect(onToggle).toHaveBeenCalledWith('1');
});

test('shows show-all toggle when more than 15 themes', () => {
  const manyThemes = Array.from({ length: 20 }, (_, i) => ({
    id: String(i),
    name: `Theme ${i}`,
    sample_count: 10 - i,
  }));
  render(<TagPills themes={manyThemes} selectedIds={[]} onToggle={() => {}} />);
  expect(screen.getByText(/show all/i)).toBeInTheDocument();
});
```

**Step 3: Run tests to confirm failure**

```bash
cd frontend
npx vitest run src/components/__tests__/TagPills.test.tsx
```

Expected: FAIL — component doesn't exist yet.

**Step 4: Create `TagPills.tsx`**

```typescript
import { useState } from 'react';
import clsx from 'clsx';

interface Theme {
  id: string;
  name: string;
  sample_count: number;
}

interface TagPillsProps {
  themes: Theme[];
  selectedIds: string[];
  onToggle: (id: string) => void;
}

const VISIBLE_LIMIT = 15;

export default function TagPills({ themes, selectedIds, onToggle }: TagPillsProps) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? themes : themes.slice(0, VISIBLE_LIMIT);

  if (themes.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2 py-3">
      {visible.map((theme) => {
        const active = selectedIds.includes(theme.id);
        return (
          <button
            key={theme.id}
            onClick={() => onToggle(theme.id)}
            className={clsx(
              'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors',
              active
                ? 'border-primary-600 bg-primary-600 text-white'
                : 'border-gray-300 bg-white text-gray-700 hover:border-primary-400 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-600',
            )}
          >
            {theme.name}
            <span
              className={clsx(
                'rounded-full px-1.5 py-0.5 text-[10px] font-semibold',
                active ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
              )}
            >
              {theme.sample_count}
            </span>
          </button>
        );
      })}
      {themes.length > VISIBLE_LIMIT && (
        <button
          onClick={() => setShowAll((prev) => !prev)}
          className="text-xs text-primary-600 hover:underline dark:text-primary-400"
        >
          {showAll ? 'Show fewer' : `Show all ${themes.length}`}
        </button>
      )}
    </div>
  );
}
```

**Step 5: Run tests**

```bash
npx vitest run src/components/__tests__/TagPills.test.tsx
```

Expected: all PASS.

**Step 6: Wire TagPills into the samples page**

In the samples list page, add:

```typescript
import TagPills from '../components/TagPills';
import { useQuery } from '@tanstack/react-query';
import { fetchThemes } from '../api/endpoints';

// Inside the component, fetch themes sorted by count:
const { data: themes = [] } = useQuery({
  queryKey: ['themes'],
  queryFn: fetchThemes,
  staleTime: 10 * 60 * 1000,
});

// Sort themes by sample count descending (if count is available)
// Render above FilterBar:
<TagPills
  themes={themes}
  selectedIds={filters.theme_ids ?? []}
  onToggle={(id) => {
    const current = filters.theme_ids ?? [];
    const next = current.includes(id)
      ? current.filter((t) => t !== id)
      : [...current, id];
    onFiltersChange({ ...filters, theme_ids: next, page: 1 });
  }}
/>
```

**Step 7: Verify in browser**

```bash
npm run dev
```

Navigate to the samples page. Confirm theme pills appear above the filter bar and clicking one filters the list.

**Step 8: Commit**

```bash
git add frontend/src/components/TagPills.tsx frontend/src/components/__tests__/TagPills.test.tsx
git add frontend/src/pages/  # whichever samples page was modified
git commit -m "feat(tags): add clickable tag pills above sample list"
```

---

### Task 2: Add NLP auto-tag indicator to SampleCard and SampleDetail

**Files:**
- Modify: `frontend/src/components/SampleCard.tsx`
- Modify: `frontend/src/pages/SampleDetail.tsx`

NLP-assigned tags must be visually distinguishable from future manually-assigned tags.
Use a small gear icon (⚙) prefix on auto-assigned theme chips.

All themes currently in the DB are NLP-assigned. The `ThemeResponse` schema does
not yet have an `is_auto` field — we use a simple convention: render all current
theme chips with the auto indicator. The distinction matters for future manual tags.

**Step 1: Read SampleCard.tsx and check existing theme rendering**

Open `frontend/src/components/SampleCard.tsx`. Look for how themes are currently
rendered — if they are not shown at all, add them. If they are shown, add the indicator.

**Step 2: Add theme chips to SampleCard**

In `SampleCard.tsx`, add theme chips below the content snippet:

```typescript
{/* Theme chips — show up to 3, with overflow count */}
{sample.themes && sample.themes.length > 0 && (
  <div className="mt-2 flex flex-wrap gap-1">
    {sample.themes.slice(0, 3).map((theme) => (
      <span
        key={theme.id}
        className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-[11px] text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
        title="Auto-assigned by NLP"
      >
        <span className="opacity-60">⚙</span>
        {theme.name}
      </span>
    ))}
    {sample.themes.length > 3 && (
      <span className="text-[11px] text-gray-400">
        +{sample.themes.length - 3} more
      </span>
    )}
  </div>
)}
```

**Step 3: Add theme chips to SampleDetail**

In `SampleDetail.tsx`, in the metadata section, show all themes:

```typescript
{sample.themes && sample.themes.length > 0 && (
  <div className="mt-4">
    <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">
      Themes
    </h3>
    <div className="flex flex-wrap gap-1.5">
      {sample.themes.map((theme) => (
        <span
          key={theme.id}
          className="inline-flex items-center gap-1 rounded-full bg-blue-50 border border-blue-200 px-2.5 py-1 text-xs text-blue-700 dark:bg-blue-900/30 dark:border-blue-700 dark:text-blue-300"
          title="Auto-assigned by NLP analysis"
        >
          <span className="opacity-50 text-[10px]">⚙</span>
          {theme.name}
        </span>
      ))}
    </div>
  </div>
)}
```

**Step 4: Verify in browser**

Navigate to a sample card and its detail page. Confirm theme chips appear with the ⚙ indicator.

**Step 5: Commit**

```bash
git add frontend/src/components/SampleCard.tsx frontend/src/pages/SampleDetail.tsx
git commit -m "feat(tags): show NLP auto-tag chips on SampleCard and SampleDetail"
```

---

### Task 3: Create the Trends page

**Files:**
- Create: `frontend/src/pages/TrendsPage.tsx`
- Modify: `frontend/src/App.tsx` (add `/trends` route)
- Modify: `frontend/src/components/` (navigation — add Trends link)

**Step 1: Check what Recharts components are available**

```bash
grep -r "recharts" frontend/package.json
```

Recharts is already installed. Available components: `BarChart`, `Bar`, `LineChart`,
`Line`, `XAxis`, `YAxis`, `CartesianGrid`, `Tooltip`, `Legend`, `ResponsiveContainer`, `PieChart`, `Pie`, `Cell`.

**Step 2: Check existing API endpoint functions**

```bash
grep -n "analysis\|trending\|sentiment" frontend/src/api/endpoints.ts
```

Note the names of existing functions — e.g. `fetchTrendingThemes`, `fetchSentimentOverTime`,
`fetchThemeFrequency`, `fetchDiscourseTypes`. Use these exact names in the Trends page.

**Step 3: Create `TrendsPage.tsx`**

```typescript
import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import {
  fetchTrendingThemes,
  fetchSentimentOverTime,
  fetchThemeFrequency,
  fetchDiscourseTypes,
  fetchCollectionStats,
  fetchSamples,
} from '../api/endpoints';
import LoadingSpinner from '../components/LoadingSpinner';

// ---------------------------------------------------------------------------
// Provenance bar
// ---------------------------------------------------------------------------

function ProvenanceBar({ totalArticles, lastCollected }: { totalArticles: number; lastCollected: string | null }) {
  return (
    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
      Based on {totalArticles.toLocaleString()} articles
      {lastCollected ? ` · Last collected ${new Date(lastCollected).toLocaleString()}` : ''}
    </p>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function TrendsPage() {
  const queryClient = useQueryClient();

  const trendingQ = useQuery({ queryKey: ['trending-themes'], queryFn: fetchTrendingThemes });
  const sentimentQ = useQuery({ queryKey: ['sentiment-over-time'], queryFn: fetchSentimentOverTime });
  const themeFreqQ = useQuery({ queryKey: ['theme-frequency'], queryFn: fetchThemeFrequency });
  const discourseQ = useQuery({ queryKey: ['discourse-types'], queryFn: fetchDiscourseTypes });
  const statsQ = useQuery({ queryKey: ['collectionStats'], queryFn: fetchCollectionStats });
  const recentQ = useQuery({
    queryKey: ['recent-samples'],
    queryFn: () => fetchSamples({ page: 1, page_size: 20 }),
  });

  const isLoading = trendingQ.isLoading || sentimentQ.isLoading || themeFreqQ.isLoading;

  function handleRefresh() {
    queryClient.invalidateQueries({ queryKey: ['trending-themes'] });
    queryClient.invalidateQueries({ queryKey: ['sentiment-over-time'] });
    queryClient.invalidateQueries({ queryKey: ['theme-frequency'] });
    queryClient.invalidateQueries({ queryKey: ['discourse-types'] });
    queryClient.invalidateQueries({ queryKey: ['collectionStats'] });
    queryClient.invalidateQueries({ queryKey: ['recent-samples'] });
  }

  const topTrend = trendingQ.data?.[0];
  const totalArticles = statsQ.data?.total ?? 0;
  const lastCollected = statsQ.data?.last_collected ?? null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Trends</h1>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          ↻ Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><LoadingSpinner /></div>
      ) : (
        <>
          {/* 1. Headline insight */}
          {topTrend && (
            <div className="rounded-xl bg-primary-600 p-6 text-white">
              <p className="text-sm font-medium opacity-80">Fastest-rising theme this month</p>
              <p className="mt-1 text-3xl font-bold">{topTrend.theme}</p>
              <p className="mt-1 text-sm opacity-70">
                {topTrend.recent_count} articles recently · trend score +{topTrend.trend_score.toFixed(3)}
              </p>
              <ProvenanceBar totalArticles={totalArticles} lastCollected={lastCollected} />
            </div>
          )}

          {/* 2. Trending themes bar chart */}
          <section className="rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">Trending Themes</h2>
            <ProvenanceBar totalArticles={totalArticles} lastCollected={lastCollected} />
            <div className="mt-4 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trendingQ.data?.slice(0, 10) ?? []} layout="vertical" margin={{ left: 80 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="theme" tick={{ fontSize: 11 }} width={80} />
                  <Tooltip />
                  <Bar dataKey="recent_count" name="Recent articles" fill="#4f46e5" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* 3. Sentiment over time */}
          <section className="rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">Sentiment Over Time</h2>
            <ProvenanceBar totalArticles={totalArticles} lastCollected={lastCollected} />
            <div className="mt-4 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sentimentQ.data?.data_points ?? []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis domain={[-1, 1]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="average_sentiment" name="Avg. sentiment" stroke="#4f46e5" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* 4. Discourse type breakdown */}
          <section className="rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">Discourse Types</h2>
            <ProvenanceBar totalArticles={totalArticles} lastCollected={lastCollected} />
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {discourseQ.data?.discourse_types?.map((item: any) => (
                <div key={item.classification_type} className="rounded-lg bg-gray-50 dark:bg-gray-700 p-4 text-center">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{item.count}</p>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 leading-tight">
                    {item.classification_type.replace(/_/g, ' ')}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* 5. Recent articles feed */}
          <section className="rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recently Collected</h2>
            {recentQ.data?.items?.length === 0 ? (
              <p className="text-sm text-gray-400">No articles collected yet.</p>
            ) : (
              <ul className="divide-y divide-gray-100 dark:divide-gray-700">
                {recentQ.data?.items?.map((sample: any) => (
                  <li key={sample.id} className="py-3">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {sample.title}
                        </p>
                        <p className="mt-0.5 text-xs text-gray-400">
                          {sample.source?.name} · {new Date(sample.collected_at).toLocaleDateString()}
                        </p>
                        {sample.themes?.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {sample.themes.slice(0, 4).map((t: any) => (
                              <span key={t.id} className="rounded-full bg-blue-50 dark:bg-blue-900/30 px-2 py-0.5 text-[10px] text-blue-700 dark:text-blue-300">
                                ⚙ {t.name}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
```

**Step 4: Register the route**

In `frontend/src/App.tsx`, add:

```typescript
import TrendsPage from './pages/TrendsPage';

// Inside <Routes>:
<Route path="/trends" element={<TrendsPage />} />
```

**Step 5: Add Trends to navigation**

Find the nav component (check `src/components/` for a `Nav`, `Sidebar`, or `Layout` component). Add:

```typescript
<NavLink to="/trends">Trends</NavLink>
```

**Step 6: Verify in browser**

```bash
npm run dev
```

Navigate to `/trends`. Confirm:
- Headline card shows fastest-rising theme
- Bar chart, line chart, discourse counts render
- Recent articles appear at the bottom
- Refresh button re-fetches all data
- Provenance bar shows article count and timestamp

**Step 7: Commit**

```bash
git add frontend/src/pages/TrendsPage.tsx frontend/src/App.tsx frontend/src/components/
git commit -m "feat(trends): add /trends page with headline insight, charts, and recent articles feed"
```

---

### Task 4: Final check and PR

**Step 1: Run all frontend checks**

```bash
cd frontend
npm run build     # TypeScript compile + bundle — must succeed with 0 errors
npm run lint      # ESLint — must return 0 warnings (max-warnings: 0)
npx vitest run    # All component tests pass
```

**Step 2: Confirm tag filtering works end to end**

1. Open the app, go to the samples page
2. Click a theme pill — sample list filters to that theme
3. Click the same pill again — filter clears
4. Open a sample card — theme chips with ⚙ icon visible
5. Open sample detail — all themes listed with ⚙ icon

**Step 3: Confirm trends page**

1. Navigate to `/trends`
2. All sections render (no blank charts)
3. Provenance bar shows non-zero article count
4. Clicking Refresh triggers a re-fetch (network tab shows new requests)

**Step 4: Raise PR to master**

```bash
git push origin feat/tags-and-trends
gh pr create --title "feat: tags surfacing and /trends page" \
  --body "Surfaces NLP theme tags as clickable pills, adds auto-tag indicators on sample cards, and adds a /trends page with headline insight, charts, and recent articles feed. Closes the tag discoverability gap identified in the board review."
```
