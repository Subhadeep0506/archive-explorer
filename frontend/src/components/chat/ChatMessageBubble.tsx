import { ChatMessage } from "@/types/chat";
import { cn } from "@/lib/utils";
import {
  User,
  Bot,
  Info,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  Globe,
  FileText,
  BookOpen,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import { useState } from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MessageFeedbackDialog } from "./MessageFeedbackDialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";

interface ChatMessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
  metadata?: {
    completion_tokens?: number;
    prompt_tokens?: number;
    total_tokens?: number;
  };
  paperPdfUrl?: string;
  onLike?: (liked: boolean) => void;
  onFeedback?: (feedback: string, stars: number) => void;
}

export function ChatMessageBubble({
  message,
  isStreaming = false,
  metadata,
  paperPdfUrl,
  onLike,
  onFeedback,
}: ChatMessageBubbleProps) {
  const isUser = message.role === "user";
  const [showTokens, setShowTokens] = useState(false);
  const [feedbackDialogOpen, setFeedbackDialogOpen] = useState(false);
  const [sourcesPopoverOpen, setSourcesPopoverOpen] = useState(false);
  const [pdfDialogOpen, setPdfDialogOpen] = useState(false);
  const [selectedPdfUrl, setSelectedPdfUrl] = useState("");

  const handleLike = () => {
    if (onLike) {
      onLike(message.liked === true ? null : true);
    }
  };

  const handleDislike = () => {
    if (onLike) {
      onLike(message.liked === false ? null : false);
    }
  };

  const handleFeedbackSubmit = (feedback: string, stars: number) => {
    if (onFeedback) {
      onFeedback(feedback, stars);
    }
  };

  const handleSourceClick = (source: (typeof message.sources)[0]) => {
    const isWebSource =
      source.source_type === "web" || source.source_type === "search";

    if (isWebSource && source.source_url) {
      // Open web source in new tab
      window.open(source.source_url, "_blank", "noopener,noreferrer");
    } else if (source.source_type === "document" && paperPdfUrl) {
      // Open PDF dialog with page number if available
      const pageNum = source.metadata?.page_number || source.metadata?.page;
      console.log("Source metadata:", source.metadata);
      console.log("Page number:", pageNum);
      console.log("Original PDF URL:", paperPdfUrl);

      // Format PDF URL with page parameter
      let pdfUrl = paperPdfUrl;
      if (pageNum) {
        // Remove any existing page fragment
        const baseUrl = pdfUrl.split("#")[0].split("?")[0];
        // Use the standard PDF Open Parameters format
        pdfUrl = `${baseUrl}#page=${pageNum}`;
        console.log("Final PDF URL:", pdfUrl);
      }
      setSelectedPdfUrl(pdfUrl);
      setPdfDialogOpen(true);
      setSourcesPopoverOpen(false);
    }
  };

  return (
    <div className="space-y-2">
      <div
        className={cn(
          "flex gap-3 items-start animate-fade-in px-4 py-3 rounded-lg",
          isUser ? "bg-muted/50" : "",
        )}
      >

        <div className="flex-1 min-w-0">
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex, rehypeHighlight]}
              components={{
                h1: ({ children }) => (
                  <h1 className="text-base font-bold mt-2 mb-1">{children}</h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-base font-bold mt-2 mb-1">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-sm font-semibold mt-2 mb-1">
                    {children}
                  </h3>
                ),
                p: ({ children }) => <p className="my-1 text-sm">{children}</p>,
                ul: ({ children }) => (
                  <ul className="list-disc list-outside ml-4 my-1 space-y-0.5 text-sm">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-outside ml-4 my-1 space-y-0.5 text-sm">
                    {children}
                  </ol>
                ),
                li: ({ children }) => <li className="text-sm">{children}</li>,
                code: ({ className, children, ...props }) => {
                  const isInline = !className;
                  return isInline ? (
                    <code
                      className="bg-muted/50 px-1.5 py-0.5 rounded text-xs font-mono"
                      {...props}
                    >
                      {children}
                    </code>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
                pre: ({ children }) => (
                  <pre className="bg-muted/50 rounded p-2 my-2 overflow-x-auto text-xs">
                    {children}
                  </pre>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-2 border-muted-foreground/30 pl-3 my-2 italic text-sm">
                    {children}
                  </blockquote>
                ),
                table: ({ children }) => (
                  <div className="overflow-x-auto my-2">
                    <table className="w-full text-xs border border-border">
                      {children}
                    </table>
                  </div>
                ),
                th: ({ children }) => (
                  <th className="px-2 py-1 text-left font-semibold border border-border bg-muted">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="px-2 py-1 border border-border">{children}</td>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
            {isStreaming && (
              <span className="inline-block w-2 h-4 ml-0.5 bg-current animate-pulse" />
            )}
          </div>
        </div>
      </div>

      {/* Actions for assistant messages - token usage and feedback on same line */}
      {!isUser && !isStreaming && (
        <div className="flex gap-3 items-center justify-between px-4">
          {/* Left side - Sources button */}
          <div className="flex items-center gap-1">
            {message.sources && message.sources.length > 0 && (
              <Popover
                open={sourcesPopoverOpen}
                onOpenChange={setSourcesPopoverOpen}
              >
                <PopoverTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    {message.sources.length}{" "}
                    {message.sources.length === 1 ? "Source" : "Sources"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  className="w-[380px] p-0 overflow-hidden"
                  align="start"
                  sideOffset={8}
                >
                  <div className="p-3 border-b">
                    <h4 className="font-semibold text-sm">Sources</h4>
                  </div>
                  <ScrollArea className="h-80">
                    <div className="p-2 space-y-2">
                      {message.sources.map((source) => {
                        const isWebSource =
                          source.source_type === "web" ||
                          source.source_type === "search";
                        const pageNum =
                          source.metadata?.page_number || source.metadata?.page;

                        return (
                          <button
                            key={source.id}
                            onClick={() => handleSourceClick(source)}
                            className="w-full flex items-start gap-2 p-2 rounded-md bg-muted/50 hover:bg-muted transition-colors text-left overflow-hidden max-w-full"
                          >
                            <div className="shrink-0 mt-0.5">
                              {isWebSource ? (
                                <Globe className="w-3.5 h-3.5 text-muted-foreground" />
                              ) : (
                                <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0 space-y-1 max-w-[300px]">
                              {source.source_url && (
                                <div
                                  className="text-xs font-medium text-primary hover:underline break-all line-clamp-2"
                                  style={{
                                    wordBreak: "break-all",
                                    overflowWrap: "anywhere",
                                  }}
                                >
                                  {source.source_url}
                                </div>
                              )}
                              {source.source_text && (
                                <p
                                  className="text-xs text-muted-foreground line-clamp-2"
                                  style={{
                                    wordBreak: "break-word",
                                    overflowWrap: "anywhere",
                                  }}
                                >
                                  {source.source_text}
                                </p>
                              )}
                              <div className="flex items-center gap-1.5 flex-wrap">
                                {source.source_type && (
                                  <Badge
                                    variant="secondary"
                                    className="text-[10px] h-4 truncate max-w-[120px]"
                                  >
                                    {source.source_type}
                                  </Badge>
                                )}
                                {pageNum && (
                                  <Badge
                                    variant="outline"
                                    className="text-[10px] h-4"
                                  >
                                    Page {pageNum}
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </ScrollArea>
                </PopoverContent>
              </Popover>
            )}
          </div>

          {/* Right side - Token usage and feedback buttons */}
          <div className="flex items-center gap-1 ml-auto">
            {/* Token count display */}
            {metadata &&
              (metadata.prompt_tokens !== undefined ||
                metadata.completion_tokens !== undefined ||
                metadata.total_tokens !== undefined) && (
                <TooltipProvider>
                  <Tooltip open={showTokens} onOpenChange={setShowTokens}>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
                        onMouseEnter={() => setShowTokens(true)}
                        onMouseLeave={() => setShowTokens(false)}
                      >
                        <Info className="w-3 h-3" />
                        Token Usage
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="space-y-1">
                      {metadata.prompt_tokens !== undefined && (
                        <div className="flex justify-between gap-4 text-xs">
                          <span className="text-muted-foreground">
                            Prompt tokens:
                          </span>
                          <Badge variant="secondary" className="text-xs">
                            {metadata.prompt_tokens.toLocaleString()}
                          </Badge>
                        </div>
                      )}
                      {metadata.completion_tokens !== undefined && (
                        <div className="flex justify-between gap-4 text-xs">
                          <span className="text-muted-foreground">
                            Completion tokens:
                          </span>
                          <Badge variant="secondary" className="text-xs">
                            {metadata.completion_tokens.toLocaleString()}
                          </Badge>
                        </div>
                      )}
                      {metadata.total_tokens !== undefined && (
                        <div className="flex justify-between gap-4 text-xs font-medium pt-1 border-t">
                          <span>Total:</span>
                          <Badge variant="default" className="text-xs">
                            {metadata.total_tokens.toLocaleString()}
                          </Badge>
                        </div>
                      )}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}

            {/* Feedback buttons */}
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "h-7 w-7 p-0",
                message.liked === true && "text-primary bg-primary/10",
              )}
              onClick={handleLike}
              title="Like this response"
            >
              <ThumbsUp className="w-3.5 h-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "h-7 w-7 p-0",
                message.liked === false && "text-destructive bg-destructive/10",
              )}
              onClick={handleDislike}
              title="Dislike this response"
            >
              <ThumbsDown className="w-3.5 h-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "h-7 gap-1.5 text-xs",
                (message.feedback || message.stars) &&
                  "text-primary bg-primary/10",
              )}
              onClick={() => setFeedbackDialogOpen(true)}
              title="Provide feedback"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              Feedback
            </Button>
          </div>
        </div>
      )}

      <MessageFeedbackDialog
        open={feedbackDialogOpen}
        onOpenChange={setFeedbackDialogOpen}
        onSubmit={handleFeedbackSubmit}
        currentFeedback={message.feedback || ""}
        currentStars={message.stars || 0}
      />

      {/* PDF Preview Dialog */}
      <Dialog open={pdfDialogOpen} onOpenChange={setPdfDialogOpen}>
        <DialogContent className="max-w-4xl h-[85vh] flex flex-col p-0">
          <DialogHeader className="px-6 pt-6 pb-2">
            <DialogTitle>Source Document</DialogTitle>
          </DialogHeader>
          <div className="flex-1 px-6 pb-6">
            {selectedPdfUrl && (
              <embed
                key={selectedPdfUrl}
                src={selectedPdfUrl}
                type="application/pdf"
                className="w-full h-full rounded border"
                title="PDF Viewer"
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
