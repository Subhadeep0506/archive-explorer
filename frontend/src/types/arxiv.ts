export interface ArxivEntry {
    id?: string | null;
    arxiv_id?: string | null;
    title?: string | null;
    abstract?: string | null;
    authors: string[];
    pdf_url?: string | null;
    paper_url?: string | null;
    categories: string[];
    primary_category?: string | null;
    published?: string | null;
    updated?: string | null;
    comment?: string | null;
    journal_ref?: string | null;
    doi?: string | null;
    thumbnail_url?: string | null;
}
