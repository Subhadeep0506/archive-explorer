import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  ReactNode,
  Dispatch,
  SetStateAction,
} from "react";
import { Paper } from "@/types/paper";

interface SearchContextType {
  isDialogOpen: boolean;
  setIsDialogOpen: (open: boolean) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  searchResults: Paper[];
  setSearchResults: Dispatch<SetStateAction<Paper[]>>;
  currentStart: number;
  setCurrentStart: (start: number) => void;
  hasMore: boolean;
  setHasMore: (more: boolean) => void;
  isSearching: boolean;
  setIsSearching: (searching: boolean) => void;
  isLoadingMore: boolean;
  setIsLoadingMore: (loading: boolean) => void;
  resetSearch: () => void;
}

const SearchContext = createContext<SearchContextType | undefined>(undefined);

export function SearchProvider({ children }: { children: ReactNode }) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Paper[]>([]);
  const [currentStart, setCurrentStart] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const resetSearch = useCallback(() => {
    setSearchQuery("");
    setSearchResults([]);
    setCurrentStart(0);
    setHasMore(false);
    setIsSearching(false);
    setIsLoadingMore(false);
  }, []);

  const value = useMemo(
    () => ({
      isDialogOpen,
      setIsDialogOpen,
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
      resetSearch,
    }),
    [
      isDialogOpen,
      searchQuery,
      searchResults,
      currentStart,
      hasMore,
      isSearching,
      isLoadingMore,
      resetSearch,
    ]
  );

  return (
    <SearchContext.Provider value={value}>
      {children}
    </SearchContext.Provider>
  );
}

export function useSearch() {
  const context = useContext(SearchContext);
  if (context === undefined) {
    throw new Error("useSearch must be used within a SearchProvider");
  }
  return context;
}
