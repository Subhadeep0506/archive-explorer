import { useMemo } from "react";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PdfViewer } from "@/components/ui/pdf-viewer";
import { API_BASE_URL } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import type { Paper } from "@/types/paper";

const ARXIV_PDF_RE = /^https?:\/\/arxiv\.org\/pdf\/(\d{4}\.\d{4,5}(?:v\d+)?)/;

interface PaperPdfViewerProps {
  paper: Paper;
  height?: number;
}

export function PaperPdfViewer({ paper, height = 700 }: PaperPdfViewerProps) {
  const { accessToken } = useAuth();

  const fileUrl = useMemo(() => {
    const raw = paper.pdfUrl && paper.pdfUrl !== "#" ? paper.pdfUrl : undefined;
    if (!raw) return undefined;
    const match = raw.match(ARXIV_PDF_RE);
    if (match) {
      const proxyUrl = `${API_BASE_URL}/arxiv/pdf/${match[1]}`;
      return accessToken ? `${proxyUrl}?token=${accessToken}` : proxyUrl;
    }
    return raw;
  }, [paper.pdfUrl, accessToken]);

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
      <PdfViewer url={fileUrl} className="h-full" />
    </div>
  );
}
