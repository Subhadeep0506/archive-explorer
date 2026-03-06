export interface UsabilityMetrics {
    domain_applicability: Record<string, number>;
    reproducibility_score: Record<string, number>;
    new_tech_applicability: Record<string, number>;
    impact_score?: number;
}

export interface SummaryResponse {
    arxiv_id: string;
    summary: string | null;
    usability: UsabilityMetrics | null;
}

export interface GenerateSummaryRequest {
    arxiv_id?: string;
    pdf_url?: string;
}

export interface GenerateUsabilityRequest {
    arxiv_id?: string;
    pdf_url?: string;
}

export interface GenerateSummaryResponse {
    arxiv_id: string;
    summary: string;
}

export interface GenerateUsabilityResponse {
    arxiv_id?: string;
    pdf_url?: string;
    domain_applicability: Record<string, number>;
    reproducibility_score: Record<string, number>;
    new_tech_applicability: Record<string, number>;
    impact_score?: number;
}
