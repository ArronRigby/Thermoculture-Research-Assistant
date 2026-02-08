import clsx from 'clsx';

interface PaginationProps {
  page: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
}

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

export default function Pagination({
  page,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: PaginationProps) {
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalItems);

  /** Build the list of page numbers to show (with ellipsis). */
  function getPageNumbers(): (number | '...')[] {
    const pages: (number | '...')[] = [];
    const maxVisible = 7;

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      // Always show first page
      pages.push(1);

      if (page > 3) pages.push('...');

      const rangeStart = Math.max(2, page - 1);
      const rangeEnd = Math.min(totalPages - 1, page + 1);
      for (let i = rangeStart; i <= rangeEnd; i++) pages.push(i);

      if (page < totalPages - 2) pages.push('...');

      // Always show last page
      pages.push(totalPages);
    }

    return pages;
  }

  if (totalItems === 0) {
    return null;
  }

  return (
    <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
      {/* Items info */}
      <p className="text-sm text-gray-600">
        Showing{' '}
        <span className="font-medium text-gray-900">{start}</span>
        {' - '}
        <span className="font-medium text-gray-900">{end}</span>
        {' of '}
        <span className="font-medium text-gray-900">{totalItems}</span>
        {' results'}
      </p>

      {/* Page buttons */}
      <nav className="flex items-center gap-1" aria-label="Pagination">
        {/* Previous */}
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className={clsx(
            'rounded-md border px-3 py-1.5 text-sm font-medium transition-colors',
            page <= 1
              ? 'cursor-not-allowed border-gray-200 bg-gray-50 text-gray-300'
              : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
          )}
        >
          Previous
        </button>

        {/* Page numbers */}
        {getPageNumbers().map((p, idx) =>
          p === '...' ? (
            <span
              key={`ellipsis-${idx}`}
              className="px-2 py-1.5 text-sm text-gray-400"
            >
              ...
            </span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={clsx(
                'min-w-[36px] rounded-md border px-2 py-1.5 text-sm font-medium transition-colors',
                p === page
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
              )}
            >
              {p}
            </button>
          ),
        )}

        {/* Next */}
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className={clsx(
            'rounded-md border px-3 py-1.5 text-sm font-medium transition-colors',
            page >= totalPages
              ? 'cursor-not-allowed border-gray-200 bg-gray-50 text-gray-300'
              : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
          )}
        >
          Next
        </button>
      </nav>

      {/* Page size selector */}
      {onPageSizeChange && (
        <div className="flex items-center gap-2">
          <label
            htmlFor="page-size"
            className="text-sm text-gray-600"
          >
            Per page:
          </label>
          <select
            id="page-size"
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="rounded-md border border-gray-300 py-1 pl-2 pr-7 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
