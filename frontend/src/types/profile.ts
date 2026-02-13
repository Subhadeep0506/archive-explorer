export interface Profile {
    id: number;
    user_id: number;
    phone?: string;
    bio?: string;
    avatar_url?: string;
    topic_preferences?: string;
}

export interface ProfileUpdate {
    phone?: string;
    bio?: string;
    avatar_url?: string;
    topic_preferences?: string;
}

export interface ProfileCreate {
    phone?: string;
    bio?: string;
    avatar_url?: string;
    topic_preferences?: string;
}