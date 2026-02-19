import React from 'react';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import { fetchThemes } from '../api/endpoints';

interface TagPillsProps {
  activeIds: string[];
  onToggle: (id: string) => void;
}

const TagPills: React.FC<TagPillsProps> = ({ activeIds, onToggle }) => {
  const { data: themes, isLoading } = useQuery({
    queryKey: ['themes'],
    queryFn: fetchThemes,
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading || !themes?.length) return null;

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {themes.map((theme) => {
        const active = activeIds.includes(theme.id);
        return (
          <button
            key={theme.id}
            type="button"
            onClick={() => onToggle(theme.id)}
            className={clsx(
              'inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-colors',
              active
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600',
            )}
          >
            {theme.name}
          </button>
        );
      })}
    </div>
  );
};

export default TagPills;
