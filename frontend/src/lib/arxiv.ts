import { apiRequest } from "@/lib/api";
import { ArxivEntry } from "@/types/arxiv";

interface FeedParams {
    topics: string[];
    start?: number;
    max_results?: number;
    sort_by?: string;
    sort_order?: string;
    include_thumbnails?: boolean;
}

export const DEFAULT_TOPICS = ["cs.AI", "cs.CL", "cs.LG", "stat.ML"];

export async function fetchArxivFeed(
    { topics, start = 0, max_results = 24, sort_by, sort_order, include_thumbnails = true }: FeedParams,
    token?: string | null,
): Promise<ArxivEntry[]> {
    const topicList = topics.length > 0 ? topics : DEFAULT_TOPICS;
    return apiRequest<ArxivEntry[]>("/arxiv/feed", {
        params: {
            topics: topicList,
            start,
            max_results,
            sort_by,
            sort_order,
            include_thumbnails,
        },
        token,
    });
}

export async function fetchPaperById(
    arxivId: string,
    token?: string | null,
): Promise<ArxivEntry | null> {
    const tryQueries = [`id:${arxivId}`, `all:${arxivId}`];

    for (const search_query of tryQueries) {
        const results = await apiRequest<ArxivEntry[]>("/arxiv/search", {
            params: {
                search_query,
                max_results: 1,
            },
            token,
        });

        if (results.length > 0) {
            return results[0];
        }
    }

    return null;
}

export async function searchArxivPapers(
    searchQuery: string,
    start: number = 0,
    maxResults: number = 10,
    token?: string | null,
): Promise<ArxivEntry[]> {
    return apiRequest<ArxivEntry[]>("/arxiv/search", {
        params: {
            search_query: searchQuery,
            start,
            max_results: maxResults,
        },
        token,
    });
}
