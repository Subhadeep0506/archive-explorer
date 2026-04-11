import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Info } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";

interface StreamingResponseProps {
  content: string;
  metadata?: {
    completion_tokens?: number;
    prompt_tokens?: number;
    total_tokens?: number;
  };
}

export function StreamingResponse({
  content,
  metadata,
}: StreamingResponseProps) {
  return (
    <Card className="border-chip-violet/20">
      <CardContent className="pt-6">
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex, rehypeHighlight]}
            components={{
              h1: ({ children }) => (
                <h1 className="text-xl font-bold mt-4 mb-2">{children}</h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-lg font-semibold mt-4 mb-2">{children}</h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-base font-semibold mt-3 mb-1">
                  {children}
                </h3>
              ),
              p: ({ children }) => (
                <p className="my-1 text-sm leading-relaxed">{children}</p>
              ),
              ul: ({ children }) => (
                <ul className="list-disc list-outside ml-6 my-2 space-y-1 text-sm">
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol className="list-decimal list-outside ml-6 my-2 space-y-1 text-sm">
                  {children}
                </ol>
              ),
              li: ({ children }) => <li className="text-sm">{children}</li>,
              code: ({ className, children, ...props }) => {
                const isInline = !className;
                return isInline ? (
                  <code
                    className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono"
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
                <pre className="bg-muted rounded p-3 my-3 overflow-x-auto text-xs">
                  {children}
                </pre>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-chip-violet/50 pl-4 my-3 italic text-sm">
                  {children}
                </blockquote>
              ),
              table: ({ children }) => (
                <div className="overflow-x-auto my-4">
                  <table className="w-full text-sm border border-border">
                    {children}
                  </table>
                </div>
              ),
              thead: ({ children }) => (
                <thead className="bg-muted">{children}</thead>
              ),
              tbody: ({ children }) => <tbody>{children}</tbody>,
              tr: ({ children }) => <tr>{children}</tr>,
              th: ({ children }) => (
                <th className="px-4 py-2 text-left font-semibold border border-border bg-muted">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="px-4 py-2 border border-border">{children}</td>
              ),
              a: ({ children, href }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-chip-violet hover:underline"
                >
                  {children}
                </a>
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        </div>

        {/* Token count display */}
        {metadata && (
          <div className="mt-4 flex justify-end">
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-2">
                  <Info className="w-4 h-4" />
                  Token Usage
                </Button>
              </PopoverTrigger>
              <PopoverContent side="top" align="end" className="w-64">
                <div className="space-y-2">
                  {metadata.prompt_tokens !== undefined && (
                    <div className="flex items-center justify-between gap-8">
                      <span className="text-xs text-muted-foreground">
                        Prompt tokens
                      </span>
                      <span className="text-sm font-semibold font-mono">
                        {metadata.prompt_tokens.toLocaleString()}
                      </span>
                    </div>
                  )}
                  {metadata.completion_tokens !== undefined && (
                    <div className="flex items-center justify-between gap-8">
                      <span className="text-xs text-muted-foreground">
                        Completion tokens
                      </span>
                      <span className="text-sm font-semibold font-mono">
                        {metadata.completion_tokens.toLocaleString()}
                      </span>
                    </div>
                  )}
                  {metadata.total_tokens !== undefined && (
                    <div className="flex items-center justify-between gap-8 border-t border-border pt-2">
                      <span className="text-xs text-muted-foreground">
                        Total tokens
                      </span>
                      <span className="text-sm font-semibold font-mono">
                        {metadata.total_tokens.toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
              </PopoverContent>
            </Popover>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
