import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { PaperPdfViewer } from "@/components/PdfViewer";
import { ScrollArea } from "@/components/ui/scroll-area";
import { UsabilityChart } from "@/components/UsabilityChart";
import {
  Calendar,
  Building2,
  MapPin,
  Users,
  FileText,
  Globe,
  Code,
  Sparkles,
  Copy,
  ExternalLink,
  MessageCircle,
  BookmarkPlus,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { useSearch } from "@/context/SearchContext";
import { fetchPaperById } from "@/lib/arxiv";
import { normalizeArxivEntry } from "@/lib/papers";
import {
  savePaper,
  getSavedPapers,
  ingestPaper,
  getSummaryAndUsability,
  generateSummary,
  generateUsability,
  generateSummaryFlexible,
  generateUsabilityFlexible,
} from "@/lib/api";
import type { Paper } from "@/types/paper";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import remarkGfm from "remark-gfm";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";

export default function PaperDetail() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { accessToken } = useAuth();
  const { setIsDialogOpen } = useSearch();
  const queryClient = useQueryClient();
  const statePaper = location.state?.paper as Paper | undefined;
  const fromSearch = location.state?.fromSearch as boolean | undefined;
  const fromPage = location.state?.fromPage as string | undefined; // Track which page user came from

  useEffect(() => {
    setIsDialogOpen(false);
  }, [setIsDialogOpen]);

  const { data, isLoading } = useQuery({
    queryKey: ["paper", id],
    queryFn: () => fetchPaperById(id!, accessToken),
    enabled: Boolean(id && accessToken && !statePaper),
    staleTime: 1000 * 60 * 10, // 10 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes
    refetchOnWindowFocus: false,
  });

  const paper = statePaper || (data ? normalizeArxivEntry(data) : undefined);

  const { data: savedPapers } = useQuery({
    queryKey: ["savedPapers"],
    queryFn: () => getSavedPapers(accessToken),
    enabled: Boolean(accessToken),
    staleTime: 1000 * 60 * 5,
    refetchOnWindowFocus: false,
  });

  // Computed before the summary query so we can gate the query on isSaved
  const isSaved = savedPapers?.some((sp) => sp.arxiv_id === paper?.id);
  const savedPaperData = savedPapers?.find((sp) => sp.arxiv_id === paper?.id);
  const isIngested = savedPaperData?.ingested ?? false;

  // Poll savedPapers every 3 s while this paper is saved but ingestion hasn't finished yet.
  // Stops automatically once isIngested flips to true.
  useEffect(() => {
    if (!isSaved || isIngested) return;
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ["savedPapers"] });
    }, 3000);
    return () => clearInterval(interval);
  }, [isSaved, isIngested, queryClient]);

  // Local state for unsaved papers — results are generated but never persisted in DB,
  // so we hold them in memory for the lifetime of this page visit.
  const [localSummary, setLocalSummary] = useState<string | null>(null);
  const [localUsability, setLocalUsability] = useState<import("@/types/summary").UsabilityMetrics | null>(null);

  // Only query the DB for saved papers — unsaved papers have no DB record to fetch.
  const {
    data: summaryData,
    isLoading: isSummaryLoading,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ["summary", id],
    queryFn: () => getSummaryAndUsability(id!, accessToken),
    enabled: Boolean(id && accessToken && paper && isSaved),
    retry: false,
    staleTime: 1000 * 60 * 15,
    gcTime: 1000 * 60 * 60,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });

  const savePaperMutation = useMutation({
    mutationFn: () => savePaper(paper!, accessToken),
    onSuccess: () => {
      toast.success("Paper saved successfully!");
      // Immediately refetch saved papers after save
      queryClient.invalidateQueries({ queryKey: ["savedPapers"] });

      // Start ingestion in background
      ingestPaper({
        paperUrl: paper!.pdfUrl,
        arxivId: paper!.id,
        token: accessToken,
      })
        .then(() => {
          toast.success(
            "Document ingested successfully! You can now chat with this paper.",
          );
          // Refetch saved papers immediately after ingestion completes
          queryClient.refetchQueries({ queryKey: ["savedPapers"], type: "active" });
        })
        .catch((error) => {
          const errorMsg = error instanceof Error
            ? error.message
            : typeof error === 'object' && error?.message
              ? error.message
              : "Unknown error occurred";
          toast.error(`Failed to ingest document: ${errorMsg}`);
          // Refresh saved papers to update ingestion status
          queryClient.invalidateQueries({ queryKey: ["savedPapers"] });
        });
    },
    onError: (error) => {
      const errorMsg = error instanceof Error ? error.message : "Unknown error occurred";
      const friendlyMsg = errorMsg.includes("already exists")
        ? "This paper is already saved"
        : `Failed to save paper: ${errorMsg}`;
      toast.error(friendlyMsg);
    },
  });

  const generateSummaryMutation = useMutation({
    mutationFn: () => {
      if (isSaved) {
        // Always send pdf_url alongside arxiv_id so the backend can fall back to
        // direct PDF loading without needing it stored in the DB (handles not-ingested papers).
        return generateSummaryFlexible(
          { arxiv_id: id, pdf_url: paper!.pdfUrl ?? undefined },
          accessToken,
        );
      } else {
        return generateSummaryFlexible({ pdf_url: paper!.pdfUrl }, accessToken);
      }
    },
    onSuccess: (data) => {
      toast.success("Summary generated successfully!");
      if (isSaved) {
        refetchSummary();
      } else {
        // Unsaved papers have no DB record — store result locally so the UI can display it.
        setLocalSummary(data.summary);
      }
    },
    onError: (error) => {
      const errorMsg = error instanceof Error ? error.message : "Unknown error";
      const friendlyMsg = errorMsg.includes("no arxiv_id or pdf_url")
        ? "No PDF URL available. Please save the paper first."
        : errorMsg.includes("timeout")
          ? "Summary generation took too long. Please try again."
          : `Failed to generate summary: ${errorMsg}`;
      toast.error(friendlyMsg);
    },
  });

  const generateUsabilityMutation = useMutation({
    mutationFn: () => {
      if (isSaved) {
        return generateUsabilityFlexible(
          { arxiv_id: id, pdf_url: paper!.pdfUrl ?? undefined },
          accessToken,
        );
      } else {
        return generateUsabilityFlexible(
          { pdf_url: paper!.pdfUrl },
          accessToken,
        );
      }
    },
    onSuccess: (data) => {
      toast.success("Usability metrics generated successfully!");
      if (isSaved) {
        refetchSummary();
      } else {
        setLocalUsability({
          domain_applicability: data.domain_applicability,
          reproducibility_score: data.reproducibility_score,
          new_tech_applicability: data.new_tech_applicability,
          impact_score: data.impact_score,
        });
      }
    },
    onError: (error) => {
      const errorMsg = error instanceof Error ? error.message : "Unknown error";
      const friendlyMsg = errorMsg.includes("no arxiv_id or pdf_url")
        ? "No PDF URL available. Please save the paper first."
        : errorMsg.includes("timeout")
          ? "Analysis took too long. Please try again."
          : `Failed to generate metrics: ${errorMsg}`;
      toast.error(friendlyMsg);
    },
  });

  const handleSavePaper = () => {
    savePaperMutation.mutate();
  };

  const handleChat = () => {
    navigate(`/paper/${paper.id}/chat`, { state: { paper } });
  };

  const handleCopyBibtex = () => {
    const bibtex = `@article{${paper.authors[0]?.split(" ")[1]?.toLowerCase() || "author"}${paper.date.slice(0, 4)},
  title={${paper.title}},
  author={${paper.authors.join(" and ")}},
  year={${paper.date.slice(0, 4)}},
  institution={${paper.institution || paper.primaryCategory || "arXiv"}}
}`;
    navigator.clipboard.writeText(bibtex);
    toast.success("BibTeX copied to clipboard!");
  };

  const formattedDate = paper?.date
    ? new Date(paper.date).toLocaleDateString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "Date pending";

  // For saved papers: comes from DB via query. For unsaved: held in local state.
  const aiSummary = summaryData?.summary ?? localSummary;
  const usabilityMetrics = summaryData?.usability ?? localUsability;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto py-6 px-4">
          <div className="flex items-center justify-center min-h-[60vh]">
            <Loader2 className="w-12 h-12 animate-spin text-chip-violet" />
          </div>
        </div>
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto py-6 px-4">
          <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
            <p className="text-lg text-muted-foreground">Paper not found</p>
            <Button onClick={() => navigate("/app")}>Back to Dashboard</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-6 px-4">
        <div className="mb-6">
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink
                  onClick={() => navigate("/app")}
                  className="cursor-pointer"
                >
                  Dashboard
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />

              {fromPage === "/saved-papers" && (
                <>
                  <BreadcrumbItem>
                    <BreadcrumbLink
                      onClick={() => navigate("/saved-papers")}
                      className="cursor-pointer"
                    >
                      Saved Papers
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator />
                </>
              )}

              <BreadcrumbItem>
                <BreadcrumbPage className="max-w-xs truncate">
                  {paper?.title}
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3 space-y-6">
            <div className="animate-fade-in">
              <h1 className="text-2xl lg:text-3xl font-bold leading-tight mb-4">
                {paper.title}
              </h1>

              <div className="flex flex-wrap gap-2 mb-4">
                {paper.topics.map((topic) => (
                  <Badge key={topic} variant="secondary">
                    {topic}
                  </Badge>
                ))}
              </div>

              <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mb-6">
                <span className="flex items-center gap-1.5">
                  <Users className="w-4 h-4" />
                  {paper.authors.join(", ")}
                </span>
                <span className="flex items-center gap-1.5">
                  <Building2 className="w-4 h-4" />
                  {paper.institution || paper.primaryCategory || "arXiv"}
                </span>
                <span className="flex items-center gap-1.5">
                  <MapPin className="w-4 h-4" />
                  {paper.country || "Global Research"}
                </span>
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-4 h-4" />
                  {formattedDate}
                </span>
              </div>

              <div className="flex flex-wrap gap-3 mb-2">
                <Button
                  onClick={handleSavePaper}
                  disabled={isSaved || savePaperMutation.isPending}
                  variant="outline"
                >
                  {savePaperMutation.isPending ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <BookmarkPlus className="w-4 h-4 mr-2" />
                  )}
                  {isSaved ? "Saved" : "Save Paper"}
                </Button>
                <Button
                  onClick={handleChat}
                  disabled={!isSaved || !isIngested}
                  variant="outline"
                  title={!isSaved ? "Save the paper first to chat with it" : ""}
                >
                  {isSaved && !isIngested ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <MessageCircle className="w-4 h-4 mr-2" />
                  )}
                  {isSaved && !isIngested ? "Ingesting..." : "Chat with Paper"}
                </Button>
                <a
                  href={paper.pdfUrl || paper.htmlUrl || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="outline">
                    <FileText className="w-4 h-4 mr-2" />
                    View PDF
                    <ExternalLink className="w-3 h-3 ml-2" />
                  </Button>
                </a>
                {paper.htmlUrl && (
                  <a
                    href={paper.htmlUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button
                      variant="outline"
                    >
                      <Globe className="w-4 h-4 mr-2" />
                      HTML Version
                    </Button>
                  </a>
                )}
                {paper.githubUrl && (
                  <a
                    href={paper.githubUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button
                      variant="outline"
                    >
                      <Code className="w-4 h-4 mr-2" />
                      Source Code
                    </Button>
                  </a>
                )}
                <Button variant="outline" onClick={handleCopyBibtex}>
                  <Copy className="w-4 h-4 mr-2" />
                  Copy BibTeX
                </Button>
              </div>
            </div>
            <Card
              className="animate-fade-in"
              style={{ animationDelay: "0.15s" }}
            >
              <CardHeader>
                <CardTitle className="text-lg">Abstract</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground leading-relaxed">
                  {paper.abstract}
                </p>
              </CardContent>
            </Card>
            <Card
              className="animate-fade-in"
              style={{ animationDelay: "0.1s" }}
            >
              <CardHeader className="pb-1 space-y-1">
                <CardTitle className="text-lg flex items-center gap-2">
                  <FileText className="w-5 h-5 text-chip-violet" />
                  Paper Preview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <PaperPdfViewer paper={paper} />
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-2">
            {/* Sticky wrapper — overflow must be on a child, not this element */}
            <div className="sticky top-24">
            <ScrollArea className="h-[calc(100vh-7rem)]">
            <div className="space-y-6 pb-4">
              {/* AI Summary Card */}
              <Card className="animate-slide-in-right">
                <CardHeader className="border-b shrink-0">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Sparkles className="w-5 h-5" />
                    AI-Generated Summary
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  {isSummaryLoading ? (
                    <div className="h-50 flex items-center justify-center">
                      <Loader2 className="w-8 h-8 animate-spin text-chip-violet" />
                    </div>
                  ) : aiSummary ? (
                    <ScrollArea className="h-80">
                      <div className="px-4 py-4">
                        <div className="markdown-content">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm, remarkMath]}
                            rehypePlugins={[rehypeKatex, rehypeHighlight]}
                            components={{
                              h2: ({ children }) => (
                                <h2 className="text-lg font-bold mt-4 mb-2 text-foreground">{children}</h2>
                              ),
                              h3: ({ children }) => (
                                <h3 className="text-base font-semibold mt-3 mb-1 text-foreground">{children}</h3>
                              ),
                              p: ({ children }) => (
                                <p className="text-sm text-muted-foreground my-2 leading-relaxed">{children}</p>
                              ),
                              ul: ({ children }) => (
                                <ul className="list-disc list-outside text-sm text-muted-foreground my-2 ml-6 space-y-1">{children}</ul>
                              ),
                              ol: ({ children }) => (
                                <ol className="list-decimal list-outside text-sm text-muted-foreground my-2 ml-6 space-y-1">{children}</ol>
                              ),
                              li: ({ children }) => (
                                <li className="text-muted-foreground">{children}</li>
                              ),
                              table: ({ children }) => (
                                <div className="overflow-x-auto my-4">
                                  <table className="w-full text-sm border border-border">{children}</table>
                                </div>
                              ),
                              thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
                              tbody: ({ children }) => <tbody>{children}</tbody>,
                              tr: ({ children }) => <tr>{children}</tr>,
                              th: ({ children }) => (
                                <th className="px-4 py-2 text-left font-semibold text-foreground border border-border bg-muted">{children}</th>
                              ),
                              td: ({ children }) => (
                                <td className="px-4 py-2 text-muted-foreground border border-border">{children}</td>
                              ),
                              code: ({ className, children, ...props }) => {
                                const isInline = !className;
                                return isInline ? (
                                  <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono text-foreground" {...props}>
                                    {children}
                                  </code>
                                ) : (
                                  <code className={`block bg-muted p-3 rounded text-sm font-mono overflow-x-auto ${className || ""}`} {...props}>
                                    {children}
                                  </code>
                                );
                              },
                              pre: ({ children }) => (
                                <pre className="bg-muted p-3 rounded text-sm font-mono overflow-x-auto my-3 border border-border">{children}</pre>
                              ),
                              strong: ({ children }) => (
                                <strong className="font-semibold text-foreground">{children}</strong>
                              ),
                              em: ({ children }) => (
                                <em className="italic text-foreground">{children}</em>
                              ),
                            }}
                          >
                            {aiSummary}
                          </ReactMarkdown>
                        </div>
                      </div>
                    </ScrollArea>
                  ) : (
                    <div className="h-50 flex flex-col items-center justify-center gap-4">
                      <p className="text-sm text-muted-foreground text-center">
                        No summary available yet.
                      </p>
                      <Button
                        onClick={() => generateSummaryMutation.mutate()}
                        disabled={generateSummaryMutation.isPending}
                        variant="accent"
                      >
                        {generateSummaryMutation.isPending ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4 mr-2" />
                            Generate Summary
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Usability Metrics Card */}
              <Card
                className="animate-slide-in-right"
                style={{ animationDelay: "0.05s" }}
              >
                {isSummaryLoading ? (
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="w-8 h-8 animate-spin text-chip-emerald" />
                    </div>
                  </CardContent>
                ) : usabilityMetrics ? (
                  <UsabilityChart usability={usabilityMetrics} />
                ) : (
                  <>
                    <CardHeader className="border-b shrink-0">
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <Sparkles className="w-5 h-5" />
                        Usability Metrics
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="h-50 flex flex-col items-center justify-center gap-4">
                        <p className="text-sm text-muted-foreground text-center">
                          No usability metrics available yet.
                        </p>
                        <Button
                          onClick={() => generateUsabilityMutation.mutate()}
                          disabled={generateUsabilityMutation.isPending}
                          variant="accent"
                        >
                          {generateUsabilityMutation.isPending ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Generating...
                            </>
                          ) : (
                            <>
                              <Sparkles className="w-4 h-4 mr-2" />
                              Generate Metrics
                            </>
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </>
                )}
              </Card>
            </div>
            </ScrollArea>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
