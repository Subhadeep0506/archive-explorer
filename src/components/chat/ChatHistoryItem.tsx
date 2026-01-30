import { ChatConversation } from '@/types/chat';
import { FileText, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ChatHistoryItemProps {
  conversation: ChatConversation;
  isActive: boolean;
  onClick: () => void;
  onOpenPdf: (e: React.MouseEvent) => void;
}

export function ChatHistoryItem({
  conversation,
  isActive,
  onClick,
  onOpenPdf,
}: ChatHistoryItemProps) {
  const formattedDate = new Date(conversation.lastUpdated).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });

  return (
    <div
      onClick={onClick}
      className={cn(
        'group p-3 rounded-lg cursor-pointer transition-all duration-200',
        'hover:bg-accent/80',
        isActive ? 'bg-accent border border-primary/20' : 'bg-transparent'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm truncate text-foreground">
            {conversation.title}
          </h4>
          <p className="text-xs text-muted-foreground mt-1 truncate">
            {conversation.paperTitle}
          </p>
          <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <MessageSquare className="w-3 h-3" />
              {conversation.messages.length}
            </span>
            <span>{formattedDate}</span>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
          onClick={onOpenPdf}
        >
          <FileText className="w-4 h-4 text-chip-coral" />
        </Button>
      </div>
    </div>
  );
}
