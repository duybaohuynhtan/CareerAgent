export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    isLoading?: boolean;
}

export interface ModelOption {
    id: string;
    name: string;
    description: string;
}

export interface ChatRequest {
    message: string;
    model: string;
    chatHistory: ChatMessage[];
}

export interface ChatResponse {
    response: string;
    success: boolean;
    error?: string;
}