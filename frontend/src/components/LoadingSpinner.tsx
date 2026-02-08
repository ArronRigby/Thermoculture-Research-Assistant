import clsx from 'clsx';

interface LoadingSpinnerProps {
  /** Optional message to display below the spinner. */
  message?: string;
  /** Size variant. Defaults to 'md'. */
  size?: 'sm' | 'md' | 'lg';
  /** If true, centers the spinner in its container with padding. */
  fullArea?: boolean;
}

const SIZE_CLASSES = {
  sm: 'h-5 w-5 border-2',
  md: 'h-8 w-8 border-[3px]',
  lg: 'h-12 w-12 border-4',
} as const;

export default function LoadingSpinner({
  message,
  size = 'md',
  fullArea = true,
}: LoadingSpinnerProps) {
  const spinner = (
    <div className="flex flex-col items-center gap-3">
      <div
        className={clsx(
          'animate-spin rounded-full border-primary-200 border-t-primary-600',
          SIZE_CLASSES[size],
        )}
        role="status"
        aria-label="Loading"
      />
      {message && (
        <p className="text-sm text-gray-500">{message}</p>
      )}
    </div>
  );

  if (fullArea) {
    return (
      <div className="flex min-h-[200px] items-center justify-center p-8">
        {spinner}
      </div>
    );
  }

  return spinner;
}
