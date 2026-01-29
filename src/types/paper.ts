export interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  date: string;
  topics: string[];
  institution: string;
  country: string;
  pdfUrl: string;
  htmlUrl?: string;
  githubUrl?: string;
  thumbnailUrl?: string;
}

export interface FilterOption {
  id: string;
  label: string;
  count: number;
  color: 'coral' | 'teal' | 'amber' | 'violet' | 'emerald' | 'blue' | 'rose';
}

export interface Filters {
  topics: string[];
  countries: string[];
  institutions: string[];
  years: string[];
}

export type ViewMode = 'grid' | 'detailed';
