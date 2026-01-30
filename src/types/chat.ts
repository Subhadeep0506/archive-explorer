export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
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
