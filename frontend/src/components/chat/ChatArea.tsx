import { useRef, useEffect, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage, StreamingState } from "@/types/chat";
import { ChatMessageBubble } from "./ChatMessageBubble";
import { StreamingUpdate } from "./StreamingUpdate";
import { TypingIndicator } from "./TypingIndicator";
import {
  MessageSquare,
  ChevronDown,
  ChevronRight,
  Settings2,
} from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";

interface ChatAreaProps {
  messages: ChatMessage[];
  paperTitle?: string;
  paperPdfUrl?: string;
  isStreaming?: boolean;
  streamingState?: StreamingState;
  onMessageLike?: (
    messageId: string,
    liked: boolean | null,
  ) => Promise<void> | void;
  onMessageFeedback?: (
    messageId: string,
    feedback: string,
    stars: number,
  ) => Promise<void> | void;
}

export function ChatArea({
  messages,
  paperTitle,
  paperPdfUrl,
  isStreaming = false,
  streamingState,
  onMessageLike,
  onMessageFeedback,
}: ChatAreaProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [isStepsOpen, setIsStepsOpen] = useState(true);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingState]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 h-full flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-chip-violet-bg flex items-center justify-center">
            <MessageSquare className="w-8 h-8 text-chip-violet" />
          </div>
          <h2 className="text-xl font-semibold mb-2">Start a conversation</h2>
          <p className="text-muted-foreground">
            {paperTitle
              ? `Ask questions about "${paperTitle}" and get AI-powered answers based on the paper content.`
              : "Select a conversation from the sidebar or start a new chat."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 h-full">
      <div className="max-w-[70%] mx-auto p-4 pb-48 space-y-4">
        {messages.map((message, index) => {
          const isLastMessage = index === messages.length - 1;
          const isStreamingMessage =
            isStreaming && isLastMessage && message.id === "streaming";

          // Skip rendering the default streaming message if we have streaming state
          if (
            isStreamingMessage &&
            streamingState &&
            streamingState.nodes.length > 0
          ) {
            return null;
          }

          // Skip rendering the last assistant message if we're showing it via streamingState
          if (
            isLastMessage &&
            message.role === "assistant" &&
            streamingState?.finalResponse &&
            message.content === streamingState.finalResponse
          ) {
            return null;
          }

          return (
            <ChatMessageBubble
              key={message.id}
              message={message}
              isStreaming={isStreamingMessage}
              metadata={message.generation_metadata}
              paperPdfUrl={paperPdfUrl}
              onLike={
                onMessageLike
                  ? (liked) => onMessageLike(message.id, liked)
                  : undefined
              }
              onFeedback={
                onMessageFeedback
                  ? (feedback, stars) =>
                      onMessageFeedback(message.id, feedback, stars)
                  : undefined
              }
            />
          );
        })}

        {/* Show streaming updates as timeline */}
        {streamingState && streamingState.nodes.length > 0 && (
          <div className="bg-card/30 overflow-hidden">
            <Collapsible open={isStepsOpen} onOpenChange={setIsStepsOpen}>
              <CollapsibleTrigger className=" rounded-lg flex items-center justify-between w-full px-3 py-2 hover:bg-accent/50 transition-colors">
                <div className="flex items-center gap-1.5 rounded-sm">
                  {isStepsOpen ? (
                    <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />
                  )}
                  <span className="font-medium text-xs flex items-center">
                    <Settings2 className="w-3.5 h-3.5 text-muted-foreground mr-1" />{" "}
                    Processing Steps
                  </span>
                  <Badge
                    variant="secondary"
                    className="text-[10px] px-1 py-0 h-4"
                  >
                    {streamingState.nodes.length}
                  </Badge>
                </div>
                {!isStreaming && (
                  <Badge
                    variant="outline"
                    className="text-[10px] px-1 py-0 h-4 text-green-600 border-green-600"
                  >
                    ✓ Completed
                  </Badge>
                )}
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="px-3 py-2">
                  {streamingState.nodes.map((node, index) => {
                    const isActiveNode =
                      isStreaming &&
                      index === streamingState.nodes.length - 1 &&
                      !streamingState.finalResponse;
                    const isLastNode =
                      index === streamingState.nodes.length - 1;
                    return (
                      <StreamingUpdate
                        key={node.id}
                        node={node}
                        isActive={isActiveNode}
                        isLast={isLastNode}
                      />
                    );
                  })}
                </div>
              </CollapsibleContent>
            </Collapsible>
          </div>
        )}

        {/* Show typing indicator when generating response */}
        {isStreaming && streamingState && !streamingState.finalResponse && (
          <TypingIndicator />
        )}

        {/* Show final response as a normal AI message */}
        {streamingState?.finalResponse && (
          <ChatMessageBubble
            message={{
              id: "final-response",
              role: "assistant",
              content:
                typeof streamingState.finalResponse === "string"
                  ? streamingState.finalResponse
                  : JSON.stringify(streamingState.finalResponse),
              timestamp: new Date().toISOString(),
              sources: streamingState.sources,
            }}
            isStreaming={false}
            metadata={streamingState.responseMetadata}
            paperPdfUrl={paperPdfUrl}
          />
        )}

        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
