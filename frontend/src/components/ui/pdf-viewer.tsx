import { Viewer, Worker } from "@react-pdf-viewer/core";
import { defaultLayoutPlugin } from "@react-pdf-viewer/default-layout";
import workerUrl from "pdfjs-dist/legacy/build/pdf.worker.min.js?url";
import { AlertCircle, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/useTheme";
import { cn } from "@/lib/utils";

interface PdfViewerProps {
  url: string;
  className?: string;
}

export function PdfViewer({ url, className }: PdfViewerProps) {
  const { theme } = useTheme();
  const defaultLayoutPluginInstance = defaultLayoutPlugin();

  // Parse #page=N fragment — @react-pdf-viewer uses initialPage (0-indexed)
  // instead of URL fragments for page navigation.
  const hashMatch = url.match(/#page=(\d+)/i);
  const initialPage = hashMatch ? Math.max(0, parseInt(hashMatch[1], 10) - 1) : 0;
  const fileUrl = url.split("#")[0];

  return (
    <Worker workerUrl={workerUrl}>
      <div
        className={cn(
          "rpv-core__viewer h-full",
          theme === "dark" && "rpv-core__viewer--dark",
          className,
        )}
      >
        <Viewer
          fileUrl={fileUrl}
          initialPage={initialPage}
          plugins={[defaultLayoutPluginInstance]}
          renderError={() => (
            <div className="flex flex-col items-center justify-center gap-3 h-full p-8 text-center">
              <AlertCircle className="h-10 w-10 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Failed to load PDF</p>
              <Button asChild size="sm" variant="outline">
                <a href={fileUrl} target="_blank" rel="noreferrer">
                  <ExternalLink className="w-3 h-3 mr-2" /> Open in browser
                </a>
              </Button>
            </div>
          )}
        />
      </div>
    </Worker>
  );
}
