import { useMemo } from "react";
import { AlertCircle, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Paper } from "@/types/paper";

interface PaperPdfViewerProps {
  paper: Paper;
  height?: number;
}

export function PaperPdfViewer({ paper, height = 700 }: PaperPdfViewerProps) {
  const fileUrl =
    paper.pdfUrl && paper.pdfUrl !== "#" ? paper.pdfUrl : undefined;

  if (!fileUrl) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border bg-muted/30 p-8 text-center">
        <AlertCircle className="h-10 w-10 text-muted-foreground" />
        <div>
          <p className="text-sm font-medium text-foreground">
            PDF not available
          </p>
          <p className="text-xs text-muted-foreground">
            We could not locate a PDF for this paper yet.
          </p>
        </div>
        {paper.htmlUrl && (
          <Button asChild size="sm">
            <a href={paper.htmlUrl} target="_blank" rel="noreferrer">
              Open HTML Version
            </a>
          </Button>
        )}
      </div>
    );
  }

  return (
    <div
      className="rounded-lg border bg-card overflow-hidden"
      style={{ height: height }}
    >
      <iframe
        src={fileUrl}
        width="100%"
        height="100%"
        style={{ border: "none" }}
        title={`PDF Viewer for ${paper.title}`}
      />
    </div>
  );
}
