import { FileText, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

interface PdfPreviewPopoverProps {
  pdfUrl: string;
  children: React.ReactNode;
}

export function PdfPreviewPopover({ pdfUrl, children }: PdfPreviewPopoverProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>{children}</PopoverTrigger>
      <PopoverContent className="w-[500px] p-0" align="start" side="bottom">
        <div className="border-b p-3 flex items-center justify-between bg-muted/50">
          <span className="text-sm font-medium flex items-center gap-2">
            <FileText className="w-4 h-4 text-chip-coral" />
            PDF Preview
          </span>
          <a href={pdfUrl} target="_blank" rel="noopener noreferrer">
            <Button variant="ghost" size="sm">
              Open Full PDF
              <ExternalLink className="w-3 h-3 ml-2" />
            </Button>
          </a>
        </div>
        <div className="aspect-[3/4] bg-muted flex items-center justify-center">
          <div className="text-center p-8">
            <div className="w-20 h-28 mx-auto mb-4 bg-background rounded-lg shadow-lg flex items-center justify-center border">
              <FileText className="w-10 h-10 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground text-sm mb-3">PDF Preview</p>
            <a href={pdfUrl} target="_blank" rel="noopener noreferrer">
              <Button size="sm" className="bg-chip-coral hover:bg-chip-coral/90">
                View PDF
                <ExternalLink className="w-3 h-3 ml-2" />
              </Button>
            </a>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
