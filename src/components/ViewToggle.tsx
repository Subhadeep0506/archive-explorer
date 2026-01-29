import { Grid3X3, List } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ViewMode } from '@/types/paper';
import { cn } from '@/lib/utils';

interface ViewToggleProps {
  mode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
}

export function ViewToggle({ mode, onModeChange }: ViewToggleProps) {
  return (
    <div className="inline-flex items-center rounded-lg border bg-muted p-1">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onModeChange('grid')}
        className={cn(
          'h-8 px-3 rounded-md',
          mode === 'grid' && 'bg-background shadow-sm'
        )}
      >
        <Grid3X3 className="w-4 h-4 mr-2" />
        Grid
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onModeChange('detailed')}
        className={cn(
          'h-8 px-3 rounded-md',
          mode === 'detailed' && 'bg-background shadow-sm'
        )}
      >
        <List className="w-4 h-4 mr-2" />
        Detailed
      </Button>
    </div>
  );
}
