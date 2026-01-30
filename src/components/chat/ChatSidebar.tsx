import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChatConversation } from '@/types/chat';
import { ChatHistoryItem } from './ChatHistoryItem';

interface ChatSidebarProps {
  conversations: ChatConversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onOpenPdf: (url: string) => void;
}

export function ChatSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onOpenPdf,
}: ChatSidebarProps) {
  return (
    <div className="w-72 border-r bg-sidebar-background flex flex-col h-full">
      <div className="p-4 border-b">
        <Button 
          onClick={onNewChat} 
          className="w-full bg-primary hover:bg-primary/90"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Chat
        </Button>
      </div>

      <ScrollArea className="flex-1 p-3">
        <div className="space-y-2">
          {conversations.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              No conversations yet
            </div>
          ) : (
            conversations.map((conv) => (
              <ChatHistoryItem
                key={conv.id}
                conversation={conv}
                isActive={conv.id === activeConversationId}
                onClick={() => onSelectConversation(conv.id)}
                onOpenPdf={(e) => {
                  e.stopPropagation();
                  onOpenPdf(conv.pdfUrl);
                }}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
