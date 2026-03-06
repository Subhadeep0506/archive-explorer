import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ArrowLeft,
  FileText,
  Globe,
  Github,
  Trash2,
  ExternalLink,
  Loader2,
  Sparkles,
  Search,
  Filter,
  X,
  MoreHorizontal,
} from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import {
  getSavedPapers,
  deleteSavedPaper,
  bulkDeleteSavedPapers,
  deleteIngestedPaper,
  ingestPaper,
} from "@/lib/api";
import { normalizeSavedPaper } from "@/lib/papers";
import type { SavedPaper } from "@/types/paper";

export default function SavedPapers() {
  const { accessToken } = useAuth();
  const queryClient = useQueryClient();
  const [paperToDelete, setPaperToDelete] = useState<SavedPaper | null>(null);
  const [selectedPapers, setSelectedPapers] = useState<Set<number>>(new Set());
  const [bulkDeleteMode, setBulkDeleteMode] = useState(false);
  const [ingestingPaperId, setIngestingPaperId] = useState<number | null>(null);
  const [deletingPaperId, setDeletingPaperId] = useState<number | null>(null);

  // Search and filter state
  const [searchText, setSearchText] = useState("");
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [selectedYears, setSelectedYears] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<
    "date_added" | "date_published" | "title"
  >("date_added");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const {
    data: savedPapers,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["saved-papers"],
    queryFn: () => getSavedPapers(accessToken),
    enabled: Boolean(accessToken),
  });

  // Filter and sort papers
  const filteredAndSortedPapers = useMemo(() => {
    if (!savedPapers) return [];

    const filtered = savedPapers.filter((paper) => {
      // Text search
      const searchLower = searchText.toLowerCase();
      const matchesSearch =
        paper.title.toLowerCase().includes(searchLower) ||
        paper.abstract.toLowerCase().includes(searchLower) ||
        paper.authors.toLowerCase().includes(searchLower);

      // Topic filter
      const matchesTopics =
        selectedTopics.length === 0 ||
        (paper.topics &&
          selectedTopics.some((topic) =>
            paper.topics!.toLowerCase().includes(topic.toLowerCase()),
          ));

      // Year filter
      const matchesYears =
        selectedYears.length === 0 ||
        selectedYears.some((year) => {
          const pubDate = paper.published_date || paper.date_published;
          return pubDate && pubDate.includes(year);
        });

      return matchesSearch && matchesTopics && matchesYears;
    });

    // Sort
    filtered.sort((a, b) => {
      let aValue: Date | string, bValue: Date | string;

      switch (sortBy) {
        case "date_added":
          aValue = new Date(a.created_at);
          bValue = new Date(b.created_at);
          break;
        case "date_published":
          aValue = new Date(
            a.published_date || a.date_published || "1970-01-01",
          );
          bValue = new Date(
            b.published_date || b.date_published || "1970-01-01",
          );
          break;
        case "title":
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        default:
          return 0;
      }

      if (sortOrder === "asc") {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    return filtered;
  }, [
    savedPapers,
    searchText,
    selectedTopics,
    selectedYears,
    sortBy,
    sortOrder,
  ]);

  // Get unique topics and years for filter options
  const availableTopics = useMemo(() => {
    if (!savedPapers) return [];
    const topics = new Set<string>();
    savedPapers.forEach((paper) => {
      if (paper.topics) {
        paper.topics.split(",").forEach((topic) => {
          topics.add(topic.trim());
        });
      }
    });
    return Array.from(topics).sort();
  }, [savedPapers]);

  const availableYears = useMemo(() => {
    if (!savedPapers) return [];
    const years = new Set<string>();
    savedPapers.forEach((paper) => {
      const date = paper.published_date || paper.date_published;
      if (date) {
        const year = new Date(date).getFullYear().toString();
        years.add(year);
      }
    });
    return Array.from(years).sort().reverse();
  }, [savedPapers]);

  const deleteMutation = useMutation({
    mutationFn: async (paperId: number) => {
      // First delete from vector store
      if (paperToDelete) {
        try {
          await deleteIngestedPaper(paperToDelete.arxiv_id, accessToken);
        } catch (error) {
          console.warn("Failed to delete from vector store:", error);
          // Continue with database deletion even if vector store deletion fails
        }
      }
      // Then delete from database
      return deleteSavedPaper(paperId, accessToken);
    },
    onMutate: (paperId) => {
      setDeletingPaperId(paperId);
    },
    onSuccess: () => {
      toast.success("Paper deleted successfully!");
      queryClient.invalidateQueries({ queryKey: ["saved-papers"] });
      setPaperToDelete(null);
      setDeletingPaperId(null);
    },
    onError: (error) => {
      toast.error(`Failed to delete paper: ${error.message}`);
      setDeletingPaperId(null);
    },
  });

  const bulkDeleteMutation = useMutation({
    mutationFn: async (paperIds: number[]) => {
      // Get the papers to delete from vector store
      const papersToDelete = filteredAndSortedPapers.filter((p) =>
        paperIds.includes(p.id),
      );

      // Delete from vector store first
      for (const paper of papersToDelete) {
        try {
          await deleteIngestedPaper(paper.arxiv_id, accessToken);
        } catch (error) {
          console.warn(
            `Failed to delete ${paper.arxiv_id} from vector store:`,
            error,
          );
          // Continue with other deletions even if one fails
        }
      }

      // Then delete from database
      return bulkDeleteSavedPapers(paperIds, accessToken);
    },
    onSuccess: () => {
      toast.success(`${selectedPapers.size} papers deleted successfully!`);
      queryClient.invalidateQueries({ queryKey: ["saved-papers"] });
      setSelectedPapers(new Set());
      setBulkDeleteMode(false);
    },
    onError: (error) => {
      toast.error(`Failed to delete papers: ${error.message}`);
    },
  });

  const ingestMutation = useMutation<
    unknown,
    unknown,
    SavedPaper,
    { toastId: string | number }
  >({
    mutationFn: (paper: SavedPaper) =>
      ingestPaper({
        paperUrl: paper.pdf_url,
        arxivId: paper.arxiv_id,
        token: accessToken,
      }),
    onMutate: (paper) => {
      setIngestingPaperId(paper.id);
      const toastId = toast.loading(`Ingesting "${paper.title}"`, {
        description: "Hang tight while we process this PDF.",
        duration: Infinity,
      });
      return { toastId };
    },
    onSuccess: (_, paper, context) => {
      toast.success(`"${paper.title}" ingested successfully.`, {
        id: context?.toastId,
      });
      queryClient.invalidateQueries({ queryKey: ["saved-papers"] });
    },
    onError: (error, paper, context) => {
      const message = error instanceof Error ? error.message : "Unknown error";
      toast.error(`Failed to ingest "${paper?.title ?? "paper"}": ${message}`, {
        id: context?.toastId,
      });
    },
    onSettled: () => {
      setIngestingPaperId(null);
    },
  });

  const handleDelete = (paper: SavedPaper) => {
    setPaperToDelete(paper);
  };

  const confirmDelete = () => {
    if (paperToDelete) {
      deleteMutation.mutate(paperToDelete.id);
    }
  };

  const handleSelectPaper = (paperId: number, checked: boolean) => {
    const newSelected = new Set(selectedPapers);
    if (checked) {
      newSelected.add(paperId);
    } else {
      newSelected.delete(paperId);
    }
    setSelectedPapers(newSelected);
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedPapers(new Set(filteredAndSortedPapers.map((p) => p.id)));
    } else {
      setSelectedPapers(new Set());
    }
  };

  const handleBulkDelete = () => {
    if (selectedPapers.size > 0) {
      bulkDeleteMutation.mutate(Array.from(selectedPapers));
    }
  };

  const toggleBulkDeleteMode = () => {
    setBulkDeleteMode(!bulkDeleteMode);
    setSelectedPapers(new Set());
  };

  const showTableLoading = isLoading && !savedPapers;

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto py-12 text-center">
          <h1 className="text-2xl font-bold mb-4">
            Error loading saved papers
          </h1>
          <p className="text-muted-foreground mb-6">
            {(error as Error)?.message || "Unable to load saved papers"}
          </p>
          <Link to="/app">
            <Button>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-6 px-4">
        <div className="flex items-center gap-4 mb-6">
          <Link to="/app">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
          <div className="flex-1">
            <h1 className="text-2xl font-bold">Saved Papers</h1>
          </div>
          {filteredAndSortedPapers.length > 0 && (
            <div className="flex items-center gap-2">
              {bulkDeleteMode ? (
                <>
                  <span className="text-sm text-muted-foreground">
                    {selectedPapers.size} selected
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={toggleBulkDeleteMode}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleBulkDelete}
                    disabled={
                      selectedPapers.size === 0 || bulkDeleteMutation.isPending
                    }
                  >
                    {bulkDeleteMutation.isPending ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4 mr-2" />
                    )}
                    Delete Selected ({selectedPapers.size})
                  </Button>
                </>
              ) : (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={toggleBulkDeleteMode}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Bulk Delete
                </Button>
              )}
            </div>
          )}
        </div>

        {/* Search and Filters */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Search */}
              <div className="space-y-2">
                <Label htmlFor="search">Search</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <Input
                    id="search"
                    placeholder="Search papers..."
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Topics Filter */}
              <div className="space-y-2">
                <Label>Topics</Label>
                <Select
                  value=""
                  onValueChange={(value) => {
                    if (value && !selectedTopics.includes(value)) {
                      setSelectedTopics([...selectedTopics, value]);
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select topics" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableTopics.map((topic) => (
                      <SelectItem key={topic} value={topic}>
                        {topic}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedTopics.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {selectedTopics.map((topic) => (
                      <Badge
                        key={topic}
                        variant="secondary"
                        className="text-xs"
                      >
                        {topic}
                        <X
                          className="w-3 h-3 ml-1 cursor-pointer"
                          onClick={() =>
                            setSelectedTopics(
                              selectedTopics.filter((t) => t !== topic),
                            )
                          }
                        />
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              {/* Years Filter */}
              <div className="space-y-2">
                <Label>Years</Label>
                <Select
                  value=""
                  onValueChange={(value) => {
                    if (value && !selectedYears.includes(value)) {
                      setSelectedYears([...selectedYears, value]);
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select years" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableYears.map((year) => (
                      <SelectItem key={year} value={year}>
                        {year}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedYears.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {selectedYears.map((year) => (
                      <Badge key={year} variant="secondary" className="text-xs">
                        {year}
                        <X
                          className="w-3 h-3 ml-1 cursor-pointer"
                          onClick={() =>
                            setSelectedYears(
                              selectedYears.filter((y) => y !== year),
                            )
                          }
                        />
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              {/* Sort */}
              <div className="space-y-2">
                <Label>Sort by</Label>
                <Select
                  value={`${sortBy}-${sortOrder}`}
                  onValueChange={(value) => {
                    const [field, order] = value.split("-") as [
                      typeof sortBy,
                      typeof sortOrder,
                    ];
                    setSortBy(field);
                    setSortOrder(order);
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="date_added-desc">
                      Date Added (Newest)
                    </SelectItem>
                    <SelectItem value="date_added-asc">
                      Date Added (Oldest)
                    </SelectItem>
                    <SelectItem value="date_published-desc">
                      Date Published (Newest)
                    </SelectItem>
                    <SelectItem value="date_published-asc">
                      Date Published (Oldest)
                    </SelectItem>
                    <SelectItem value="title-asc">Title (A-Z)</SelectItem>
                    <SelectItem value="title-desc">Title (Z-A)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Clear Filters */}
            {(searchText ||
              selectedTopics.length > 0 ||
              selectedYears.length > 0) && (
              <div className="mt-4 pt-4 border-t">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSearchText("");
                    setSelectedTopics([]);
                    setSelectedYears([]);
                  }}
                >
                  <X className="w-4 h-4 mr-2" />
                  Clear all filters
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {showTableLoading ? (
          <Card>
            <CardContent className="p-6">
              <div className="space-y-4">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            </CardContent>
          </Card>
        ) : !savedPapers || savedPapers.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <div className="text-muted-foreground">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-semibold mb-2">
                  No saved papers yet
                </h3>
                <p className="mb-4">
                  Start saving papers from the dashboard to build your
                  collection.
                </p>
                <Link to="/app">
                  <Button>Browse Papers</Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ) : filteredAndSortedPapers.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <div className="text-muted-foreground">
                <Filter className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-semibold mb-2">
                  No papers match your filters
                </h3>
                <p className="mb-4">
                  Try adjusting your search or filter criteria.
                </p>
                <Button
                  variant="outline"
                  onClick={() => {
                    setSearchText("");
                    setSelectedTopics([]);
                    setSelectedYears([]);
                  }}
                >
                  Clear filters
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="relative rounded-lg border bg-card overflow-hidden animate-fade-in">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  {bulkDeleteMode && (
                    <TableHead className="w-[5%]">
                      <Checkbox
                        checked={
                          selectedPapers.size ===
                            filteredAndSortedPapers.length &&
                          filteredAndSortedPapers.length > 0
                        }
                        onCheckedChange={(checked) =>
                          handleSelectAll(checked as boolean)
                        }
                      />
                    </TableHead>
                  )}
                  <TableHead className={bulkDeleteMode ? "w-[26%]" : "w-[30%]"}>
                    Title
                  </TableHead>
                  <TableHead className="w-[10%]">Added</TableHead>
                  <TableHead className="w-[10%]">Published</TableHead>
                  <TableHead className="w-[25%]">Summary</TableHead>
                  <TableHead className="w-[8%] text-center">Status</TableHead>
                  <TableHead className="w-[17%] text-center">Links</TableHead>
                  <TableHead className="w-[7%] text-center">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAndSortedPapers.map((paper) => {
                  const safeDate = paper.published_date
                    ? new Date(paper.published_date)
                    : null;
                  const shortDate = safeDate
                    ? safeDate.toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                      })
                    : "—";

                  return (
                    <TableRow
                      key={paper.id}
                      className="group hover:bg-muted/30 transition-colors"
                    >
                      {bulkDeleteMode && (
                        <TableCell>
                          <Checkbox
                            checked={selectedPapers.has(paper.id)}
                            onCheckedChange={(checked) =>
                              handleSelectPaper(paper.id, checked as boolean)
                            }
                          />
                        </TableCell>
                      )}
                      <TableCell>
                        <Link
                          to={`/paper/${paper.arxiv_id}`}
                          state={{ paper: normalizeSavedPaper(paper) }}
                          className="font-medium text-foreground hover:text-primary transition-colors line-clamp-2"
                        >
                          {paper.title}
                        </Link>
                        <p className="text-xs text-muted-foreground mt-1">
                          {paper.authors.split(",").slice(0, 2).join(", ")}
                          {paper.authors.split(",").length > 2 &&
                            ` +${paper.authors.split(",").length - 2}`}
                        </p>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(paper.created_at).toLocaleDateString(
                          "en-US",
                          {
                            month: "short",
                            day: "numeric",
                          },
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {shortDate}
                      </TableCell>
                      <TableCell>
                        <Link to={`/paper/${paper.arxiv_id}`}>
                          <Badge
                            variant="outline"
                            className="cursor-pointer bg-chip-violet-bg text-chip-violet border-chip-violet/30 hover:bg-chip-violet hover:text-white transition-colors"
                          >
                            <Sparkles className="w-3 h-3 mr-1" />
                            AI Summary
                          </Badge>
                        </Link>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge
                          variant="outline"
                          className={`whitespace-nowrap ${
                            paper.ingested
                              ? "bg-chip-emerald-bg text-chip-emerald border-chip-emerald/40"
                              : "bg-chip-rose-bg text-chip-rose border-chip-rose/40"
                          }`}
                        >
                          {paper.ingested ? "Ingested" : "Not Ingested"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-center gap-2">
                          <Badge
                            variant="outline"
                            className="cursor-pointer bg-chip-amber-bg text-chip-amber border-chip-amber/30 hover:bg-chip-amber hover:text-white transition-colors"
                          >
                            <FileText className="w-3 h-3 mr-1" />
                            Saved
                          </Badge>
                          {paper.pdf_url && (
                            <a
                              href={paper.pdf_url}
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
                          )}
                          {paper.paper_url && (
                            <a
                              href={paper.paper_url}
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
                          {paper.github_url && (
                            <a
                              href={paper.github_url}
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
                      <TableCell className="text-center">
                        {!bulkDeleteMode && (
                          <AlertDialog>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                  onClick={(e) => e.stopPropagation()}
                                  disabled={deletingPaperId === paper.id}
                                >
                                  {deletingPaperId === paper.id ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                  ) : (
                                    <MoreHorizontal className="w-4 h-4" />
                                  )}
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                {!paper.ingested && (
                                  <DropdownMenuItem
                                    onClick={(event) => {
                                      event.stopPropagation();
                                      ingestMutation.mutate(paper);
                                    }}
                                    disabled={
                                      ingestMutation.isPending &&
                                      ingestingPaperId === paper.id
                                    }
                                  >
                                    {ingestMutation.isPending &&
                                    ingestingPaperId === paper.id ? (
                                      <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                                    ) : (
                                      <Sparkles className="w-3 h-3 mr-2" />
                                    )}
                                    Ingest
                                  </DropdownMenuItem>
                                )}
                                <AlertDialogTrigger asChild>
                                  <DropdownMenuItem
                                    onClick={(event) => {
                                      event.stopPropagation();
                                      handleDelete(paper);
                                    }}
                                  >
                                    <Trash2 className="w-3 h-3 mr-2" />
                                    Delete
                                  </DropdownMenuItem>
                                </AlertDialogTrigger>
                              </DropdownMenuContent>
                            </DropdownMenu>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>
                                  Delete Saved Paper
                                </AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to delete "{paper.title}
                                  " from your saved papers? This action cannot
                                  be undone.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={confirmDelete}
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                  {deleteMutation.isPending ? (
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                  ) : (
                                    <Trash2 className="w-4 h-4 mr-2" />
                                  )}
                                  Delete
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            {bulkDeleteMutation.isPending && (
              <div className="absolute inset-0 bg-background/80 flex items-center justify-center z-10 rounded-lg">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="w-6 h-6 animate-spin" />
                  <span>Deleting papers...</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
