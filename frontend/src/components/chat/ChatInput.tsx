import { useState, useRef, useEffect } from "react";
import { Globe, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ChatConfigPopover, ChatConfig } from "./ChatConfigPopover";
import { cn } from "@/lib/utils";
import { Badge } from "../ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  config: ChatConfig;
  onConfigChange: (config: ChatConfig) => void;
  useWebSearch: boolean;
  onWebSearchToggle: () => void;
}

export function ChatInput({
  onSendMessage,
  disabled,
  config,
  onConfigChange,
  useWebSearch,
  onWebSearchToggle,
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = "auto";
      const newHeight = Math.min(Math.max(textarea.scrollHeight, 60), 200);
      textarea.style.height = `${newHeight}px`;

      // Enable scrolling when max height is reached
      if (textarea.scrollHeight > 200) {
        textarea.style.overflowY = "auto";
      } else {
        textarea.style.overflowY = "hidden";
      }
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="absolute bottom-0 left-0 right-0 m-4 pointer-events-none">
      {/* Gradient fade at top */}
      <div className="absolute bottom-full left-4 right-4 h-24 bg-linear-to-t from-background to-transparent pointer-events-none" />

      <form
        onSubmit={handleSubmit}
        className="max-w-[70%] mx-auto pointer-events-auto"
      >
        <div className="relative backdrop-blur-xl bg-background/70 rounded-2xl border shadow-lg p-2 overflow-hidden before:absolute before:inset-0 before:rounded-[inherit] before:bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJhIiB4PSIwIiB5PSIwIj48ZmVUdXJidWxlbmNlIGJhc2VGcmVxdWVuY3k9Ii43NSIgc3RpdGNoVGlsZXM9InN0aXRjaCIgdHlwZT0iZnJhY3RhbE5vaXNlIi8+PGZlQ29sb3JNYXRyaXggdHlwZT0ic2F0dXJhdGUiIHZhbHVlcz0iMCIvPjwvZmlsdGVyPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbHRlcj0idXJsKCNhKSIgb3BhY2l0eT0iMC4wNSIvPjwvc3ZnPg==')] before:opacity-30 before:pointer-events-none">
          <div className="relative">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about this paper... (Shift+Enter for newline)"
              className="resize-none pr-14 pb-2 bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 relative z-10"
              style={{
                height: "60px",
                overflowY: "hidden",
                maxHeight: "200px",
              }}
              disabled={disabled}
            />
          </div>

          {/* Bottom controls below textarea */}
          <div className="flex items-center justify-between pointer-events-none z-10 mt-2">
            <div className="flex items-center gap-2 pointer-events-auto">
              <ChatConfigPopover
                config={config}
                onConfigChange={onConfigChange}
              />
              <div className="flex items-center gap-1.5">
                <Switch
                  id="web-search"
                  checked={useWebSearch}
                  onCheckedChange={onWebSearchToggle}
                  disabled={disabled}
                  className="scale-90 data-[state=checked]:bg-green-600 data-[state=checked]:hover:bg-green-700"
                />
                <Badge
                  variant={useWebSearch ? "default" : "secondary"}
                  className={cn(
                    "px-1 text-xs cursor-pointer",
                    useWebSearch && "bg-green-600 hover:bg-green-700",
                  )}
                  onClick={onWebSearchToggle}
                >
                  <Globe className="h-4 w-4 mr-1" />{" "}
                  {useWebSearch ? "Web Search On" : "Web Search Off"}
                </Badge>
              </div>
              <Badge variant="default" className="text-xs">
                {config.modelProvider && config.modelSlug
                  ? `${config.modelProvider} · ${config.modelSlug}`
                  : config.model}
              </Badge>
            </div>

            <Button
              type="submit"
              size="sm"
              className="h-8 w-8 p-0 pointer-events-auto"
              disabled={!message.trim() || disabled}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
