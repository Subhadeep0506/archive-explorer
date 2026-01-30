import { ChatConversation } from '@/types/chat';
import { MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';
import { PdfPreviewDialog } from './PdfPreviewDialog';
import { Button } from '@/components/ui/button';
import { FileText } from 'lucide-react';

interface ChatHistoryItemProps {
  conversation: ChatConversation;
  isActive: boolean;
  onClick: () => void;
}

export function ChatHistoryItem({
  conversation,
  isActive,
  onClick,
}: ChatHistoryItemProps) {
  const formattedDate = new Date(conversation.lastUpdated).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });

  return (
    <div
      onClick={onClick}
      className={cn(
        'group px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200',
        'hover:bg-accent/80',
        isActive 
          ? 'bg-primary/10 border-l-2 border-l-primary shadow-sm' 
          : 'bg-transparent border-l-2 border-l-transparent'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h4 className={cn(
            "font-medium text-sm truncate",
            isActive ? "text-primary" : "text-foreground"
          )}>
            {conversation.title}
          </h4>
          <p className="text-xs text-muted-foreground mt-0.5 truncate">
            {conversation.paperTitle}
          </p>
          <div className="flex items-center gap-2 mt-1.5 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <MessageSquare className="w-3 h-3" />
              {conversation.messages.length}
            </span>
            <span>•</span>
            <span>{formattedDate}</span>
          </div>
        </div>
        <PdfPreviewDialog pdfUrl={conversation.pdfUrl}>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
            onClick={(e) => e.stopPropagation()}
          >
            <FileText className="w-4 h-4 text-chip-coral" />
          </Button>
        </PdfPreviewDialog>
      </div>
    </div>
  );
}
