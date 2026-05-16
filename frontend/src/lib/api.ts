const DEFAULT_BASE_URL = "http://localhost:8000/api/v1";

export const API_BASE_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "")
    || DEFAULT_BASE_URL;

export const ACCESS_TOKEN_KEY = "arxiver.access_token";
export const REFRESH_TOKEN_KEY = "arxiver.refresh_token";
export const USER_KEY = "arxiver.user";
const SETTINGS_KEY = "user_settings";

type ApiPrimitive = string | number | boolean | undefined | null;
type ApiParam = ApiPrimitive | ApiPrimitive[];

export interface ApiRequestOptions {
    method?: string;
    body?: unknown;
    headers?: HeadersInit;
    params?: Record<string, ApiParam>;
    token?: string | null;
    auth?: boolean;
    includeApiKeys?: boolean; // New option to include user API keys in request
}

const buildUrl = (path: string, params?: Record<string, ApiParam>) => {
    const base = API_BASE_URL;
    const needsSlash = path.startsWith("/");
    const url = path.startsWith("http")
        ? new URL(path)
        : new URL(`${base}${needsSlash ? "" : "/"}${path}`);

    if (params) {
        Object.entries(params).forEach(([key, value]) => {
            if (value === undefined || value === null) return;
            if (Array.isArray(value)) {
                value.forEach((v) => {
                    if (v === undefined || v === null) return;
                    url.searchParams.append(key, String(v));
                });
            } else {
                url.searchParams.append(key, String(value));
            }
        });
    }

    return url;
};

/**
 * Get user's encrypted API keys from localStorage
 */
const getUserApiKeys = (): import("@/types/settings").ApiKeyItem[] | null => {
    try {
        if (typeof window === "undefined") return null;
        const settingsStr = window.localStorage.getItem(SETTINGS_KEY);
        if (!settingsStr) return null;
        const settings = JSON.parse(settingsStr) as import("@/types/settings").UserSettings;
        return settings.api_keys_encrypted || null;
    } catch (error) {
        console.error("Failed to get user API keys:", error);
        return null;
    }
};

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
    if (isRefreshing && refreshPromise) {
        return refreshPromise;
    }

    isRefreshing = true;
    refreshPromise = (async () => {
        try {
            const refreshToken = typeof window !== "undefined"
                ? window.localStorage.getItem(REFRESH_TOKEN_KEY)
                : null;

            if (!refreshToken) {
                return null;
            }

            const url = buildUrl("/auth/refresh");
            const response = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (!response.ok) {
                return null;
            }

            const data = await response.json() as { access_token: string };
            const newAccessToken = data.access_token;

            // Update stored access token
            if (typeof window !== "undefined") {
                window.localStorage.setItem(ACCESS_TOKEN_KEY, newAccessToken);
            }

            return newAccessToken;
        } catch (error) {
            return null;
        } finally {
            isRefreshing = false;
            refreshPromise = null;
        }
    })();

    return refreshPromise;
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
    const { method = "GET", body, headers, params, token, auth = true, includeApiKeys = false } = options;
    const url = buildUrl(path, params);
    const finalHeaders = new Headers(headers ?? {});
    let payload: BodyInit | undefined;

    // Prepare the request body
    let requestBody = body;

    // If includeApiKeys is true, merge api_keys_encrypted into the body
    if (includeApiKeys && requestBody && typeof requestBody === 'object' && !(requestBody instanceof FormData)) {
        const apiKeys = getUserApiKeys();
        if (apiKeys && apiKeys.length > 0) {
            requestBody = {
                ...requestBody,
                api_keys_encrypted: apiKeys,
            };
        }
    }

    if (requestBody instanceof FormData) {
        payload = requestBody;
    } else if (requestBody !== undefined && requestBody !== null) {
        finalHeaders.set("Content-Type", "application/json");
        payload = JSON.stringify(requestBody);
    }

    const resolvedToken = auth
        ? token
        ?? (typeof window !== "undefined"
            ? window.localStorage.getItem(ACCESS_TOKEN_KEY)
            : null)
        : null;

    if (resolvedToken) {
        finalHeaders.set("Authorization", `Bearer ${resolvedToken}`);
    }

    let response = await fetch(url, {
        method,
        headers: finalHeaders,
        body: payload,
    });

    // If 401 and we have a refresh token, try to refresh and retry
    if (response.status === 401 && auth && typeof window !== "undefined") {
        const refreshToken = window.localStorage.getItem(REFRESH_TOKEN_KEY);
        if (refreshToken && !path.includes("/auth/")) {
            const newAccessToken = await refreshAccessToken();
            if (newAccessToken) {
                // Retry the request with the new token
                const retryHeaders = new Headers(headers ?? {});
                retryHeaders.set("Authorization", `Bearer ${newAccessToken}`);

                response = await fetch(url, {
                    method,
                    headers: retryHeaders,
                    body: payload,
                });
            }
        }
    }

    if (!response.ok) {
        let message = response.statusText || "Request failed";
        try {
            const errorData = await response.json();
            message = errorData?.detail || errorData?.message || message;
        } catch (error) {
            // Ignore JSON parse errors; fallback to status text
        }
        throw new Error(message);
    }

    if (response.status === 204) {
        return undefined as T;
    }

    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
        return (await response.json()) as T;
    }

    return (await response.text()) as T;
}

