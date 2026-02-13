export interface AuthUser {
    id: number;
    username: string;
    email: string;
    full_name: string;
}

export interface LoginPayload {
    email: string;
    password: string;
}

export interface RegisterPayload {
    email: string;
    password: string;
    full_name: string;
    username: string;
}

export interface AuthResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
    user: AuthUser;
}
