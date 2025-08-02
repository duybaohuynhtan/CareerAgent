import { ChatRequest, ChatResponse, UpdateModelRequest, UpdateModelResponse, ModelOption, UploadResponse } from '@/types/chat';

const API_BASE_URL = process.env.NODE_ENV === 'production'
    ? 'https://your-backend-url.com'
    : 'http://localhost:8000';

export class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
        try {
            const response = await fetch(`${this.baseUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API Error:', error);
            return {
                response: 'Sorry, an error occurred while connecting to the server.',
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error',
            };
        }
    }

    async healthCheck(): Promise<boolean> {
        try {
            const response = await fetch(`${this.baseUrl}/api/health`);
            return response.ok;
        } catch {
            return false;
        }
    }

    async getCurrentModel(): Promise<{ current_model: string, available_models: string[] } | null> {
        try {
            const response = await fetch(`${this.baseUrl}/api/model`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Get model error:', error);
            return null;
        }
    }

    async updateModel(request: UpdateModelRequest): Promise<UpdateModelResponse> {
        try {
            const response = await fetch(`${this.baseUrl}/api/model`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Update model error:', error);
            return {
                success: false,
                message: error instanceof Error ? error.message : 'Unknown error',
                current_model: 'unknown'
            };
        }
    }

    async getAvailableModels(): Promise<ModelOption[]> {
        try {
            const response = await fetch(`${this.baseUrl}/api/models`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data.models || [];
        } catch (error) {
            console.error('Get models error:', error);
            // Return fallback models if API fails
            return [
                {
                    id: 'llama-3.3-70b-versatile',
                    name: 'Llama 3.3 70B Versatile',
                    description: 'Versatile model for general conversations'
                }
            ];
        }
    }

    async clearChat(): Promise<{ success: boolean, message: string }> {
        try {
            const response = await fetch(`${this.baseUrl}/api/chat/clear`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Clear chat error:', error);
            return {
                success: false,
                message: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }

    async uploadCV(file: File): Promise<UploadResponse> {
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${this.baseUrl}/api/upload/cv`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Upload CV error:', error);
            return {
                success: false,
                message: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }
}

export const apiClient = new ApiClient();