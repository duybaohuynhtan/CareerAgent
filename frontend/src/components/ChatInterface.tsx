'use client';

import { useState, useEffect, useRef } from 'react';
import { Trash2, MessageSquare } from 'lucide-react';
import { ChatMessage, ModelOption } from '@/types/chat';
import { apiClient } from '@/lib/api';
import { generateId } from '@/lib/utils';
import ModelSelector from './ModelSelector';
import ChatMessageComponent from './ChatMessage';
import ChatInput from './ChatInput';

export default function ChatInterface() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [selectedModel, setSelectedModel] = useState('deepseek-r1-distill-llama-70b');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Welcome message
    useEffect(() => {
        if (messages.length === 0) {
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
    }, []);

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
                model: selectedModel,
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

    const clearChat = () => {
        setMessages([]);
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
                        onModelChange={setSelectedModel}
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

            {/* Input */}
            <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
        </div>
    );
}