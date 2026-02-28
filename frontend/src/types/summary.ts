export interface UsabilityMetrics {
    domain_applicability: Record<string, number>;
    reproducibility_score: number;
    new_tech_applicability: Record<string, number>;
    impact_score?: number;
}

export interface SummaryResponse {
    arxiv_id: string;
    summary: string | null;
    usability: UsabilityMetrics | null;
}

export interface GenerateSummaryResponse {
    arxiv_id: string;
    summary: string;
}

export interface GenerateUsabilityResponse {
    arxiv_id: string;
    domain_applicability: Record<string, number>;
    reproducibility_score: number;
    new_tech_applicability: Record<string, number>;
    impact_score?: number;
}
