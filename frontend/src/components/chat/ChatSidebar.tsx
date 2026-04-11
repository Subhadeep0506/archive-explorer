import { Plus, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatConversation } from "@/types/chat";
import { ChatHistoryItem } from "./ChatHistoryItem";
import { UserProfilePopover } from "./UserProfilePopover";
import { Skeleton } from "@/components/ui/skeleton";

interface ChatSidebarProps {
  conversations: ChatConversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onDeleteConversation: (id: string) => Promise<void> | void;
  onRenameConversation: (id: string, title: string) => Promise<void> | void;
  deletingConversationId?: string | null;
  renamingConversationId?: string | null;
  isLoadingSessions?: boolean;
  isCreatingSession?: boolean;
}

export function ChatSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  onRenameConversation,
  deletingConversationId = null,
  renamingConversationId = null,
  isLoadingSessions = false,
  isCreatingSession = false,
}: ChatSidebarProps) {
  return (
    <div className="min-w-0 bg-sidebar flex flex-col h-full w-full">
      <div className="p-3 ">
        <Button
          onClick={onNewChat}
          className="w-full bg-primary hover:bg-primary/90"
          disabled={isCreatingSession}
        >
          {isCreatingSession ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Plus className="w-4 h-4 mr-2" />
          )}
          New Chat
        </Button>
      </div>

      <ScrollArea className="flex-1 py-2 min-w-0">
        <div className="space-y-1 px-3 overflow-hidden min-w-0">
          {isLoadingSessions ? (
            <div className="space-y-2">
              <Skeleton className="h-20 w-full rounded-md" />
              <Skeleton className="h-20 w-full rounded-md" />
              <Skeleton className="h-20 w-full rounded-md" />
            </div>
          ) : conversations.length === 0 ? (
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
                onDelete={() => onDeleteConversation(conv.id)}
                onRename={(title) => onRenameConversation(conv.id, title)}
                isDeleting={deletingConversationId === conv.id}
                isRenaming={renamingConversationId === conv.id}
              />
            ))
          )}
        </div>
      </ScrollArea>

      <div className="p-3">
        <UserProfilePopover />
      </div>
    </div>
  );
}
