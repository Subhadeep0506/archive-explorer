import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent, MouseEvent } from "react";
import { ChatConversation } from "@/types/chat";
import { MessageSquare, Pencil, Trash2, Check, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface ChatHistoryItemProps {
  conversation: ChatConversation;
  isActive: boolean;
  onClick: () => void;
  onDelete: () => Promise<void> | void;
  onRename: (newTitle: string) => Promise<void> | void;
  isDeleting?: boolean;
  isRenaming?: boolean;
}

export function ChatHistoryItem({
  conversation,
  isActive,
  onClick,
  onDelete,
  onRename,
  isDeleting = false,
  isRenaming = false,
}: ChatHistoryItemProps) {
  const formattedDate = new Date(conversation.lastUpdated).toLocaleDateString(
    "en-US",
    {
      month: "short",
      day: "numeric",
    },
  );

  const [isEditing, setIsEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(conversation.title);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setDraftTitle(conversation.title);
  }, [conversation.title]);

  useEffect(() => {
    if (isEditing) {
      inputRef.current?.focus();
    }
  }, [isEditing]);

  const handleRenameSubmit = async () => {
    const trimmed = draftTitle.trim();
    if (!trimmed) {
      setDraftTitle(conversation.title);
      setIsEditing(false);
      return;
    }

    if (trimmed === conversation.title) {
      setIsEditing(false);
      return;
    }

    try {
      await onRename(trimmed);
      setIsEditing(false);
    } catch (error) {
      // Keep editing so user can adjust the title
      console.error("Failed to rename session", error);
    }
  };

  const handleStartEditing = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    setIsEditing(true);
  };

  const handleCancelEditing = (
    event?: MouseEvent<HTMLButtonElement> | KeyboardEvent<HTMLInputElement>,
  ) => {
    event?.stopPropagation();
    setDraftTitle(conversation.title);
    setIsEditing(false);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      handleRenameSubmit();
    } else if (event.key === "Escape") {
      handleCancelEditing(event);
    }
  };

  const handleDeleteConfirmed = async (
    event: MouseEvent<HTMLButtonElement>,
  ) => {
    event.stopPropagation();
    try {
      await onDelete();
    } catch (error) {
      console.error("Failed to delete session", error);
    }
  };

  return (
    <div
      onClick={onClick}
      className={cn(
        "group px-3 py-2.5 rounded-md cursor-pointer transition-all duration-200 overflow-hidden w-full max-w-full min-w-0",
        "hover:bg-accent/80",
        isActive
          ? "bg-primary/10 border border-primary/20 shadow-sm"
          : "bg-transparent border border-transparent",
      )}
    >
      <div className="flex items-start justify-between gap-2 min-w-0 w-full overflow-hidden">
        <div className="flex-1 min-w-0 overflow-hidden">
          {isEditing ? (
            <Input
              ref={inputRef}
              value={draftTitle}
              onChange={(event) => setDraftTitle(event.target.value)}
              onKeyDown={handleKeyDown}
              onClick={(event) => event.stopPropagation()}
              className="h-7 px-1 text-sm font-medium bg-transparent border-border/40 focus-visible:ring-0 focus-visible:border-primary focus-visible:ring-offset-0 rounded-[8px] border-b"
              aria-label="Edit session title"
            />
          ) : (
            <h4
              className={cn(
                "font-medium text-sm leading-tight break-words overflow-hidden [display:-webkit-box] [-webkit-box-orient:vertical] [-webkit-line-clamp:2]",
                isActive ? "text-primary" : "text-foreground",
              )}
              title={conversation.title}
            >
              {conversation.title}
            </h4>
          )}
          <p
            className="text-xs text-muted-foreground mt-0.5 break-words overflow-hidden [display:-webkit-box] [-webkit-box-orient:vertical] [-webkit-line-clamp:1]"
            title={conversation.paperTitle}
          >
            {conversation.paperTitle}
          </p>
          <div className="flex items-center gap-2 mt-1.5 text-xs text-muted-foreground overflow-hidden">
            <span className="flex items-center gap-1 shrink-0">
              <MessageSquare className="w-3 h-3" />
              {conversation.messages.length}
            </span>
            <span className="shrink-0">•</span>
            <span className="truncate">{formattedDate}</span>
          </div>
        </div>
        <div
          className={cn(
            "flex items-center gap-1 shrink-0",
            isEditing || isDeleting || isRenaming
              ? "opacity-100"
              : "opacity-0 group-hover:opacity-100",
            "transition-opacity",
          )}
        >
          {isEditing ? (
            <>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={(event) => {
                  event.stopPropagation();
                  handleRenameSubmit();
                }}
                disabled={isRenaming}
              >
                {isRenaming ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Check className="w-4 h-4 text-emerald-600" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={(event) => handleCancelEditing(event)}
                disabled={isRenaming}
              >
                <X className="w-4 h-4 text-destructive" />
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={handleStartEditing}
              >
                <Pencil className="w-4 h-4" />
              </Button>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={(event) => event.stopPropagation()}
                    disabled={isDeleting}
                  >
                    {isDeleting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4 text-destructive" />
                    )}
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent
                  onClick={(event) => event.stopPropagation()}
                >
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete chat session</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will permanently remove "{conversation.title}" and
                      its messages.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel
                      onClick={(event) => event.stopPropagation()}
                    >
                      Cancel
                    </AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handleDeleteConfirmed}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      {isDeleting ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4 mr-2" />
                      )}
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
