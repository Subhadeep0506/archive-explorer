// Backend API types
export interface Source {
  id: number;
  message_id: number;
  source_text: string | null;
  source_type: string | null;
  source_url: string | null;
  metadata: {
    page_number?: number;
    page?: number;
    [key: string]: unknown;
  } | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  session_id: number;
  user_id: number | null;
  content: {
    role: string;
    content: string;
  } | Array<{
    role: string;
    content: string;
  }>;
  parent_message_id: number | null;
  model_used: string | null;
  confidence_score: number | null;
  liked: boolean | null;
  feedback: string | null;
  stars: number | null;
  generation_metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  sources?: Source[];
}

export interface Session {
  id: number;
  user_id: number;
  paper_id: number | null;
  title: string;
  started_at: string;
  ended_at: string | null;
  device_type: string | null;
}

export interface SessionCreate {
  title?: string;
  paper_id?: number | null;
  started_at: string;
  ended_at?: string | null;
  device_type?: string | null;
}

export interface SessionUpdate {
  title?: string;
  started_at?: string;
  ended_at?: string | null;
  device_type?: string | null;
}

export interface MessageUpdate {
  content?: Record<string, unknown>;
  liked?: boolean;
  feedback?: string;
  stars?: number;
}

export interface ChatQueryRequest {
  query: string;
  paper_id: string;
  session_id: number;
  model_name?: string;
  temperature?: number;
  max_tokens?: number;
  top_k?: number;
  use_web_search?: boolean;
  web_search_topic?: string;
}

// UI types (for backward compatibility with existing components)
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  liked?: boolean;
  feedback?: string;
  stars?: number;
  generation_metadata?: {
    completion_tokens?: number;
    prompt_tokens?: number;
    total_tokens?: number;
  } | null;
  sources?: Source[];
}

export interface ChatConversation {
  id: string;
  paperId: string;
  paperTitle: string;
  title: string;
  messages: ChatMessage[];
  lastUpdated: string;
  pdfUrl: string;
}

// Streaming types for progressive UI
export interface StreamingNodeUpdate {
  id: string;
  type: 'custom' | 'updates';
  nodeName: string;
  displayName: string;
  timestamp: number;
  startTime: number;
  endTime?: number;
  messages: string[];
  data?: unknown;
}

export interface StreamingState {
  nodes: StreamingNodeUpdate[];
  finalResponse: string;
  responseMetadata?: {
    completion_tokens?: number;
    prompt_tokens?: number;
    total_tokens?: number;
  };
}
