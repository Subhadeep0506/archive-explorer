import { ChatMessage } from '@/types/chat';
import { cn } from '@/lib/utils';
import { User, Bot } from 'lucide-react';

interface ChatMessageBubbleProps {
  message: ChatMessage;
}

export function ChatMessageBubble({ message }: ChatMessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={cn(
        'flex gap-3 animate-fade-in',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center shrink-0',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-chip-violet-bg text-chip-violet'
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      <div
        className={cn(
          'max-w-[75%] rounded-2xl px-4 py-3',
          isUser
            ? 'bg-primary text-primary-foreground rounded-tr-sm'
            : 'bg-muted text-foreground rounded-tl-sm'
        )}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {message.content.split('\n').map((line, i) => {
            if (line.startsWith('**') && line.endsWith('**')) {
              return (
                <p key={i} className="font-semibold my-1">
                  {line.replace(/\*\*/g, '')}
                </p>
              );
            }
            if (line.startsWith('- ')) {
              return (
                <p key={i} className="my-0.5 ml-2">
                  • {line.substring(2).replace(/\*\*(.*?)\*\*/g, '$1')}
                </p>
              );
            }
            if (line.match(/^\d+\./)) {
              const boldMatch = line.match(/\*\*(.*?)\*\*/);
              if (boldMatch) {
                return (
                  <p key={i} className="my-0.5">
                    {line.replace(/\*\*(.*?)\*\*/g, '')}
                    <strong>{boldMatch[1]}</strong>
                    {line.split('**')[2] || ''}
                  </p>
                );
              }
              return <p key={i} className="my-0.5">{line}</p>;
            }
            if (line.trim() === '') return <br key={i} />;
            return <p key={i} className="my-1">{line.replace(/\*\*(.*?)\*\*/g, '$1')}</p>;
          })}
        </div>
      </div>
    </div>
  );
}
