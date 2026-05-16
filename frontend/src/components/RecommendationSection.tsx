import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  HoverCard,
  HoverCardTrigger,
  HoverCardContent,
} from "@/components/ui/hover-card";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselPrevious,
  CarouselNext,
} from "@/components/ui/carousel";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Lightbulb, AlertCircle, Layers, Compass, Users } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { getRecommendations } from "@/lib/api";
import { normalizeRecommendationItem } from "@/lib/papers";
import { PaperHoverCard } from "@/components/PaperHoverCard";
import {
  CATEGORY_GRADIENTS,
  DEFAULT_GRADIENT,
} from "@/components/PaperCard";
import type { Paper, RecommendationItem } from "@/types/paper";

interface RecommendationSectionProps {
  paper: Paper;
}

function RecCard({ item }: { item: RecommendationItem }) {
  const paper = normalizeRecommendationItem(item);
  const gradient = useMemo(() => {
    const cat = item.primary_category || "";
    return CATEGORY_GRADIENTS[cat] || DEFAULT_GRADIENT;
  }, [item.primary_category]);

  const formattedDate = item.published_date
    ? new Date(item.published_date).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "";

  const displayAuthors =
    paper.authors.slice(0, 2).join(", ") +
    (paper.authors.length > 2 ? ` +${paper.authors.length - 2}` : "");

  return (
    <HoverCard openDelay={400}>
      <HoverCardTrigger asChild>
        <Link to={`/paper/${paper.id}`} state={{ paper }} className="block h-full">
          <div className="group h-full rounded-lg border bg-card overflow-hidden transition-colors duration-200 hover:border-primary/50">
            <div
              className={`relative px-3.5 pt-3 pb-2.5 bg-linear-to-br ${gradient} flex flex-col justify-between min-h-32`}
            >
              <span className="text-[10px] font-medium text-white/70 tracking-wide">
                {item.primary_category || "arXiv"}
              </span>
              <h4 className="font-semibold text-sm leading-snug text-white line-clamp-3 mt-1">
                {item.title}
              </h4>
              <div className="flex items-center gap-1.5 mt-2 text-[10px] text-white/70">
                <span className="truncate">{displayAuthors}</span>
                {formattedDate && (
                  <>
                    <span className="shrink-0">&middot;</span>
                    <span className="shrink-0">{formattedDate}</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </Link>
      </HoverCardTrigger>
      <HoverCardContent side="left" sideOffset={8} className="w-80 p-0">
        <PaperHoverCard paper={paper} />
      </HoverCardContent>
    </HoverCard>
  );
}

function RecCarousel({
  title,
  icon,
  items,
}: {
  title: string;
  icon: React.ReactNode;
  items: RecommendationItem[];
}) {
  if (items.length === 0) return null;

  return (
    <Carousel opts={{ align: "start", dragFree: true }}>
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <Badge variant="secondary" className="text-xs">
          {items.length}
        </Badge>
        <div className="ml-auto flex items-center gap-1">
          <CarouselPrevious className="static translate-x-0 translate-y-0" />
          <CarouselNext className="static translate-x-0 translate-y-0" />
        </div>
      </div>
      <CarouselContent>
        {items.map((item, i) => (
          <CarouselItem
            key={item.arxiv_id || i}
            className="basis-56 md:basis-60"
          >
            <RecCard item={item} />
          </CarouselItem>
        ))}
      </CarouselContent>
    </Carousel>
  );
}

function CarouselSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-4 w-32" />
      <div className="flex gap-4">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-32 w-56 rounded-lg shrink-0" />
        ))}
      </div>
    </div>
  );
}

export function RecommendationSection({ paper }: RecommendationSectionProps) {
  const { accessToken } = useAuth();

  const {
    data: recommendations,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["recommendations", paper.id],
    queryFn: () => getRecommendations(paper, accessToken),
    enabled: Boolean(paper.id && accessToken),
    staleTime: 1000 * 60 * 15,
    gcTime: 1000 * 60 * 60,
    refetchOnWindowFocus: false,
  });

  const hasResults =
    recommendations &&
    (recommendations.similar_papers.length > 0 ||
      recommendations.on_this_topic.length > 0 ||
      recommendations.from_these_authors.length > 0);

  return (
    <Card className="animate-fade-in" style={{ animationDelay: "0.2s" }}>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-amber-500" />
          Recommendations
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading ? (
          <>
            <CarouselSkeleton />
            <CarouselSkeleton />
          </>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center gap-3 py-6 text-center">
            <AlertCircle className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Failed to load recommendations
            </p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        ) : hasResults ? (
          <>
            <RecCarousel
              title="Similar Papers"
              icon={<Layers className="w-4 h-4 text-muted-foreground" />}
              items={recommendations!.similar_papers}
            />
            <RecCarousel
              title="On This Topic"
              icon={<Compass className="w-4 h-4 text-muted-foreground" />}
              items={recommendations!.on_this_topic}
            />
            <RecCarousel
              title="From These Authors"
              icon={<Users className="w-4 h-4 text-muted-foreground" />}
              items={recommendations!.from_these_authors}
            />
          </>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-4">
            No recommendations found for this paper
          </p>
        )}
      </CardContent>
    </Card>
  );
}
