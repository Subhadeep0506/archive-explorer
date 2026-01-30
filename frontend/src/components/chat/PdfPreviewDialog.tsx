import { FileText, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
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
      <DialogContent className="max-w-2xl w-[90vw] max-h-[85vh] p-0 flex flex-col overflow-hidden">
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
        <div className="flex-1 min-h-0 bg-muted flex items-center justify-center overflow-auto">
          <div className="text-center p-8">
            <div className="w-24 h-32 mx-auto mb-4 bg-background rounded-lg shadow-lg flex items-center justify-center border">
              <FileText className="w-12 h-12 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground text-sm mb-4">PDF Preview</p>
            <a href={pdfUrl} target="_blank" rel="noopener noreferrer">
              <Button size="sm" className="bg-chip-coral hover:bg-chip-coral/90">
                View PDF
                <ExternalLink className="w-3 h-3 ml-2" />
              </Button>
            </a>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
