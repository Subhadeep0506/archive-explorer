import { Paper } from "@/types/paper";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Globe,
  Github,
  Sparkles,
  BookmarkPlus,
  Loader2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { savePaper, ingestPaper } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

interface PapersTableProps {
  papers: Paper[];
  savedPapers?: import("@/types/paper").SavedPaper[];
  fromSearch?: boolean;
}

export function PapersTable({
  papers,
  savedPapers,
  fromSearch,
}: PapersTableProps) {
  const { accessToken } = useAuth();
  const queryClient = useQueryClient();

  const savePaperMutation = useMutation({
    mutationFn: (paper: Paper) => savePaper(paper, accessToken),
    onSuccess: (_, paper) => {
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
          toast.error(`Failed to ingest document: ${error.message}`, {
            id: ingestToastId,
          });
        });
      queryClient.invalidateQueries({ queryKey: ["savedPapers"] });
    },
    onError: (error) => {
      toast.error(`Failed to save paper: ${error.message}`);
    },
  });

  const handleSavePaper = (paper: Paper) => {
    savePaperMutation.mutate(paper);
  };

  return (
    <div className="rounded-lg border bg-card overflow-hidden animate-fade-in">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50">
            <TableHead className="w-[40%]">Title</TableHead>
            <TableHead className="w-[12%]">Date</TableHead>
            <TableHead className="w-[28%]">Summary</TableHead>
            <TableHead className="w-[20%] text-center">Links</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {papers.map((paper) => {
            const safeDate = paper.date ? new Date(paper.date) : null;
            const shortDate = safeDate
              ? safeDate.toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                })
              : "—";
            const isSaved = savedPapers?.some((sp) => sp.arxiv_id === paper.id);

            return (
              <TableRow
                key={paper.id}
                className="group hover:bg-muted/30 transition-colors"
              >
                <TableCell>
                  <Link
                    to={`/paper/${paper.id}`}
                    state={{ paper, ...(fromSearch && { fromSearch }) }}
                    className="font-medium text-foreground hover:text-primary transition-colors line-clamp-2"
                  >
                    {paper.title}
                  </Link>
                  <p className="text-xs text-muted-foreground mt-1">
                    {paper.authors.slice(0, 2).join(", ")}
                    {paper.authors.length > 2 &&
                      ` +${paper.authors.length - 2}`}
                  </p>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {shortDate}
                </TableCell>
                <TableCell>
                  <Link
                    to={`/paper/${paper.id}`}
                    state={{ paper, ...(fromSearch && { fromSearch }) }}
                  >
                    <Badge
                      variant="outline"
                      className="cursor-pointer bg-chip-violet-bg text-chip-violet border-chip-violet/30 hover:bg-chip-violet hover:text-white transition-colors"
                    >
                      <Sparkles className="w-3 h-3 mr-1" />
                      AI Summary
                    </Badge>
                  </Link>
                </TableCell>
                <TableCell>
                  <div className="flex items-center justify-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSavePaper(paper);
                      }}
                      disabled={isSaved || savePaperMutation.isPending}
                      className="cursor-pointer bg-chip-amber-bg text-chip-amber border-chip-amber/30 hover:bg-chip-amber hover:text-white transition-colors h-6 px-2"
                    >
                      {savePaperMutation.isPending ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <BookmarkPlus className="w-3 h-3" />
                      )}
                    </Button>
                    <a
                      href={paper.pdfUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Badge
                        variant="outline"
                        className="cursor-pointer bg-chip-coral-bg text-chip-coral border-chip-coral/30 hover:bg-chip-coral hover:text-white transition-colors"
                      >
                        <FileText className="w-3 h-3 mr-1" />
                        PDF
                      </Badge>
                    </a>
                    {paper.htmlUrl && (
                      <a
                        href={paper.htmlUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer bg-chip-blue-bg text-chip-blue border-chip-blue/30 hover:bg-chip-blue hover:text-white transition-colors"
                        >
                          <Globe className="w-3 h-3 mr-1" />
                          HTML
                        </Badge>
                      </a>
                    )}
                    {paper.githubUrl && (
                      <a
                        href={paper.githubUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Badge
                          variant="outline"
                          className="cursor-pointer bg-chip-emerald-bg text-chip-emerald border-chip-emerald/30 hover:bg-chip-emerald hover:text-white transition-colors"
                        >
                          <Github className="w-3 h-3 mr-1" />
                          Code
                        </Badge>
                      </a>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
