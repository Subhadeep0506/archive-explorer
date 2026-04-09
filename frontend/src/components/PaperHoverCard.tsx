import { Paper } from "@/types/paper";
import { Badge } from "@/components/ui/badge";
import { Calendar, Building2, Users } from "lucide-react";

interface PaperHoverCardProps {
  paper: Paper;
}

export function PaperHoverCard({ paper }: PaperHoverCardProps) {
  const safeDate = paper.date ? new Date(paper.date) : null;
  const formattedDate = safeDate
    ? safeDate.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "Date pending";

  const institutionLabel = paper.institution || paper.primaryCategory || "arXiv";

  return (
    <div className="pointer-events-none w-96 rounded-lg border border-border bg-background/95 backdrop-blur-sm shadow-2xl p-5 animate-in fade-in zoom-in-95 duration-200">
      {/* Header with title and date */}
      <div className="space-y-3 mb-4">
        <h3 className="font-bold text-base leading-tight line-clamp-3 text-foreground">
          {paper.title}
        </h3>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            {formattedDate}
          </span>
          <span className="flex items-center gap-1 truncate">
            <Building2 className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="truncate">{institutionLabel}</span>
          </span>
        </div>
      </div>

      {/* Abstract */}
      <div className="mb-4 pb-4 border-b border-border/50">
        <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
          Abstract
        </p>
        <p className="text-sm text-foreground/80 line-clamp-5 leading-relaxed">
          {paper.abstract || "Abstract not available"}
        </p>
      </div>

      {/* Authors */}
      <div className="mb-4 pb-4 border-b border-border/50">
        <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide flex items-center gap-2">
          <Users className="w-3.5 h-3.5" />
          Authors
        </p>
        <p className="text-sm text-foreground/80 line-clamp-2">
          {paper.authors.slice(0, 3).join(", ")}
          {paper.authors.length > 3 && ` +${paper.authors.length - 3} more`}
        </p>
      </div>

      {/* Topics */}
      <div>
        <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
          Topics
        </p>
        <div className="flex flex-wrap gap-1.5">
          {paper.topics.slice(0, 4).map((topic) => (
            <Badge key={topic} variant="secondary" className="text-xs">
              {topic}
            </Badge>
          ))}
          {paper.topics.length > 4 && (
            <Badge variant="outline" className="text-xs">
              +{paper.topics.length - 4}
            </Badge>
          )}
        </div>
      </div>

      {/* Arrow indicator */}
      <div className="absolute -left-2 top-6 w-0 h-0 border-l-[8px] border-r-0 border-t-[6px] border-b-[6px] border-l-background/95 border-t-transparent border-b-transparent" />
    </div>
  );
}
