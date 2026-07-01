import { FileText, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PdfViewer } from '@/components/ui/pdf-viewer';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

interface PdfPreviewDialogProps {
  pdfUrl: string;
  children: React.ReactNode;
}

export function PdfPreviewDialog({ pdfUrl, children }: PdfPreviewDialogProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="max-w-4xl w-[90vw] h-[90vh] p-0 flex flex-col overflow-hidden">
        <DialogHeader className="p-4 border-b bg-muted/50">
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2 text-base">
              <FileText className="w-5 h-5 text-chip-coral" />
              PDF Preview
            </DialogTitle>
            <a href={pdfUrl} target="_blank" rel="noopener noreferrer">
              <Button variant="ghost" size="sm">
                Open Full PDF
                <ExternalLink className="w-3 h-3 ml-2" />
              </Button>
            </a>
          </div>
        </DialogHeader>
        <div className="flex-1 min-h-0 overflow-hidden">
          <PdfViewer url={pdfUrl} />
        </div>
      </DialogContent>
    </Dialog>
  );
}
