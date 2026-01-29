import { cn } from '@/lib/utils';

interface FilterChipProps {
  label: string;
  count: number;
  color: 'coral' | 'teal' | 'amber' | 'violet' | 'emerald' | 'blue' | 'rose';
  isSelected?: boolean;
  onClick?: () => void;
}

const colorStyles = {
  coral: {
    base: 'bg-chip-coral-bg text-chip-coral border-chip-coral/20',
    selected: 'bg-chip-coral text-white border-chip-coral',
  },
  teal: {
    base: 'bg-chip-teal-bg text-chip-teal border-chip-teal/20',
    selected: 'bg-chip-teal text-white border-chip-teal',
  },
  amber: {
    base: 'bg-chip-amber-bg text-chip-amber border-chip-amber/20',
    selected: 'bg-chip-amber text-white border-chip-amber',
  },
  violet: {
    base: 'bg-chip-violet-bg text-chip-violet border-chip-violet/20',
    selected: 'bg-chip-violet text-white border-chip-violet',
  },
  emerald: {
    base: 'bg-chip-emerald-bg text-chip-emerald border-chip-emerald/20',
    selected: 'bg-chip-emerald text-white border-chip-emerald',
  },
  blue: {
    base: 'bg-chip-blue-bg text-chip-blue border-chip-blue/20',
    selected: 'bg-chip-blue text-white border-chip-blue',
  },
  rose: {
    base: 'bg-chip-rose-bg text-chip-rose border-chip-rose/20',
    selected: 'bg-chip-rose text-white border-chip-rose',
  },
};

export function FilterChip({ label, count, color, isSelected = false, onClick }: FilterChipProps) {
  const styles = colorStyles[color];

  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium border transition-all duration-200',
        'hover:scale-105 hover:shadow-sm active:scale-100',
        isSelected ? styles.selected : styles.base
      )}
    >
      <span className="truncate max-w-[120px]">{label}</span>
      <span
        className={cn(
          'inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full text-xs font-semibold',
          isSelected ? 'bg-white/20' : 'bg-current/10'
        )}
      >
        {count}
      </span>
    </button>
  );
}
