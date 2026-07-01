import { Paper } from "@/types/paper";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { HoverCard, HoverCardTrigger, HoverCardContent } from "@/components/ui/hover-card";
import {
  BookmarkPlus,
  BookmarkCheck,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { savePaper, ingestPaper } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";
import { useMemo, useState } from "react";
import { PaperHoverCard } from "@/components/PaperHoverCard";

export const CATEGORY_GRADIENTS: Record<string, string> = {
  "cs.AI": "from-blue-700 via-indigo-500 to-violet-400",
  "cs.CL": "from-emerald-700 via-teal-500 to-cyan-400",
  "cs.LG": "from-purple-700 via-fuchsia-500 to-pink-400",
  "cs.CV": "from-orange-700 via-amber-500 to-yellow-400",
  "cs.CR": "from-red-700 via-rose-500 to-pink-400",
  "cs.SE": "from-sky-700 via-blue-500 to-indigo-400",
  "cs.RO": "from-slate-700 via-zinc-500 to-stone-400",
  "cs.NE": "from-lime-700 via-green-500 to-emerald-400",
  "cs.IR": "from-cyan-700 via-sky-500 to-blue-400",
  "cs.DC": "from-violet-700 via-purple-500 to-indigo-400",
  "cs.HC": "from-rose-700 via-pink-500 to-fuchsia-400",
  "cs.CY": "from-amber-700 via-orange-500 to-red-400",
  "cs.DB": "from-teal-700 via-emerald-500 to-green-400",
  "stat.ML": "from-pink-700 via-rose-500 to-red-400",
};
export const DEFAULT_GRADIENT = "from-slate-700 via-blue-600 to-indigo-500";

interface PaperCardProps {
  paper: Paper;
  index: number;
  savedPapers?: import("@/types/paper").SavedPaper[];
  fromSearch?: boolean;
  fromPage?: string;
}

export function PaperCard({
  paper,
  index,
  savedPapers,
  fromSearch,
  fromPage,
}: PaperCardProps) {
  const { accessToken } = useAuth();
  const queryClient = useQueryClient();

  const safeDate = paper.date ? new Date(paper.date) : null;
  const formattedDate = safeDate
    ? safeDate.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "Date pending";

  const isSaved = savedPapers?.some((sp) => sp.arxiv_id === paper.id);
  const savedPaperData = savedPapers?.find((sp) => sp.arxiv_id === paper.id);
  const isIngested = savedPaperData?.ingested ?? false;

  const savePaperMutation = useMutation({
    mutationFn: () => savePaper(paper, accessToken),
    onSuccess: () => {
      toast.success("Paper saved successfully!");
      const ingestToastId = toast.loading(`Ingesting "${paper.title}"`, {
        description: "Hang tight while we process this PDF.",
        duration: Infinity,
      });
      ingestPaper({
        paperUrl: paper.pdfUrl,
        arxivId: paper.id,
        token: accessToken,
      })
        .then(() => {
          toast.success(
            "Document ingested successfully! You can now chat with this paper.",
            { id: ingestToastId },
          );
        })
        .catch((error) => {
          const errorMsg = error instanceof Error
            ? error.message
            : typeof error === 'object' && error?.message
              ? error.message
              : "Unknown error occurred";
          toast.error(`Failed to ingest document: ${errorMsg}`, {
            id: ingestToastId,
          });
          // Refresh saved papers to update ingestion status
          queryClient.invalidateQueries({ queryKey: ["savedPapers"] });
        });
      queryClient.invalidateQueries({ queryKey: ["savedPapers"] });
    },
    onError: (error) => {
      toast.error(`Failed to save paper: ${error.message}`);
    },
  });

  const handleSavePaper = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    savePaperMutation.mutate();
  };
  const cardGradient = useMemo(() => {
    const cat = paper.primaryCategory || paper.topics?.[0] || "";
    return CATEGORY_GRADIENTS[cat] || DEFAULT_GRADIENT;
  }, [paper.primaryCategory, paper.topics]);

  const displayAuthors = useMemo(() => {
    if (paper.authors.length <= 2) return paper.authors.join(", ");
    return `${paper.authors[0]}, ${paper.authors[1]}`;
  }, [paper.authors]);

  return (
    <HoverCard openDelay={3000}>
      <HoverCardTrigger asChild>
        <Link
          to={`/paper/${paper.id}`}
          state={{ paper, ...(fromSearch && { fromSearch }), ...(fromPage && { fromPage }) }}
        >
          <Card
            className={`group h-full cursor-pointer transition-all duration-300 hover:shadow-lg hover:-translate-y-1 hover:border-primary/50 animate-fade-in stagger-${(index % 6) + 1} overflow-hidden`}
          >
            <div className={`relative -mt-4 px-5 pt-5 pb-4 bg-linear-to-br ${cardGradient} flex flex-col justify-between min-h-[180px]`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-xs font-medium text-white/70 tracking-wide shrink-0">
                    {paper.primaryCategory || "arXiv"}
                  </span>
                  <span className="text-xs text-white/50 truncate">
                    {paper.id}
                  </span>
                </div>
                <Button
                  size="icon"
                  onClick={handleSavePaper}
                  disabled={isSaved || savePaperMutation.isPending}
                  className={`size-8 border-0 shadow-none backdrop-blur-sm ${
                    isSaved
                      ? "bg-white/10 text-white/40 cursor-default"
                      : "bg-white text-indigo-700 hover:bg-white/90 hover:scale-110 transition-transform"
                  }`}
                >
                  {savePaperMutation.isPending ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : isSaved ? (
                    <BookmarkCheck className="size-4" />
                  ) : (
                    <BookmarkPlus className="size-4" />
                  )}
                </Button>
              </div>

              <h3 className="font-bold text-base leading-snug text-white line-clamp-3 mt-2">
                {paper.title}
              </h3>

              <div className="flex items-center gap-2 mt-3 text-xs text-white/70">
                <span className="truncate">{displayAuthors}</span>
                <span className="shrink-0">&middot;</span>
                <span className="shrink-0">{formattedDate}</span>
              </div>
            </div>

            <CardContent className="pt-3 pb-3 space-y-2">
              <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
                {paper.abstract || "No abstract available."}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {paper.topics.slice(0, 2).map((topic) => (
                  <Badge key={topic} variant="secondary" className="text-xs">
                    {topic}
                  </Badge>
                ))}
                {paper.topics.length > 2 && (
                  <Badge variant="outline" className="text-xs">
                    +{paper.topics.length - 2}
                  </Badge>
                )}
                {isSaved && isIngested && (
                  <Badge
                    variant="outline"
                    className="ml-auto shrink-0 gap-1 border-green-500/40 bg-green-500/10 text-green-600 dark:text-green-400"
                  >
                    <CheckCircle2 className="w-3 h-3" />
                    Ready
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        </Link>
      </HoverCardTrigger>

      <HoverCardContent side="right" align="center" className="w-96 p-0">
        <PaperHoverCard paper={paper} />
      </HoverCardContent>
    </HoverCard>
  );
}
