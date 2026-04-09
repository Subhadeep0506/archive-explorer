import { Paper } from "@/types/paper";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Calendar,
  Building2,
  MapPin,
  BookmarkPlus,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { savePaper, ingestPaper } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";
import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { PaperHoverCard } from "@/components/PaperHoverCard";

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
  const [showHoverCard, setShowHoverCard] = useState(false);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });
  const hoverTimeoutRef = useRef<NodeJS.Timeout>();
  const cardRef = useRef<HTMLDivElement>(null);

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

  const handleMouseEnter = () => {
    if (cardRef.current) {
      const rect = cardRef.current.getBoundingClientRect();
      const cardWidth = 384; // w-96 = 24rem = 384px
      const cardHeight = 400; // approximate height of hover card
      const gap = 16; // 16px gap

      // Calculate positions
      let x = rect.right + gap;
      let y = rect.top + rect.height / 2 - cardHeight / 2;

      // Check if card goes off screen on the right
      if (x + cardWidth > window.innerWidth) {
        // Show on the left instead
        x = rect.left - cardWidth - gap;
      }

      // Check if card goes off screen on the bottom
      if (y + cardHeight > window.innerHeight) {
        // Adjust to stay within viewport
        y = window.innerHeight - cardHeight - 16;
      }

      // Check if card goes off screen on the top
      if (y < 0) {
        y = 16;
      }

      setHoverPosition({ x, y });
    }

    hoverTimeoutRef.current = setTimeout(() => {
      setShowHoverCard(true);
    }, 3000);
  };

  const handleMouseLeave = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    setShowHoverCard(false);
  };

  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

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
  const institutionLabel =
    paper.institution || paper.primaryCategory || "arXiv";
  const abstractPreview = paper.abstract
    ? `${paper.abstract.slice(0, 80)}...`
    : "Snapshot unavailable";

  return (
    <>
      <Link
        to={`/paper/${paper.id}`}
        state={{ paper, ...(fromSearch && { fromSearch }), ...(fromPage && { fromPage }) }}
      >
        <Card
          ref={cardRef}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          className={`group h-full cursor-pointer transition-all duration-300 hover:shadow-lg hover:-translate-y-1 hover:border-primary/50 animate-fade-in stagger-${(index % 6) + 1}`}
          style={{ opacity: 0 }}
        >
        <div className="aspect-[16/9] rounded-t-lg overflow-hidden relative">
          {paper.thumbnailUrl ? (
            <img
              src={paper.thumbnailUrl}
              alt={paper.title}
              className="h-full w-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="h-full w-full bg-gradient-to-br from-primary/10 via-primary/5 to-accent" />
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-background/0" />
          <div className="absolute bottom-3 left-3 right-3 text-xs text-black/80 dark:text-white/80 line-clamp-2">
            {abstractPreview}
          </div>
        </div>
        <CardHeader className="pb-2 relative">
          <h3 className="font-semibold text-base leading-snug line-clamp-2 group-hover:text-primary transition-colors pr-24">
            {paper.title}
          </h3>
          <div className="absolute top-2 right-2 z-10 flex items-center gap-1">
            {isSaved && isIngested && (
              <div className="flex items-center gap-0.5 px-2 py-1 bg-background border border-border rounded text-xs">
                <CheckCircle2 className="w-3 h-3 text-green-500" />
                <span className="text-green-600 dark:text-green-400">Ready</span>
              </div>
            )}
            <Button
              size="sm"
              onClick={handleSavePaper}
              disabled={isSaved || savePaperMutation.isPending}
              className="bg-chip-amber hover:bg-chip-amber/90 text-white h-8 w-8 p-0"
            >
              {savePaperMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <BookmarkPlus className="w-4 h-4" />
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0 space-y-3">
          <p className="text-sm text-muted-foreground line-clamp-2">
            {paper.authors.join(", ")}
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
          </div>

          <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2 border-t">
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              {formattedDate}
            </span>
            <span className="flex items-center gap-1 truncate">
              <Building2 className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="truncate">{institutionLabel}</span>
            </span>
          </div>
        </CardContent>
        </Card>
      </Link>

      {/* Hover Card - Rendered via Portal to avoid stacking context issues */}
      {showHoverCard &&
        createPortal(
          <div
            style={{
              position: "fixed",
              left: `${hoverPosition.x}px`,
              top: `${hoverPosition.y}px`,
              zIndex: 9999,
            }}
          >
            <PaperHoverCard paper={paper} />
          </div>,
          document.body
        )}
    </>
  );
}
