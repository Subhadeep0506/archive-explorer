import { useMemo, useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import {
  useInfiniteQuery,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { Loader2, Search, RefreshCw } from "lucide-react";
import { FilterSidebar } from "@/components/FilterSidebar";
import { ViewToggle } from "@/components/ViewToggle";
import { PaperCard } from "@/components/PaperCard";
import { PapersTable } from "@/components/PapersTable";
import { Filters, FilterOption, Paper, ViewMode } from "@/types/paper";
import { ArxivEntry } from "@/types/arxiv";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { fetchArxivFeed, DEFAULT_TOPICS } from "@/lib/arxiv";
import { useAuth } from "@/context/AuthContext";
import { useUserData } from "@/context/UserDataContext";
import { useSearch } from "@/context/SearchContext";
import { normalizeArxivEntry } from "@/lib/papers";
import { getSavedPapers } from "@/lib/api";

export default function Index() {
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<Filters>({ topics: [], years: [] });
  const { accessToken } = useAuth();
  const { profile } = useUserData();
  const { setIsDialogOpen } = useSearch();
  const location = useLocation();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (location.state?.openSearchDialog) {
      setIsDialogOpen(true);
    }
  }, [location.state, setIsDialogOpen]);

  const { data: savedPapers } = useQuery({
    queryKey: ["savedPapers"],
    queryFn: () => getSavedPapers(accessToken),
    enabled: Boolean(accessToken),
  });

  const topicsToUse = useMemo(() => {
    if (filters.topics.length > 0) return filters.topics;
    if (profile?.topic_preferences) {
      return profile.topic_preferences
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
    }
    return DEFAULT_TOPICS;
  }, [filters.topics, profile]);

  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ["papers", topicsToUse.join(",")],
    queryFn: ({ pageParam }: { pageParam: number }) =>
      fetchArxivFeed(
        { topics: topicsToUse, start: pageParam, max_results: 24 },
        accessToken,
      ),
    initialPageParam: 0,
    getNextPageParam: (lastPage: ArxivEntry[], allPages: ArxivEntry[][]) => {
      if (lastPage.length < 24) return undefined;
      return allPages.length * 24;
    },
    enabled: Boolean(accessToken),
    staleTime: 1000 * 60 * 60, // 1 hour
  });

  const papers: Paper[] = useMemo(() => {
    if (!data) return [];
    return data.pages.flat().map(normalizeArxivEntry);
  }, [data]);

  const topicFilters = useMemo(() => buildTopicFilters(papers), [papers]);
  const yearFilters = useMemo(() => buildYearFilters(papers), [papers]);

  const filteredPapers = useMemo(() => {
    return papers.filter((paper) => {
      const matchesSearch =
        searchQuery === "" ||
        paper.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        paper.abstract.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesYear =
        filters.years.length === 0 ||
        filters.years.some((year) => paper.date?.startsWith(year));

      return matchesSearch && matchesYear;
    });
  }, [papers, searchQuery, filters.years]);

  const handleFiltersChange = (newFilters: Filters) => {
    setFilters(newFilters);
  };

  return (
    <div className="h-[calc(100vh-4rem)] bg-background flex flex-col">
      <div className="flex flex-1 overflow-hidden">
        <FilterSidebar
          topicFilters={topicFilters}
          yearFilters={yearFilters}
          filters={filters}
          onFiltersChange={handleFiltersChange}
        />

        <main className="flex-1 p-6 overflow-y-auto">
          <div className="mb-6">
            <div className="flex items-center justify-between gap-4 mb-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search papers... (Cmd+K)"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                  }}
                  className="pl-10"
                />
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    queryClient.invalidateQueries({
                      queryKey: ["papers", topicsToUse.join(",")],
                    })
                  }
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
                <ViewToggle mode={viewMode} onModeChange={setViewMode} />
              </div>
            </div>

            <p className="text-sm text-muted-foreground">
              Showing {filteredPapers.length} papers
              {filters.years.length > 0 && " (filtered)"}
            </p>
          </div>

          {isLoading ? (
            <div className="flex h-64 items-center justify-center text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          ) : isError ? (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-6 text-destructive">
              {(error as Error)?.message || "Unable to load papers"}
            </div>
          ) : viewMode === "grid" ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredPapers.map((paper, index) => (
                <PaperCard
                  key={paper.id}
                  paper={paper}
                  index={index}
                  savedPapers={savedPapers}
                  fromPage="/app"
                />
              ))}
            </div>
          ) : (
            <PapersTable papers={filteredPapers} savedPapers={savedPapers} fromPage="/app" />
          )}

          {filteredPapers.length === 0 && !isLoading && (
            <div className="text-center py-12">
              <Search className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-lg text-muted-foreground mb-2">
                No papers found matching your criteria
              </p>
              <p className="text-sm text-muted-foreground mb-6">
                Try adjusting your filters or search query
              </p>
              {(searchQuery || filters.years.length > 0) && (
                <Button
                  variant="outline"
                  onClick={() => {
                    setSearchQuery("");
                    setFilters({ topics: [], years: [] });
                  }}
                >
                  Clear search and filters
                </Button>
              )}
            </div>
          )}

          {hasNextPage && (
            <div className="flex justify-center mt-6">
              <Button
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
              >
                {isFetchingNextPage ? "Loading..." : "Load More"}
              </Button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

const colorRamp: FilterOption["color"][] = [
  "coral",
  "violet",
  "teal",
  "amber",
  "blue",
  "rose",
  "emerald",
];

const buildTopicFilters = (papers: Paper[]): FilterOption[] => {
  const counts = new Map<string, number>();
  papers.forEach((paper) => {
    paper.topics.forEach((topic) => {
      counts.set(topic, (counts.get(topic) || 0) + 1);
    });
  });

  const fallbackTopics = DEFAULT_TOPICS.map((topic) => [topic, 0] as const);
  const entries = counts.size ? Array.from(counts.entries()) : fallbackTopics;

  return entries
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12)
    .map(([topic, count], index) => ({
      id: topic,
      label: topic,
      value: topic,
      count,
      color: colorRamp[index % colorRamp.length],
    }));
};

const buildYearFilters = (papers: Paper[]): FilterOption[] => {
  const counts = new Map<string, number>();
  papers.forEach((paper) => {
    if (!paper.date) return;
    const year = paper.date.slice(0, 4);
    counts.set(year, (counts.get(year) || 0) + 1);
  });

  return Array.from(counts.entries())
    .sort((a, b) => Number(b[0]) - Number(a[0]))
    .slice(0, 6)
    .map(([year, count], index) => ({
      id: year,
      label: year,
      value: year,
      count,
      color: colorRamp[index % colorRamp.length],
    }));
};
