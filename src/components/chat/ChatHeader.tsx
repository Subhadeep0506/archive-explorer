import { ArrowLeft, FileText, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PdfPreviewDialog } from './PdfPreviewDialog';

interface ChatHeaderProps {
  title: string;
  pdfUrl: string;
  onBack: () => void;
  onSummarize: () => void;
}

export function ChatHeader({ title, pdfUrl, onBack, onSummarize }: ChatHeaderProps) {
  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 py-3">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <Button variant="ghost" size="icon" onClick={onBack} className="shrink-0">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <h1 className="font-semibold truncate">{title}</h1>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <PdfPreviewDialog pdfUrl={pdfUrl}>
            <Button variant="outline" size="sm">
              <FileText className="w-4 h-4 mr-2 text-chip-coral" />
              View PDF
            </Button>
          </PdfPreviewDialog>

          <Button 
            variant="outline" 
            size="sm" 
            onClick={onSummarize}
            className="border-chip-violet text-chip-violet hover:bg-chip-violet hover:text-white"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Summarize
          </Button>
        </div>
      </div>
    </header>
  );
}
