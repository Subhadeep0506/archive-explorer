import { useState } from "react";
import { format } from "date-fns";
import { Search, Loader2, Upload, FileText, CalendarIcon } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { PaperCard } from "@/components/PaperCard";
import { searchArxivPapers } from "@/lib/arxiv";
import { normalizeArxivEntry } from "@/lib/papers";
import { uploadPaper } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useSearch } from "@/context/SearchContext";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getSavedPapers } from "@/lib/api";
import { Paper } from "@/types/paper";
import { toast } from "sonner";

export function AddPaperDialog() {
  const { accessToken } = useAuth();
  const queryClient = useQueryClient();
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

  // Upload form state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [publishedDate, setPublishedDate] = useState<Date | undefined>(undefined);
  const [uploadForm, setUploadForm] = useState({
    title: "",
    abstract: "",
    authors: "",
    github_url: "",
    topics: "",
    published_date: "",
    institution: "",
    date_published: "",
  });
  const [isUploading, setIsUploading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const { data: savedPapers } = useQuery({
    queryKey: ["savedPapers"],
    queryFn: () => getSavedPapers(accessToken),
    enabled: Boolean(accessToken),
  });

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setHasSearched(true);
    setIsSearching(true);
    setCurrentStart(0);
    try {
      const results = await searchArxivPapers(searchQuery, 0, 20, accessToken);
      const normalized = results.map(normalizeArxivEntry);
      setSearchResults(normalized);
      setHasMore(results.length === 20);
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
      setHasMore(results.length === 20);
    } catch (error) {
      console.error("Load more failed:", error);
      setHasMore(false);
    } finally {
      setIsLoadingMore(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type !== "application/pdf") {
        toast.error("Please select a PDF file");
        return;
      }
      if (file.size > 50 * 1024 * 1024) {
        // 50MB limit
        toast.error("File size must be less than 50MB");
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleUploadFormChange = (field: string, value: string) => {
    setUploadForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile) {
      toast.error("Please select a PDF file");
      return;
    }

    if (
      !uploadForm.title.trim() ||
      !uploadForm.abstract.trim() ||
      !uploadForm.authors.trim()
    ) {
      toast.error("Title, abstract, and authors are required");
      return;
    }

    setIsUploading(true);
    try {
      await uploadPaper(selectedFile, uploadForm, accessToken);
      toast.success("Paper uploaded successfully!");

      // Reset form
      setSelectedFile(null);
      setPublishedDate(undefined);
      setUploadForm({
        title: "",
        abstract: "",
        authors: "",
        github_url: "",
        topics: "",
        published_date: "",
        institution: "",
        date_published: "",
      });

      // Refetch saved papers
      queryClient.invalidateQueries({ queryKey: ["savedPapers"] });

      // Close dialog
      setIsDialogOpen(false);
    } catch (error) {
      console.error("Upload failed:", error);
      toast.error((error as Error).message || "Failed to upload paper");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogContent
        className="max-w-4xl min-w-4xl max-h-[85vh] overflow-hidden flex flex-col top-[8%] translate-y-0"
        onInteractOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>Add Paper</DialogTitle>
        </DialogHeader>

        <Tabs
          defaultValue="search"
          className="flex-1 flex flex-col overflow-hidden"
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="search">
              <Search className="w-4 h-4 mr-2" />
              Search ArXiv
            </TabsTrigger>
            <TabsTrigger value="upload">
              <Upload className="w-4 h-4 mr-2" />
              Upload PDF
            </TabsTrigger>
          </TabsList>

          <TabsContent
            value="search"
            className="flex-1 overflow-hidden flex flex-col space-y-4 mt-4"
          >
            <div className="flex gap-2 m-2">
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

            <div className="overflow-y-auto flex-1">
              {isSearching ? (
                <div className="flex h-32 items-center justify-center">
                  <Loader2 className="w-6 h-6 animate-spin" />
                </div>
              ) : searchResults.length > 0 ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
              ) : hasSearched && !isSearching ? (
                <div className="text-center text-muted-foreground py-8">
                  No papers found for "{searchQuery}"
                </div>
              ) : !hasSearched && searchQuery ? (
                <div className="text-center text-muted-foreground py-8">
                  Press <kbd className="rounded border px-1.5 py-0.5 text-xs font-mono">Enter</kbd> or the Search button to search
                </div>
              ) : null}
            </div>
          </TabsContent>

          <TabsContent value="upload" className="flex-1 overflow-y-auto mt-4">
            <form onSubmit={handleUploadSubmit} className="space-y-4 m-2">
              <div className="space-y-2">
                <Label htmlFor="pdf-file">
                  PDF File <span className="text-red-500">*</span>
                </Label>
                <div className="flex items-center gap-2">
                  <Input
                    id="pdf-file"
                    type="file"
                    accept="application/pdf"
                    onChange={handleFileChange}
                    className="cursor-pointer"
                  />
                  {selectedFile && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <FileText className="w-4 h-4" />
                      <span className="truncate max-w-50">
                        {selectedFile.name}
                      </span>
                    </div>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  Upload a PDF file (max 50MB)
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="title">
                    Title <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="title"
                    placeholder="Enter paper title"
                    value={uploadForm.title}
                    onChange={(e) =>
                      handleUploadFormChange("title", e.target.value)
                    }
                    required
                  />
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="abstract">
                    Abstract <span className="text-red-500">*</span>
                  </Label>
                  <Textarea
                    id="abstract"
                    placeholder="Enter paper abstract"
                    value={uploadForm.abstract}
                    onChange={(e) =>
                      handleUploadFormChange("abstract", e.target.value)
                    }
                    rows={4}
                    required
                  />
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="authors">
                    Authors <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="authors"
                    placeholder="e.g., John Doe, Jane Smith"
                    value={uploadForm.authors}
                    onChange={(e) =>
                      handleUploadFormChange("authors", e.target.value)
                    }
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Separate multiple authors with commas
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="institution">Institution</Label>
                  <Input
                    id="institution"
                    placeholder="e.g., MIT, Stanford"
                    value={uploadForm.institution}
                    onChange={(e) =>
                      handleUploadFormChange("institution", e.target.value)
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label>Published Date</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-left font-normal"
                      >
                        <CalendarIcon className="mr-2 h-4 w-4 shrink-0 opacity-50" />
                        {publishedDate ? (
                          format(publishedDate, "PPP")
                        ) : (
                          <span className="text-muted-foreground">Pick a date</span>
                        )}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={publishedDate}
                        onSelect={(date) => {
                          setPublishedDate(date);
                          const formatted = date ? format(date, "yyyy-MM-dd") : "";
                          handleUploadFormChange("published_date", formatted);
                          handleUploadFormChange("date_published", formatted);
                        }}
                        captionLayout="dropdown"
                        defaultMonth={publishedDate ?? new Date()}
                        disabled={(date) => date > new Date()}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="topics">Topics</Label>
                  <Input
                    id="topics"
                    placeholder="e.g., Machine Learning, NLP, Computer Vision"
                    value={uploadForm.topics}
                    onChange={(e) =>
                      handleUploadFormChange("topics", e.target.value)
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    Separate multiple topics with commas
                  </p>
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="github_url">GitHub URL</Label>
                  <Input
                    id="github_url"
                    type="url"
                    placeholder="https://github.com/..."
                    value={uploadForm.github_url}
                    onChange={(e) =>
                      handleUploadFormChange("github_url", e.target.value)
                    }
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsDialogOpen(false)}
                  disabled={isUploading}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isUploading || !selectedFile}>
                  {isUploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Paper
                    </>
                  )}
                </Button>
              </div>
            </form>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