// Profile API functions
export async function getProfile(token?: string | null): Promise<import("@/types/profile").Profile | null> {
    try {
        return await apiRequest("/profile", { token });
    } catch (error) {
        if (error instanceof Error && 'status' in error && error.status === 404) {
            return null;
        }
        throw error;
    }
}

export async function createProfile(
    data: import("@/types/profile").ProfileCreate,
    token?: string | null
): Promise<import("@/types/profile").Profile> {
    return apiRequest("/profile", { method: "POST", body: data, token });
}

export async function updateProfile(
    data: import("@/types/profile").ProfileUpdate,
    token?: string | null
): Promise<import("@/types/profile").Profile> {
    return apiRequest("/profile", { method: "PUT", body: data, token });
}

export async function uploadAvatar(
    file: File,
    token?: string | null
): Promise<import("@/types/profile").Profile> {
    const formData = new FormData();
    formData.append("file", file);
    return apiRequest("/profile/avatar", { method: "POST", body: formData, token });
}

// User Settings API functions
export async function getUserSettings(
    token?: string | null
): Promise<import("@/types/settings").UserSettings> {
    return apiRequest("/settings", { token });
}

export async function updateUserSettings(
    data: import("@/types/settings").UserSettingsUpdate,
    token?: string | null
): Promise<import("@/types/settings").UserSettings> {
    return apiRequest("/settings", { method: "PUT", body: data, token });
}

// Service Catalog API functions
export async function getServiceCatalog(
    token?: string | null
): Promise<import("@/types/settings").ServiceCatalog[]> {
    return apiRequest("/settings/services", { token });
}

// Resource Catalog API functions
export async function getResourceCatalog(
    token?: string | null
): Promise<import("@/types/settings").ResourceCatalog[]> {
    return apiRequest("/settings/resources", { token });
}

// Paper API functions
export async function savePaper(
    paper: import("@/types/paper").Paper,
    token?: string | null
): Promise<import("@/types/paper").SavedPaper> {
    const paperData = {
        title: paper.title,
        abstract: paper.abstract,
        authors: paper.authors.join(", "),
        arxiv_id: paper.id,
        pdf_url: paper.pdfUrl,
        paper_url: paper.htmlUrl,
        github_url: paper.githubUrl,
        topics: paper.topics.join(", "),
        published_date: paper.date,
        institution: paper.institution,
        date_published: paper.date,
        thumbnail_url: paper.thumbnailUrl,
    };
    return apiRequest("/papers", { method: "POST", body: paperData, token });
}

