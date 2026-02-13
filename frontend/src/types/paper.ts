export interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  date: string;
  topics: string[];
  institution?: string;
  country?: string;
  pdfUrl: string;
  htmlUrl?: string;
  githubUrl?: string;
  thumbnailUrl?: string;
  primaryCategory?: string;
  ingested?: boolean;
}

export interface SavedPaper {
  id: number;
  user_id: number;
  title: string;
  abstract: string;
  authors: string;
  arxiv_id: string;
  pdf_url: string;
  paper_url?: string;
  github_url?: string;
  topics?: string;
  published_date?: string;
  thumbnail_url?: string;
  institution?: string;
  date_published?: string;
  created_at: string;
  ingested: boolean;
}

export interface FilterOption {
  id: string;
  label: string;
  value?: string;
  count?: number;
  color: 'coral' | 'teal' | 'amber' | 'violet' | 'emerald' | 'blue' | 'rose';
}

export interface Filters {
  topics: string[];
  countries?: string[];
  institutions?: string[];
  years: string[];
}

export type ViewMode = 'grid' | 'detailed';
