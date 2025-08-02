'use client';

import { Bot, User, Clock } from 'lucide-react';
import { cn, formatTimestamp } from '@/lib/utils';
import { ChatMessage as ChatMessageType } from '@/types/chat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';

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
                    "text-gray-800 leading-relaxed",
                    // Enhanced styling for markdown
                    "prose-headings:text-gray-900 prose-headings:font-semibold",
                    "prose-p:text-gray-800 prose-p:leading-relaxed",
                    "prose-li:text-gray-800 prose-li:my-1",
                    "prose-strong:text-gray-900 prose-strong:font-semibold",
                    "prose-code:text-blue-600 prose-code:bg-blue-50 prose-code:px-1 prose-code:rounded",
                    "prose-pre:bg-gray-900 prose-pre:text-gray-100",
                    "prose-blockquote:border-blue-500 prose-blockquote:bg-blue-50 prose-blockquote:text-blue-900",
                    "prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline"
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
                    ) : isUser ? (
                        // User messages - simple text display
                        <div className="whitespace-pre-wrap">{message.content}</div>
                    ) : (
                        // Assistant messages - render as markdown
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeHighlight]}
                            components={{
                                // Custom component styling
                                h1: ({ children }) => <h1 className="text-xl font-bold mb-4 text-gray-900">{children}</h1>,
                                h2: ({ children }) => <h2 className="text-lg font-semibold mb-3 text-gray-900">{children}</h2>,
                                h3: ({ children }) => <h3 className="text-base font-semibold mb-2 text-gray-900">{children}</h3>,
                                ul: ({ children }) => <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>,
                                ol: ({ children }) => <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>,
                                li: ({ children }) => <li className="text-gray-800">{children}</li>,
                                p: ({ children }) => <p className="mb-3 leading-relaxed text-gray-800">{children}</p>,
                                code: ({ children, className }) => {
                                    const isInline = !className;
                                    return isInline ? (
                                        <code className="bg-blue-50 text-blue-600 px-1 py-0.5 rounded text-sm">{children}</code>
                                    ) : (
                                        <code className={className}>{children}</code>
                                    );
                                },
                                pre: ({ children }) => (
                                    <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto mb-4">
                                        {children}
                                    </pre>
                                ),
                                blockquote: ({ children }) => (
                                    <blockquote className="border-l-4 border-blue-500 bg-blue-50 pl-4 py-2 mb-4 text-blue-900">
                                        {children}
                                    </blockquote>
                                ),
                                strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                                em: ({ children }) => <em className="italic text-gray-700">{children}</em>,
                                a: ({ children, href }) => (
                                    <a
                                        href={href}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:text-blue-800 hover:underline"
                                    >
                                        {children}
                                    </a>
                                ),
                            }}
                        >
                            {message.content}
                        </ReactMarkdown>
                    )}
                </div>
            </div>
        </div>
    );
}