export interface ApiKeyItem {
    id: number;
    slug: string;
    name: string;
    api_key: string;
}

export interface UserSettings {
    id: number;
    user_id: number;
    location?: string;
    custom_summary_instructions?: string;
    usability_analysis_instructions?: string;
    api_keys_encrypted?: ApiKeyItem[];
}

export interface UserSettingsUpdate {
    location?: string;
    custom_summary_instructions?: string;
    usability_analysis_instructions?: string;
    api_keys_encrypted?: ApiKeyItem[];
}

export interface ServiceCatalog {
    id: number;
    name: string;
    slug: string;
    service_type: string;
    description?: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface ResourceCatalog {
    id: number;
    name: string;
    slug: string;
    service_id: number;
    service_slug?: string;
    service_name?: string;
    description?: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}
