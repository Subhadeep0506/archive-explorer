import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PaperPdfViewer } from "@/components/PdfViewer";
import { UsabilityChart } from "@/components/UsabilityChart";
import {
  ArrowLeft,
  Calendar,
  Building2,
  MapPin,
  Users,
  FileText,
  Globe,
  Github,
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
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: false,
  });

  // Fetch summary and usability data
  const {
    data: summaryData,
    isLoading: isSummaryLoading,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ["summary", id],
    queryFn: () => getSummaryAndUsability(id!, accessToken),
    enabled: Boolean(id && accessToken && paper),
    retry: false,
    staleTime: 1000 * 60 * 15, // 15 minutes - summary/usability rarely changes
    gcTime: 1000 * 60 * 60, // 60 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: false, // Don't refetch on component remount if data exists
  });

  const isSaved = savedPapers?.some((sp) => sp.arxiv_id === paper?.id);

  const savePaperMutation = useMutation({
    mutationFn: () => savePaper(paper!, accessToken),
    onSuccess: () => {
      toast.success("Paper saved successfully!");
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
        })
        .catch((error) => {
          toast.error(`Failed to ingest document: ${error.message}`);
        });
      queryClient.invalidateQueries({ queryKey: ["savedPapers"] });
    },
    onError: (error) => {
      toast.error(`Failed to save paper: ${error.message}`);
    },
  });

  const generateSummaryMutation = useMutation({
    mutationFn: () => {
      // If paper is saved, use arxiv_id; otherwise use pdf_url
      if (isSaved) {
        return generateSummaryFlexible({ arxiv_id: id }, accessToken);
      } else {
        return generateSummaryFlexible({ pdf_url: paper!.pdfUrl }, accessToken);
      }
    },
    onSuccess: () => {
      toast.success("Summary generated successfully!");
      refetchSummary();
    },
    onError: (error) => {
      toast.error(`Failed to generate summary: ${error.message}`);
    },
  });

  const generateUsabilityMutation = useMutation({
    mutationFn: () => {
      // If paper is saved, use arxiv_id; otherwise use pdf_url
      if (isSaved) {
        return generateUsabilityFlexible({ arxiv_id: id }, accessToken);
      } else {
        return generateUsabilityFlexible(
          { pdf_url: paper!.pdfUrl },
          accessToken,
        );
      }
    },
    onSuccess: () => {
      toast.success("Usability metrics generated successfully!");
      refetchSummary();
    },
    onError: (error) => {
      toast.error(`Failed to generate usability metrics: ${error.message}`);
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

  const aiSummary = summaryData?.summary;
  const usabilityMetrics = summaryData?.usability;

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
        <button
          onClick={() =>
            navigate("/app", {
              state: fromSearch ? { openSearchDialog: true } : undefined,
            })
          }
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          {fromSearch ? "Back to Search" : "Back to Dashboard"}
        </button>

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

              <div className="flex flex-wrap gap-3 mb-6">
                <Button
                  onClick={handleSavePaper}
                  disabled={isSaved || savePaperMutation.isPending}
                  className="bg-chip-amber hover:bg-chip-amber/90"
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
                  className="bg-chip-violet hover:bg-chip-violet/90"
                >
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Chat with Paper
                </Button>
                <a
                  href={paper.pdfUrl || paper.htmlUrl || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button className="bg-chip-coral hover:bg-chip-coral/90">
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
                      className="border-chip-blue text-chip-blue hover:bg-chip-blue hover:text-white"
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
                      className="border-chip-emerald text-chip-emerald hover:bg-chip-emerald hover:text-white"
                    >
                      <Github className="w-4 h-4 mr-2" />
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
              style={{ animationDelay: "0.15s", opacity: 0 }}
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
              style={{ animationDelay: "0.1s", opacity: 0 }}
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
            {/* Sticky container for both AI Summary and Usability */}
            <div className="sticky top-24 space-y-6 max-h-[calc(100vh-7rem)] overflow-y-auto scrollbar-thin">
              {/* AI Summary Card */}
              <Card
                className="animate-slide-in-right overflow-hidden"
                style={{ opacity: 0 }}
              >
                <CardHeader className="border-b bg-gradient-to-r from-chip-violet-bg to-chip-blue-bg rounded-t-lg">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Sparkles className="w-5 h-5 text-chip-violet" />
                    AI-Generated Summary
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  {isSummaryLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="w-8 h-8 animate-spin text-chip-violet" />
                    </div>
                  ) : aiSummary ? (
                    <div className="markdown-content">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex, rehypeHighlight]}
                        components={{
                          h2: ({ children }) => (
                            <h2 className="text-lg font-bold mt-4 mb-2 text-foreground">
                              {children}
                            </h2>
                          ),
                          h3: ({ children }) => (
                            <h3 className="text-base font-semibold mt-3 mb-1 text-foreground">
                              {children}
                            </h3>
                          ),
                          p: ({ children }) => (
                            <p className="text-sm text-muted-foreground my-2 leading-relaxed">
                              {children}
                            </p>
                          ),
                          ul: ({ children }) => (
                            <ul className="list-disc list-outside text-sm text-muted-foreground my-2 ml-6 space-y-1">
                              {children}
                            </ul>
                          ),
                          ol: ({ children }) => (
                            <ol className="list-decimal list-outside text-sm text-muted-foreground my-2 ml-6 space-y-1">
                              {children}
                            </ol>
                          ),
                          li: ({ children }) => (
                            <li className="text-muted-foreground">
                              {children}
                            </li>
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
                            <th className="px-4 py-2 text-left font-semibold text-foreground border border-border bg-muted">
                              {children}
                            </th>
                          ),
                          td: ({ children }) => (
                            <td className="px-4 py-2 text-muted-foreground border border-border">
                              {children}
                            </td>
                          ),
                          code: ({ className, children, ...props }) => {
                            const isInline = !className;
                            return isInline ? (
                              <code
                                className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono text-foreground"
                                {...props}
                              >
                                {children}
                              </code>
                            ) : (
                              <code
                                className={`block bg-muted p-3 rounded text-sm font-mono overflow-x-auto ${className || ""}`}
                                {...props}
                              >
                                {children}
                              </code>
                            );
                          },
                          pre: ({ children }) => (
                            <pre className="bg-muted p-3 rounded text-sm font-mono overflow-x-auto my-3 border border-border">
                              {children}
                            </pre>
                          ),
                          strong: ({ children }) => (
                            <strong className="font-semibold text-foreground">
                              {children}
                            </strong>
                          ),
                          em: ({ children }) => (
                            <em className="italic text-foreground">
                              {children}
                            </em>
                          ),
                        }}
                      >
                        {aiSummary}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12 gap-4">
                      <p className="text-sm text-muted-foreground text-center">
                        No summary available yet.
                      </p>
                      <Button
                        onClick={() => generateSummaryMutation.mutate()}
                        disabled={generateSummaryMutation.isPending}
                        className="bg-chip-violet hover:bg-chip-violet/90"
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
                className="animate-slide-in-right overflow-hidden"
                style={{ animationDelay: "0.05s", opacity: 0 }}
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
                    <CardHeader className="border-b bg-gradient-to-r from-chip-emerald-bg to-chip-teal-bg rounded-t-lg">
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <Sparkles className="w-5 h-5 text-chip-emerald" />
                        Usability Metrics
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="pt-6">
                      <div className="flex flex-col items-center justify-center py-12 gap-4">
                        <p className="text-sm text-muted-foreground text-center">
                          No usability metrics available yet.
                        </p>
                        <Button
                          onClick={() => generateUsabilityMutation.mutate()}
                          disabled={generateUsabilityMutation.isPending}
                          className="bg-chip-emerald hover:bg-chip-emerald/90"
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
          </div>
        </div>
      </div>
    </div>
  );
}
