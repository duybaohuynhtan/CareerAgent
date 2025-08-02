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
    chatHistory: ChatMessage[];
}

export interface ChatResponse {
    response: string;
    success: boolean;
    error?: string;
}

export interface UpdateModelRequest {
    model: string;
}

export interface UpdateModelResponse {
    success: boolean;
    message: string;
    current_model: string;
}

export interface UploadResponse {
    success: boolean;
    message: string;
    file_id?: string;
    cv_analysis?: string;
}