'use client';

import { useState, useEffect, useRef } from 'react';
import { Trash2, MessageSquare } from 'lucide-react';
import { ChatMessage, ModelOption, UploadResponse } from '@/types/chat';
import { apiClient } from '@/lib/api';
import { generateId } from '@/lib/utils';

import ModelSelector from './ModelSelector';
import ChatMessageComponent from './ChatMessage';
import ChatInput from './ChatInput';
import FileUpload from './FileUpload';

export default function ChatInterface() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [selectedModel, setSelectedModel] = useState('llama-3.3-70b-versatile');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Load current model from backend on component mount
    useEffect(() => {
        const loadCurrentModel = async () => {
            try {
                const modelInfo = await apiClient.getCurrentModel();
                if (modelInfo) {
                    setSelectedModel(modelInfo.current_model);
                }
            } catch (error) {
                console.error('Failed to load current model:', error);
            }
        };
        loadCurrentModel();
    }, []);

    // Welcome message - only show if no messages and not during model loading
    useEffect(() => {
        if (messages.length === 0 && selectedModel) {
            const welcomeMessage: ChatMessage = {
                id: generateId(),
                role: 'assistant',
                content: `Hello! I'm an AI Assistant specialized in CV analysis and job searching.

I can help you with:
🔍 LinkedIn job search
📄 CV/Resume analysis and evaluation
📋 PDF text extraction
🎯 Finding suitable jobs based on your CV

Please share your CV or let me know what type of job you're looking for!`,
                timestamp: new Date(),
            };
            setMessages([welcomeMessage]);
        }
    }, [messages.length, selectedModel]);

    const handleModelChange = async (modelId: string) => {
        try {
            // Don't change if it's the same model
            if (modelId === selectedModel) {
                return;
            }

            const response = await apiClient.updateModel({ model: modelId });
            if (response.success) {
                setSelectedModel(modelId);

                // Clear chat messages since we switched models
                setMessages([]);

                // Add a system message about the model change
                const modelChangeMessage: ChatMessage = {
                    id: generateId(),
                    role: 'assistant',
                    content: `✅ **Model changed to ${modelId}**\n\n${response.message}\n\nHello! I'm your AI Assistant running on the new model. How can I help you today?`,
                    timestamp: new Date(),
                };

                setMessages([modelChangeMessage]);

                console.log('Model updated successfully:', response.message);
            } else {
                console.error('Failed to update model:', response.message);

                // Show error message in chat
                const errorMessage: ChatMessage = {
                    id: generateId(),
                    role: 'assistant',
                    content: `❌ **Failed to change model**: ${response.message}`,
                    timestamp: new Date(),
                };

                setMessages(prev => [...prev, errorMessage]);
            }
        } catch (error) {
            console.error('Error updating model:', error);

            // Show error message in chat
            const errorMessage: ChatMessage = {
                id: generateId(),
                role: 'assistant',
                content: `❌ **Error changing model**: ${error instanceof Error ? error.message : 'Unknown error'}`,
                timestamp: new Date(),
            };

            setMessages(prev => [...prev, errorMessage]);
        }
    };

    const handleSendMessage = async (content: string) => {
        if (isLoading) return;

        const userMessage: ChatMessage = {
            id: generateId(),
            role: 'user',
            content,
            timestamp: new Date(),
        };

        const loadingMessage: ChatMessage = {
            id: generateId(),
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isLoading: true,
        };

        setMessages(prev => [...prev, userMessage, loadingMessage]);
        setIsLoading(true);

        try {
            const response = await apiClient.sendChatMessage({
                message: content,
                chatHistory: messages,
            });

            setMessages(prev => {
                const newMessages = [...prev];
                const lastMessageIndex = newMessages.length - 1;

                if (response.success) {
                    newMessages[lastMessageIndex] = {
                        ...newMessages[lastMessageIndex],
                        content: response.response,
                        isLoading: false,
                    };
                } else {
                    newMessages[lastMessageIndex] = {
                        ...newMessages[lastMessageIndex],
                        content: response.error || 'An error occurred. Please try again.',
                        isLoading: false,
                    };
                }

                return newMessages;
            });
        } catch (error) {
            setMessages(prev => {
                const newMessages = [...prev];
                const lastMessageIndex = newMessages.length - 1;
                newMessages[lastMessageIndex] = {
                    ...newMessages[lastMessageIndex],
                    content: 'Error occurred while connecting to server. Please try again.',
                    isLoading: false,
                };
                return newMessages;
            });
        } finally {
            setIsLoading(false);
        }
    };

    const clearChat = async () => {
        try {
            // Clear backend agent memory
            const response = await apiClient.clearChat();
            if (response.success) {
                console.log('Chat cleared successfully:', response.message);
            } else {
                console.error('Failed to clear chat on backend:', response.message);
                // Still continue to clear frontend even if backend fails
            }
        } catch (error) {
            console.error('Error clearing chat:', error);
            // Still continue to clear frontend even if backend fails
        }

        // Clear frontend messages
        setMessages([]);
    };

    const handleUploadSuccess = (response: UploadResponse) => {
        if (response.cv_analysis) {
            // Add upload success message
            const successMessage: ChatMessage = {
                id: generateId(),
                role: 'assistant',
                content: response.cv_analysis,
                timestamp: new Date(),
            };

            setMessages(prev => [...prev, successMessage]);
        }
    };

    const handleUploadError = (error: string) => {
        // Add error message to chat
        const errorMessage: ChatMessage = {
            id: generateId(),
            role: 'assistant',
            content: `❌ Upload failed: ${error}`,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, errorMessage]);
    };

    return (
        <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white shadow-lg">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b bg-white">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                        <MessageSquare className="w-4 h-4 text-white" />
                    </div>
                    <div>
                        <h1 className="text-lg font-semibold text-gray-900">Resume Analyzer</h1>
                        <p className="text-sm text-gray-600">AI Career Assistant</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <ModelSelector
                        selectedModel={selectedModel}
                        onModelChange={handleModelChange}
                    />
                    <button
                        onClick={clearChat}
                        className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Clear chat history"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto">
                {messages.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-gray-500">
                        <div className="text-center">
                            <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                            <p className="text-lg font-medium">No messages yet</p>
                            <p className="text-sm">Start the conversation!</p>
                        </div>
                    </div>
                ) : (
                    <div className="pb-4">
                        {messages.map((message) => (
                            <ChatMessageComponent key={message.id} message={message} />
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* File Upload */}
            <div className="px-4 py-2 border-t bg-gray-50">
                <FileUpload
                    onUploadSuccess={handleUploadSuccess}
                    onUploadError={handleUploadError}
                    disabled={isLoading}
                />
            </div>

            {/* Input */}
            <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
        </div>
    );
}