export async function getSavedPapers(
    token?: string | null
): Promise<import("@/types/paper").SavedPaper[]> {
    return apiRequest("/papers", { token });
}

export async function getSavedPaper(
    paperId: number,
    token?: string | null
): Promise<import("@/types/paper").SavedPaper> {
    return apiRequest(`/papers/${paperId}`, { token });
}

export async function deleteSavedPaper(
    paperId: number,
    token?: string | null
): Promise<void> {
    return apiRequest(`/papers/${paperId}`, { method: "DELETE", token });
}

export async function bulkDeleteSavedPapers(
    paperIds: number[],
    token?: string | null
): Promise<{ message: string }> {
    return apiRequest("/papers/bulk", { method: "DELETE", params: { paper_ids: paperIds }, token });
}

export async function uploadPaper(
    file: File,
    metadata: {
        title: string;
        abstract: string;
        authors: string;
        github_url?: string;
        topics?: string;
        published_date?: string;
        institution?: string;
        date_published?: string;
    },
    token?: string | null
): Promise<import("@/types/paper").SavedPaper> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", metadata.title);
    formData.append("abstract", metadata.abstract);
    formData.append("authors", metadata.authors);

    if (metadata.github_url) formData.append("github_url", metadata.github_url);
    if (metadata.topics) formData.append("topics", metadata.topics);
    if (metadata.published_date) formData.append("published_date", metadata.published_date);
    if (metadata.institution) formData.append("institution", metadata.institution);
    if (metadata.date_published) formData.append("date_published", metadata.date_published);

    const url = `${API_BASE_URL}/papers/upload`;
    const headers: Record<string, string> = {};

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
        method: "POST",
        headers,
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to upload paper");
    }

    return response.json();
}

// Ingestion API functions
interface IngestPaperOptions {
    paperUrl: string;
    arxivId: string;
    embeddingModel?: string;
    token?: string | null;
}

export async function ingestPaper({ paperUrl, arxivId, embeddingModel, token }: IngestPaperOptions): Promise<{ message: string }> {
    return apiRequest("/ingestion/ingest", {
        method: "POST",
        body: { paper_url: paperUrl, arxiv_id: arxivId, embedding_model: embeddingModel },
        token,
    });
}

export async function deleteIngestedPaper(
    paperIds: string | string[],
    token?: string | null
): Promise<{ message: string }> {
    const normalizedIds = Array.isArray(paperIds) ? paperIds : [paperIds];
    return apiRequest("/ingestion/delete", {
        method: "DELETE",
        body: { paper_ids: normalizedIds },
        token,
    });
}

// Summary and Usability API functions
export async function getSummaryAndUsability(
    arxivId: string,
    token?: string | null
): Promise<import("@/types/summary").SummaryResponse> {
    return apiRequest(`/summary/${arxivId}`, { token });
}

export async function generateSummary(
    arxivId: string,
    token?: string | null
): Promise<import("@/types/summary").GenerateSummaryResponse> {
    return apiRequest(`/summary/${arxivId}`, {
        method: "POST",
        token,
        includeApiKeys: true
    });
}

export async function generateSummaryFlexible(
    request: import("@/types/summary").GenerateSummaryRequest,
    token?: string | null
): Promise<import("@/types/summary").GenerateSummaryResponse> {
    return apiRequest("/summary/generate", {
        method: "POST",
        body: request,
        token,
        includeApiKeys: true
    });
}

export async function generateUsability(
    arxivId: string,
    token?: string | null
): Promise<import("@/types/summary").GenerateUsabilityResponse> {
    return apiRequest(`/summary/${arxivId}/usability`, {
        method: "POST",
        token,
        includeApiKeys: true
    });
}

