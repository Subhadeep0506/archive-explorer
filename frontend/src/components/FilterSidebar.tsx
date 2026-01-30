import { FilterChip } from './FilterChip';
import { FilterOption, Filters } from '@/types/paper';
import { ChevronDown, ChevronRight, X } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface FilterSectionProps {
  title: string;
  options: FilterOption[];
  selectedIds: string[];
  onToggle: (id: string) => void;
  defaultOpen?: boolean;
}

function FilterSection({ title, options, selectedIds, onToggle, defaultOpen = true }: FilterSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border-b border-border/50 pb-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full py-2 text-sm font-semibold text-foreground hover:text-primary transition-colors"
      >
        <span>{title}</span>
        {isOpen ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
      </button>
      <div
        className={cn(
          'flex flex-wrap gap-2 overflow-hidden transition-all duration-300',
          isOpen ? 'max-h-96 opacity-100 mt-3' : 'max-h-0 opacity-0'
        )}
      >
        {options.map((option) => (
          <FilterChip
            key={option.id}
            label={option.label}
            count={option.count}
            color={option.color}
            isSelected={selectedIds.includes(option.id)}
            onClick={() => onToggle(option.id)}
          />
        ))}
      </div>
    </div>
  );
}

interface FilterSidebarProps {
  topicFilters: FilterOption[];
  countryFilters: FilterOption[];
  institutionFilters: FilterOption[];
  yearFilters: FilterOption[];
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
}

export function FilterSidebar({
  topicFilters,
  countryFilters,
  institutionFilters,
  yearFilters,
  filters,
  onFiltersChange,
}: FilterSidebarProps) {
  const hasActiveFilters =
    filters.topics.length > 0 ||
    filters.countries.length > 0 ||
    filters.institutions.length > 0 ||
    filters.years.length > 0;

  const handleToggle = (category: keyof Filters, id: string) => {
    const current = filters[category];
    const updated = current.includes(id)
      ? current.filter((item) => item !== id)
      : [...current, id];
    onFiltersChange({ ...filters, [category]: updated });
  };

  const clearFilters = () => {
    onFiltersChange({
      topics: [],
      countries: [],
      institutions: [],
      years: [],
    });
  };

  return (
    <aside className="w-72 flex-shrink-0 border-r bg-sidebar p-5 overflow-y-auto scrollbar-thin">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-bold">Filters</h2>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="text-xs h-7 px-2 text-muted-foreground hover:text-destructive"
          >
            <X className="w-3 h-3 mr-1" />
            Clear all
          </Button>
        )}
      </div>

      <div className="space-y-4">
        <FilterSection
          title="Topics"
          options={topicFilters}
          selectedIds={filters.topics}
          onToggle={(id) => handleToggle('topics', id)}
        />
        <FilterSection
          title="Country"
          options={countryFilters}
          selectedIds={filters.countries}
          onToggle={(id) => handleToggle('countries', id)}
        />
        <FilterSection
          title="Institution"
          options={institutionFilters}
          selectedIds={filters.institutions}
          onToggle={(id) => handleToggle('institutions', id)}
        />
        <FilterSection
          title="Year"
          options={yearFilters}
          selectedIds={filters.years}
          onToggle={(id) => handleToggle('years', id)}
          defaultOpen={false}
        />
      </div>
    </aside>
  );
}
