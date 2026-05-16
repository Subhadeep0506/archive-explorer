import { apiRequest } from "@/lib/api";
import { ArxivEntry } from "@/types/arxiv";

interface FeedParams {
    topics: string[];
    start?: number;
    limit?: number;
}

export const DEFAULT_TOPICS = ["cs.AI", "cs.CL", "cs.LG", "stat.ML"];

export async function fetchArxivFeed(
    { topics, start = 0, limit = 24 }: FeedParams,
    token?: string | null,
): Promise<ArxivEntry[]> {
    const topicList = topics.length > 0 ? topics : DEFAULT_TOPICS;
    return apiRequest<ArxivEntry[]>("/arxiv/catalog/feed", {
        params: {
            topics: topicList,
            start,
            limit,
        },
        token,
    });
}

export async function fetchSmartFeed(
    { topics, start = 0, limit = 24 }: FeedParams,
    token?: string | null,
): Promise<ArxivEntry[]> {
    const topicList = topics.length > 0 ? topics : DEFAULT_TOPICS;
    return apiRequest<ArxivEntry[]>("/arxiv/smart-feed", {
        params: {
            topics: topicList,
            start,
            limit,
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
