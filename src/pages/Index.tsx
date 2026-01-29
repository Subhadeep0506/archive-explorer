import { useState } from 'react';
import { Navbar } from '@/components/Navbar';
import { FilterSidebar } from '@/components/FilterSidebar';
import { ViewToggle } from '@/components/ViewToggle';
import { PaperCard } from '@/components/PaperCard';
import { PapersTable } from '@/components/PapersTable';
import { Pagination } from '@/components/Pagination';
import { Filters, ViewMode } from '@/types/paper';
import {
  mockPapers,
  topicFilters,
  countryFilters,
  institutionFilters,
  yearFilters,
} from '@/data/mockPapers';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';

const ITEMS_PER_PAGE = 6;

export default function Index() {
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Filters>({
    topics: [],
    countries: [],
    institutions: [],
    years: [],
  });

  // Filter papers based on search and filters
  const filteredPapers = mockPapers.filter((paper) => {
    const matchesSearch =
      searchQuery === '' ||
      paper.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      paper.abstract.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesTopics =
      filters.topics.length === 0 ||
      paper.topics.some((topic) =>
        filters.topics.some((filterId) =>
          topicFilters.find((f) => f.id === filterId)?.label === topic
        )
      );

    const matchesCountry =
      filters.countries.length === 0 ||
      filters.countries.some((filterId) =>
        countryFilters.find((f) => f.id === filterId)?.label === paper.country
      );

    const matchesInstitution =
      filters.institutions.length === 0 ||
      filters.institutions.some((filterId) =>
        institutionFilters.find((f) => f.id === filterId)?.label === paper.institution
      );

    const matchesYear =
      filters.years.length === 0 ||
      filters.years.some((filterId) =>
        paper.date.startsWith(filterId)
      );

    return matchesSearch && matchesTopics && matchesCountry && matchesInstitution && matchesYear;
  });

  const totalPages = Math.ceil(filteredPapers.length / ITEMS_PER_PAGE);
  const paginatedPapers = filteredPapers.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const handleFiltersChange = (newFilters: Filters) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="flex">
        <FilterSidebar
          topicFilters={topicFilters}
          countryFilters={countryFilters}
          institutionFilters={institutionFilters}
          yearFilters={yearFilters}
          filters={filters}
          onFiltersChange={handleFiltersChange}
        />

        <main className="flex-1 p-6">
          <div className="mb-6">
            <div className="flex items-center justify-between gap-4 mb-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search papers..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="pl-10"
                />
              </div>
              <ViewToggle mode={viewMode} onModeChange={setViewMode} />
            </div>

            <p className="text-sm text-muted-foreground">
              Showing {filteredPapers.length} papers
              {(filters.topics.length > 0 ||
                filters.countries.length > 0 ||
                filters.institutions.length > 0 ||
                filters.years.length > 0) && ' (filtered)'}
            </p>
          </div>

          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {paginatedPapers.map((paper, index) => (
                <PaperCard key={paper.id} paper={paper} index={index} />
              ))}
            </div>
          ) : (
            <PapersTable papers={paginatedPapers} />
          )}

          {filteredPapers.length === 0 && (
            <div className="text-center py-12">
              <p className="text-lg text-muted-foreground">No papers found matching your criteria</p>
              <p className="text-sm text-muted-foreground mt-1">Try adjusting your filters or search query</p>
            </div>
          )}

          {totalPages > 1 && (
            <div className="mt-8">
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={setCurrentPage}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
