import { useRef, useEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChatMessage } from '@/types/chat';
import { ChatMessageBubble } from './ChatMessageBubble';
import { MessageSquare } from 'lucide-react';

interface ChatAreaProps {
  messages: ChatMessage[];
  paperTitle?: string;
}

export function ChatArea({ messages, paperTitle }: ChatAreaProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-chip-violet-bg flex items-center justify-center">
            <MessageSquare className="w-8 h-8 text-chip-violet" />
          </div>
          <h2 className="text-xl font-semibold mb-2">Start a conversation</h2>
          <p className="text-muted-foreground">
            {paperTitle
              ? `Ask questions about "${paperTitle}" and get AI-powered answers based on the paper content.`
              : 'Select a conversation from the sidebar or start a new chat.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1">
      <div className="max-w-4xl mx-auto p-4 space-y-4">
        {messages.map((message) => (
          <ChatMessageBubble key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
