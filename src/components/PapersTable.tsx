import { Paper } from '@/types/paper';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { FileText, Globe, Github, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

interface PapersTableProps {
  papers: Paper[];
}

export function PapersTable({ papers }: PapersTableProps) {
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
          {papers.map((paper) => (
            <TableRow
              key={paper.id}
              className="group hover:bg-muted/30 transition-colors"
            >
              <TableCell>
                <Link
                  to={`/paper/${paper.id}`}
                  className="font-medium text-foreground hover:text-primary transition-colors line-clamp-2"
                >
                  {paper.title}
                </Link>
                <p className="text-xs text-muted-foreground mt-1">
                  {paper.authors.slice(0, 2).join(', ')}
                  {paper.authors.length > 2 && ` +${paper.authors.length - 2}`}
                </p>
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {new Date(paper.date).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                })}
              </TableCell>
              <TableCell>
                <Link to={`/paper/${paper.id}`}>
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
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
