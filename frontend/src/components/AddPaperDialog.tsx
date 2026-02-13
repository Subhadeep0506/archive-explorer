import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { PaperCard } from "@/components/PaperCard";
import { searchArxivPapers } from "@/lib/arxiv";
import { normalizeArxivEntry } from "@/lib/papers";
import { useAuth } from "@/context/AuthContext";
import { useSearch } from "@/context/SearchContext";
import { useQuery } from "@tanstack/react-query";
import { getSavedPapers } from "@/lib/api";
import { Paper } from "@/types/paper";


export function AddPaperDialog() {
  const { accessToken } = useAuth();
  const {
    searchQuery,
    setSearchQuery,
    searchResults,
    setSearchResults,
    currentStart,
    setCurrentStart,
    hasMore,
    setHasMore,
    isSearching,
    setIsSearching,
    isLoadingMore,
    setIsLoadingMore,
    isDialogOpen,
    setIsDialogOpen,
  } = useSearch();

  const { data: savedPapers } = useQuery({
    queryKey: ["savedPapers"],
    queryFn: () => getSavedPapers(accessToken),
    enabled: Boolean(accessToken),
  });

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setCurrentStart(0);
    try {
      const results = await searchArxivPapers(searchQuery, 0, 20, accessToken);
      const normalized = results.map(normalizeArxivEntry);
      setSearchResults(normalized);
      setHasMore(results.length === 20); // If we got 20 results, there might be more
    } catch (error) {
      console.error("Search failed:", error);
      setSearchResults([]);
      setHasMore(false);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const handleLoadMore = async () => {
    if (!searchQuery.trim() || isLoadingMore) return;

    setIsLoadingMore(true);
    const nextStart = currentStart + 20;
    try {
      const results = await searchArxivPapers(
        searchQuery,
        nextStart,
        20,
        accessToken,
      );
      const normalized = results.map(normalizeArxivEntry);
      setSearchResults((prev: Paper[]) => [...prev, ...normalized]);
      setCurrentStart(nextStart);
      setHasMore(results.length === 20); // If we got 20 results, there might be more
    } catch (error) {
      console.error("Load more failed:", error);
      setHasMore(false);
    } finally {
      setIsLoadingMore(false);
    }
  };

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>Add Paper</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search for papers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="pl-10"
              />
            </div>
            <Button
              onClick={handleSearch}
              disabled={isSearching || !searchQuery.trim()}
            >
              {isSearching ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Search"
              )}
            </Button>
          </div>
          <div className="overflow-y-auto max-h-96">
            {isSearching ? (
              <div className="flex h-32 items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin" />
              </div>
            ) : searchResults.length > 0 ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {searchResults.map((paper, index) => (
                    <PaperCard
                      key={paper.id}
                      paper={paper}
                      index={index}
                      savedPapers={savedPapers}
                      fromSearch={true}
                    />
                  ))}
                </div>
                {hasMore && (
                  <div className="flex justify-center pt-4">
                    <Button
                      onClick={handleLoadMore}
                      disabled={isLoadingMore}
                      variant="outline"
                    >
                      {isLoadingMore ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin mr-2" />
                          Loading...
                        </>
                      ) : (
                        "Load More"
                      )}
                    </Button>
                  </div>
                )}
              </>
            ) : searchQuery && !isSearching ? (
              <div className="text-center text-muted-foreground py-8">
                No papers found for "{searchQuery}"
              </div>
            ) : null}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
