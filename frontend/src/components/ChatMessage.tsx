'use client';

import { Bot, User, Clock } from 'lucide-react';
import { cn, formatTimestamp } from '@/lib/utils';
import { ChatMessage as ChatMessageType } from '@/types/chat';

interface ChatMessageProps {
    message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
    const isUser = message.role === 'user';

    return (
        <div className={cn(
            "flex gap-3 p-4",
            !isUser && "bg-gray-50/50"
        )}>
            <div className={cn(
                "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                isUser
                    ? "bg-blue-600 text-white"
                    : "bg-gray-600 text-white"
            )}>
                {isUser ? (
                    <User className="w-4 h-4" />
                ) : (
                    <Bot className="w-4 h-4" />
                )}
            </div>

            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm text-gray-900">
                        {isUser ? 'You' : 'AI Assistant'}
                    </span>
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTimestamp(message.timestamp)}
                    </span>
                </div>

                <div className={cn(
                    "prose prose-sm max-w-none",
                    "text-gray-800 leading-relaxed"
                )}>
                    {message.isLoading ? (
                        <div className="flex items-center gap-2">
                            <div className="flex space-x-1">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                            </div>
                            <span className="text-gray-500 text-sm">Processing...</span>
                        </div>
                    ) : (
                        <div className="whitespace-pre-wrap">{message.content}</div>
                    )}
                </div>
            </div>
        </div>
    );
}