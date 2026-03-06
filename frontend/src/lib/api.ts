const DEFAULT_BASE_URL = "http://localhost:8000/api/v1";

export const API_BASE_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "")
    || DEFAULT_BASE_URL;

export const ACCESS_TOKEN_KEY = "arxiver.access_token";
export const REFRESH_TOKEN_KEY = "arxiver.refresh_token";
export const USER_KEY = "arxiver.user";

type ApiPrimitive = string | number | boolean | undefined | null;
type ApiParam = ApiPrimitive | ApiPrimitive[];

export interface ApiRequestOptions {
    method?: string;
    body?: unknown;
    headers?: HeadersInit;
    params?: Record<string, ApiParam>;
    token?: string | null;
    auth?: boolean;
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

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
    const { method = "GET", body, headers, params, token, auth = true } = options;
    const url = buildUrl(path, params);
    const finalHeaders = new Headers(headers ?? {});
    let payload: BodyInit | undefined;

    if (body instanceof FormData) {
        payload = body;
    } else if (body !== undefined && body !== null) {
        finalHeaders.set("Content-Type", "application/json");
        payload = JSON.stringify(body);
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

    const response = await fetch(url, {
        method,
        headers: finalHeaders,
        body: payload,
    });

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
    return apiRequest(`/summary/${arxivId}`, { method: "POST", token });
}

export async function generateSummaryFlexible(
    request: import("@/types/summary").GenerateSummaryRequest,
    token?: string | null
): Promise<import("@/types/summary").GenerateSummaryResponse> {
    return apiRequest("/summary/generate", {
        method: "POST",
        body: request,
        token
    });
}

export async function generateUsability(
    arxivId: string,
    token?: string | null
): Promise<import("@/types/summary").GenerateUsabilityResponse> {
    return apiRequest(`/summary/${arxivId}/usability`, { method: "POST", token });
}

export async function generateUsabilityFlexible(
    request: import("@/types/summary").GenerateUsabilityRequest,
    token?: string | null
): Promise<import("@/types/summary").GenerateUsabilityResponse> {
    return apiRequest("/summary/usability/generate", {
        method: "POST",
        body: request,
        token
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

    const response = await fetch(url, {
        method: "POST",
        headers: finalHeaders,
        body: JSON.stringify(data),
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
