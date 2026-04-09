import { useState } from "react";
import { StreamingNodeUpdate } from "@/types/chat";
import {
  ChevronDown,
  ChevronRight,
  Loader2,
  Check,
  ExternalLink,
  Search,
  Database,
  Brain,
  FileText,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface StreamingUpdateProps {
  node: StreamingNodeUpdate;
  isActive?: boolean;
  isLast?: boolean;
}

// Helper to trim text
function trimText(text: string, maxLength = 40): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}

// Helper to parse and display node data
function formatNodeData(data: unknown): JSX.Element | null {
  if (!data || typeof data !== "object") return null;

  const dataObj = data as Record<string, unknown>;

  // Handle retrieved docs - show in grid
  if ("retrieved_docs" in dataObj && Array.isArray(dataObj.retrieved_docs)) {
    const docs = dataObj.retrieved_docs as Array<{
      metadata?: Record<string, unknown>;
      page_content?: string;
    }>;
    return (
      <div>
        <div className="font-medium text-[10px] mb-1.5">
          📄 Retrieved Documents ({docs.length})
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-1.5">
          {docs.map((doc, idx: number) => {
            const metadata = doc.metadata as
              | Record<string, unknown>
              | undefined;
            return (
              <div
                key={idx}
                className="bg-muted/40 rounded border border-border/50 p-1.5 space-y-0.5"
              >
                <div className="flex items-start justify-between gap-1.5">
                  <div className="font-medium text-foreground text-[10px] flex-1 leading-tight">
                    {metadata?.title
                      ? trimText(String(metadata.title), 50)
                      : "Untitled"}
                  </div>
                  <Badge
                    variant="outline"
                    className="text-[9px] px-0.5 py-0 h-3.5 shrink-0"
                  >
                    #{idx + 1}
                  </Badge>
                </div>
                <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                  {metadata?.arxiv_id && (
                    <span className="font-mono text-[9px]">
                      {String(metadata.arxiv_id)}
                    </span>
                  )}
                  {metadata?.page !== undefined && (
                    <span>• Page {Number(metadata.page) + 1}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Handle doc relevance scores with reranked docs - show in grid
  if (
    "doc_relevance_scores" in dataObj &&
    Array.isArray(dataObj.doc_relevance_scores)
  ) {
    const scores = dataObj.doc_relevance_scores as number[];
    const docs =
      (dataObj.retrieved_docs as Array<{
        metadata?: Record<string, unknown>;
      }>) || [];

    return (
      <div>
        <div className="font-medium text-[10px] mb-1.5">
          🎯 Reranked Documents
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-1.5">
          {scores.map((score: number, idx: number) => {
            const doc = docs[idx];
            const metadata = doc?.metadata as
              | Record<string, unknown>
              | undefined;
            return (
              <div
                key={idx}
                className="bg-muted/40 rounded border border-border/50 p-1.5 space-y-1"
              >
                <div className="flex items-start justify-between gap-1.5">
                  <div className="font-medium text-foreground text-[10px] flex-1 leading-tight">
                    {metadata?.title
                      ? trimText(String(metadata.title), 50)
                      : "Untitled"}
                  </div>
                  <Badge
                    variant="secondary"
                    className="text-[9px] px-1 py-0 h-4 shrink-0 bg-chip-violet/20 text-chip-violet"
                  >
                    Rank {idx + 1}
                  </Badge>
                </div>
                {metadata?.page !== undefined && (
                  <div className="text-[10px] text-muted-foreground">
                    Page {Number(metadata.page) + 1}
                  </div>
                )}
                <div className="flex items-center gap-1.5">
                  <div className="flex-1 bg-muted rounded-full h-1 overflow-hidden">
                    <div
                      className="bg-chip-violet h-full transition-all"
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                  <span className="text-muted-foreground text-[9px] w-8 text-right">
                    {(score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Handle web search results - show as clickable cards in grid
  if (
    "web_search_results" in dataObj &&
    Array.isArray(dataObj.web_search_results)
  ) {
    const results = dataObj.web_search_results as Array<{
      metadata?: {
        title?: string;
        description?: string;
        url?: string;
        image?: string;
        favicon?: string;
        sitename?: string;
      };
      page_content?: string;
    }>;

    return (
      <div>
        <div className="font-medium text-[10px] mb-1.5">
          🌐 Web Search Results ({results.length})
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {results.map((result, idx: number) => {
            const meta = result.metadata;
            if (!meta) return null;

            return (
              <a
                key={idx}
                href={meta.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group bg-muted/40 rounded-lg border border-border/50 p-2.5 hover:border-chip-violet/50 hover:bg-muted/60 transition-all overflow-hidden"
              >
                <div className="flex gap-2">
                  {/* Image thumbnail */}
                  {meta.image && (
                    <div className="flex-shrink-0 w-16 h-16 rounded overflow-hidden bg-muted">
                      <img
                        src={meta.image}
                        alt={meta.title || "Search result"}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          // Hide image if it fails to load
                          (e.target as HTMLElement).style.display = "none";
                        }}
                      />
                    </div>
                  )}

                  <div className="flex-1 min-w-0">
                    {/* Site info */}
                    <div className="flex items-center gap-1.5 mb-1">
                      {meta.favicon && (
                        <img
                          src={meta.favicon}
                          alt=""
                          className="w-3 h-3 flex-shrink-0"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = "none";
                          }}
                        />
                      )}
                      {meta.sitename && (
                        <span className="text-[9px] text-muted-foreground truncate">
                          {meta.sitename}
                        </span>
                      )}
                      <ExternalLink className="w-2.5 h-2.5 ml-auto text-muted-foreground group-hover:text-chip-violet transition-colors flex-shrink-0" />
                    </div>

                    {/* Title */}
                    {meta.title && (
                      <div className="font-medium text-foreground text-[11px] leading-tight mb-1 line-clamp-2 group-hover:text-chip-violet transition-colors">
                        {meta.title}
                      </div>
                    )}

                    {/* Description */}
                    {meta.description && (
                      <div className="text-[10px] text-muted-foreground leading-snug line-clamp-2">
                        {meta.description}
                      </div>
                    )}
                  </div>
                </div>
              </a>
            );
          })}
        </div>
      </div>
    );
  }

  // Handle response metadata - show as a table
  if ("response_metadata" in dataObj) {
    const metadata = dataObj.response_metadata as Record<string, unknown>;
    return (
      <div>
        <div className="font-medium text-[10px] mb-1.5">📊 Token Usage</div>
        <div className="border border-border rounded overflow-hidden">
          <table className="w-full text-[10px]">
            <thead className="bg-muted/50">
              <tr>
                {metadata.prompt_tokens !== undefined && (
                  <th className="px-2 py-1 text-center font-medium">
                    Prompt Tokens
                  </th>
                )}
                {metadata.completion_tokens !== undefined && (
                  <th className="px-2 py-1 text-center font-medium">
                    Completion Tokens
                  </th>
                )}
                {metadata.total_tokens !== undefined && (
                  <th className="px-2 py-1 text-center font-medium">
                    Total Tokens
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              <tr>
                {metadata.prompt_tokens !== undefined && (
                  <td className="px-2 py-1 text-center font-mono">
                    {String(metadata.prompt_tokens)}
                  </td>
                )}
                {metadata.completion_tokens !== undefined && (
                  <td className="px-2 py-1 text-center font-mono">
                    {String(metadata.completion_tokens)}
                  </td>
                )}
                {metadata.total_tokens !== undefined && (
                  <td className="px-2 py-1 text-center font-mono font-medium bg-muted/30">
                    {String(metadata.total_tokens)}
                  </td>
                )}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if ("response" in dataObj) {
    return null;
  }

  return (
    <pre className="text-xs bg-muted/50 p-2 rounded overflow-x-auto max-h-32 overflow-y-auto">
      {JSON.stringify(dataObj, null, 2)}
    </pre>
  );
}

export function StreamingUpdate({
  node,
  isActive = false,
  isLast = false,
}: StreamingUpdateProps) {
  const [isOpen, setIsOpen] = useState(true);

  const timeTaken =
    node.endTime && node.startTime
      ? ((node.endTime - node.startTime) / 1000).toFixed(1)
      : null;

  const hasVisibleData = node.data && formatNodeData(node.data) !== null;
  const hasContent = node.messages.length > 0 || hasVisibleData;

  const stepIcons: Record<string, React.ElementType> = {
    search: Search,
    fetch: Database,
    analyze: Brain,
    compose: FileText,
  };

  function StepIcon({ status }: { status: "done" | "active" | "pending" }) {
    const Icon = stepIcons[node.id] || FileText;

    if (status === "done") {
      return (
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-background">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-chip-violet/15">
            <Check className="h-3.5 w-3.5 text-chip-violet" />
          </div>
        </div>
      );
    }

    if (status === "active") {
      return (
        <div className="relative flex h-7 w-7 items-center justify-center">
          <div className="absolute inset-0 rounded-full bg-chip-violet/20 animate-pulse" />
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-background">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-chip-violet/15">
              <Loader2 className="h-3.5 w-3.5 animate-spin text-chip-violet" />
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-background">
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-secondary">
          <Icon className="h-3.5 w-3.5 text-muted-foreground" />
        </div>
      </div>
    );
  }

  const status: "done" | "active" | "pending" = isActive
    ? "active"
    : node.endTime
      ? "done"
      : "pending";

  return (
    <div className="relative">
      {!isLast && (
        <div
          className="absolute left-[13px] top-[14px] w-px bg-chip-violet/30"
          style={{ height: `calc(100% - 14px)` }}
        />
      )}

      <div className="relative flex items-start gap-3">
        <div className="relative">
          <StepIcon status={status} />
        </div>

        <div className={!isLast ? "pb-5" : "pt-1"}>
          {status !== "done" && (
            <div
              className={`text-sm font-medium leading-none ${status === "active" ? "text-chip-violet" : "text-muted-foreground"}`}
            >
              {node.displayName}
            </div>
          )}
          {node.messages.length > 0 &&
            (status !== "pending" || node.type === "custom") && (
              <div className="mt-1 text-xs text-muted-foreground">
                {node.messages.map((m, i) => (
                  <div key={i}>{m}</div>
                ))}
              </div>
            )}

          {status === "done" && timeTaken && (
            <span className="mt-1 inline-block font-mono text-[10px] text-muted-foreground">
              {timeTaken}s
            </span>
          )}

          {/* Expandable data section */}
          {hasVisibleData && status !== "pending" && (
            <div className="mt-2">
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                {isOpen ? (
                  <ChevronDown className="w-3 h-3" />
                ) : (
                  <ChevronRight className="w-3 h-3" />
                )}
                <span>Details</span>
              </button>
              {isOpen && (
                <div className="mt-2">{formatNodeData(node.data)}</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