export async function generateUsabilityFlexible(
    request: import("@/types/summary").GenerateUsabilityRequest,
    token?: string | null
): Promise<import("@/types/summary").GenerateUsabilityResponse> {
    return apiRequest("/summary/usability/generate", {
        method: "POST",
        body: request,
        token,
        includeApiKeys: true
    });
}

// Recommendation API functions
export async function getRecommendations(
    paper: { title: string; abstract: string; authors: string[]; id?: string; primaryCategory?: string },
    token?: string | null,
    limit: number = 10,
): Promise<import("@/types/paper").RecommendationsResponse> {
    return apiRequest("/arxiv/recommendations", {
        method: "POST",
        body: {
            title: paper.title,
            abstract: paper.abstract,
            authors: paper.authors.join("; "),
            primary_category: paper.primaryCategory || null,
            arxiv_id: paper.id || null,
        },
        params: { limit },
        token,
    });
}

// Session API functions
export async function getSessions(
    token?: string | null
): Promise<import("@/types/chat").Session[]> {
    return apiRequest("/sessions", { token });
}

export async function getSession(
    sessionId: number,
    token?: string | null
): Promise<import("@/types/chat").Session> {
    return apiRequest(`/sessions/${sessionId}`, { token });
}

export async function createSession(
    data: import("@/types/chat").SessionCreate,
    token?: string | null
): Promise<import("@/types/chat").Session> {
    return apiRequest("/sessions", { method: "POST", body: data, token });
}

export async function updateSession(
    sessionId: number,
    data: import("@/types/chat").SessionUpdate,
    token?: string | null
): Promise<import("@/types/chat").Session> {
    return apiRequest(`/sessions/${sessionId}`, { method: "PUT", body: data, token });
}

export async function deleteSession(
    sessionId: number,
    token?: string | null
): Promise<void> {
    return apiRequest(`/sessions/${sessionId}`, { method: "DELETE", token });
}

// Message API functions
export async function getMessagesBySession(
    sessionId: number,
    token?: string | null
): Promise<import("@/types/chat").Message[]> {
    return apiRequest(`/messages/session/${sessionId}`, { token });
}

export async function getMessage(
    messageId: number,
    token?: string | null
): Promise<import("@/types/chat").Message> {
    return apiRequest(`/messages/${messageId}`, { token });
}

export async function updateMessage(
    messageId: number,
    data: import("@/types/chat").MessageUpdate,
    token?: string | null
): Promise<import("@/types/chat").Message> {
    return apiRequest(`/messages/${messageId}`, { method: "PUT", body: data, token });
}

export async function deleteMessage(
    messageId: number,
    token?: string | null
): Promise<void> {
    return apiRequest(`/messages/${messageId}`, { method: "DELETE", token });
}

// Chat query API function (returns SSE stream)
export async function queryChatStream(
    data: import("@/types/chat").ChatQueryRequest,
    token?: string | null
): Promise<Response> {
    const url = buildUrl("/chat/query");
    const finalHeaders = new Headers();
    finalHeaders.set("Content-Type", "application/json");

    const resolvedToken = token ?? (typeof window !== "undefined" ? window.localStorage.getItem(ACCESS_TOKEN_KEY) : null);
    if (resolvedToken) {
        finalHeaders.set("Authorization", `Bearer ${resolvedToken}`);
    }

    // Include user's API keys in the request
    const apiKeys = getUserApiKeys();
    const requestData = {
        ...data,
        ...(apiKeys && apiKeys.length > 0 && { api_keys_encrypted: apiKeys })
    };

    const response = await fetch(url, {
        method: "POST",
        headers: finalHeaders,
        body: JSON.stringify(requestData),
    });

    if (!response.ok) {
        let message = response.statusText || "Request failed";
        try {
            const errorData = await response.json();
            message = errorData?.detail || errorData?.message || message;
        } catch (error) {
            // Ignore JSON parse errors
        }
        throw new Error(message);
    }

    return response;
}
