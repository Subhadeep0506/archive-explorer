import { Paper } from '@/types/paper';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Calendar, Building2, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';

interface PaperCardProps {
  paper: Paper;
  index: number;
}

export function PaperCard({ paper, index }: PaperCardProps) {
  const formattedDate = new Date(paper.date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <Link to={`/paper/${paper.id}`}>
      <Card
        className={`group h-full cursor-pointer transition-all duration-300 hover:shadow-lg hover:-translate-y-1 animate-fade-in stagger-${(index % 6) + 1}`}
        style={{ opacity: 0 }}
      >
        <div className="aspect-[16/9] bg-gradient-to-br from-primary/10 via-primary/5 to-accent rounded-t-lg overflow-hidden relative">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center p-4">
              <div className="w-16 h-16 mx-auto mb-3 rounded-xl bg-primary/10 flex items-center justify-center">
                <span className="text-2xl font-bold text-primary">
                  {paper.title.charAt(0)}
                </span>
              </div>
              <p className="text-xs text-muted-foreground line-clamp-2">
                {paper.abstract.slice(0, 80)}...
              </p>
            </div>
          </div>
        </div>
        <CardHeader className="pb-2">
          <h3 className="font-semibold text-base leading-snug line-clamp-2 group-hover:text-primary transition-colors">
            {paper.title}
          </h3>
        </CardHeader>
        <CardContent className="pt-0 space-y-3">
          <p className="text-sm text-muted-foreground line-clamp-2">
            {paper.authors.join(', ')}
          </p>
          
          <div className="flex flex-wrap gap-1.5">
            {paper.topics.slice(0, 2).map((topic) => (
              <Badge key={topic} variant="secondary" className="text-xs">
                {topic}
              </Badge>
            ))}
            {paper.topics.length > 2 && (
              <Badge variant="outline" className="text-xs">
                +{paper.topics.length - 2}
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2 border-t">
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              {formattedDate}
            </span>
            <span className="flex items-center gap-1 truncate">
              <Building2 className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="truncate">{paper.institution}</span>
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
