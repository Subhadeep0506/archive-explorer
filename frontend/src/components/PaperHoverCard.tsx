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
    <div className="w-full rounded-lg bg-card p-5">
      {/* Header with title and date */}
      <div className="space-y-3 mb-4">
        <h3 className="font-bold text-base leading-tight line-clamp-3 text-card-foreground">
          {paper.title}
        </h3>
        <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
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
        <div className="max-h-48 overflow-y-auto scrollbar-styled">
          <p className="text-sm text-card-foreground/80 leading-relaxed pr-2">
            {paper.abstract || "Abstract not available"}
          </p>
        </div>
      </div>

      {/* Authors */}
      <div className="mb-4 pb-4 border-b border-border/50">
        <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide flex items-center gap-2">
          <Users className="w-3.5 h-3.5" />
          Authors
        </p>
        <p className="text-sm text-card-foreground/80 line-clamp-2">
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
    </div>
  );
}
