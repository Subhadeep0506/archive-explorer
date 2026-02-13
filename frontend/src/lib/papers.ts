import { ArxivEntry } from "@/types/arxiv";
import { Paper, SavedPaper } from "@/types/paper";

export const normalizeArxivEntry = (entry: ArxivEntry): Paper => {
    const fallbackId =
        entry.arxiv_id ||
        entry.id ||
        (typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2));

    return {
        id: fallbackId,
        title: entry.title || "Untitled paper",
        authors: entry.authors?.length ? entry.authors : ["Unknown author"],
        abstract: entry.abstract && entry.abstract.trim() ? entry.abstract.trim() : "No abstract available yet.",
        date: entry.published || entry.updated || new Date().toISOString(),
        topics: entry.categories || [],
        institution: entry.primary_category || "arXiv",
        country: "Global Research",
        pdfUrl: entry.pdf_url || entry.paper_url || "#",
        htmlUrl: entry.paper_url || undefined,
        githubUrl: undefined,
        thumbnailUrl: entry.thumbnail_url || undefined,
        primaryCategory: entry.primary_category || undefined,
    };
};

export const normalizeSavedPaper = (savedPaper: SavedPaper): Paper => {
    return {
        id: savedPaper.arxiv_id,
        title: savedPaper.title,
        authors: savedPaper.authors ? savedPaper.authors.split(",").map(a => a.trim()) : ["Unknown author"],
        abstract: savedPaper.abstract,
        date: savedPaper.published_date || savedPaper.date_published || new Date().toISOString(),
        topics: savedPaper.topics ? savedPaper.topics.split(",").map(t => t.trim()) : [],
        institution: savedPaper.institution,
        country: "Global Research",
        pdfUrl: savedPaper.pdf_url,
        htmlUrl: savedPaper.paper_url || undefined,
        githubUrl: savedPaper.github_url || undefined,
        thumbnailUrl: savedPaper.thumbnail_url || undefined,
        primaryCategory: savedPaper.institution || "arXiv",
        ingested: savedPaper.ingested,
    };
};
