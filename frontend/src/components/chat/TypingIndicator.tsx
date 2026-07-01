import { Bot } from "lucide-react";
import { cn } from "@/lib/utils";

export function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in">
      <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-chip-violet-bg text-chip-violet">
        <Bot className="w-4 h-4" />
      </div>

      <div className="max-w-[75%] rounded-2xl px-4 py-3 bg-muted text-foreground rounded-tl-sm">
        <div className="flex items-center gap-1.5">
          <div className="flex gap-1">
            <div
              className={cn(
                "w-2 h-2 rounded-full bg-primary",
                "animate-bounce",
              )}
              style={{
                animationDelay: "0ms",
                animationDuration: "1.4s",
              }}
            />
            <div
              className={cn(
                "w-2 h-2 rounded-full bg-primary",
                "animate-bounce",
              )}
              style={{
                animationDelay: "200ms",
                animationDuration: "1.4s",
              }}
            />
            <div
              className={cn(
                "w-2 h-2 rounded-full bg-primary",
                "animate-bounce",
              )}
              style={{
                animationDelay: "400ms",
                animationDuration: "1.4s",
              }}
            />
          </div>
          <span className="text-xs text-foreground font-medium ml-1">
            Generating response...
          </span>
        </div>
      </div>
    </div>
  );
}
