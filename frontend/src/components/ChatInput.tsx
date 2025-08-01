'use client';

import { useState, KeyboardEvent } from 'react';
import { Send, Paperclip } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    disabled?: boolean;
}

export default function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
    const [message, setMessage] = useState('');

    const handleSubmit = () => {
        if (!message.trim() || disabled) return;

        onSendMessage(message.trim());
        setMessage('');
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="border-t bg-white p-4">
            <div className="flex gap-2 items-end">
                <div className="flex-1 relative">
                    <textarea
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Enter your message... (Press Enter to send, Shift+Enter for new line)"
                        disabled={disabled}
                        className={cn(
                            "w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg",
                            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                            "resize-none min-h-[48px] max-h-[120px]",
                            "disabled:bg-gray-100 disabled:cursor-not-allowed",
                            "placeholder:text-gray-500"
                        )}
                        rows={1}
                        style={{
                            height: 'auto',
                            minHeight: '48px'
                        }}
                        onInput={(e) => {
                            const target = e.target as HTMLTextAreaElement;
                            target.style.height = 'auto';
                            target.style.height = Math.min(target.scrollHeight, 120) + 'px';
                        }}
                    />

                    <button
                        type="button"
                        className="absolute right-2 bottom-2 p-1 text-gray-400 hover:text-gray-600 transition-colors"
                        title="Attach file"
                    >
                        <Paperclip className="w-4 h-4" />
                    </button>
                </div>

                <button
                    onClick={handleSubmit}
                    disabled={!message.trim() || disabled}
                    className={cn(
                        "px-4 py-3 bg-blue-600 text-white rounded-lg",
                        "hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500",
                        "disabled:bg-gray-300 disabled:cursor-not-allowed",
                        "transition-colors flex items-center gap-2",
                        "min-w-[80px] justify-center"
                    )}
                >
                    <Send className="w-4 h-4" />
                    <span className="hidden sm:inline">Send</span>
                </button>
            </div>

            <div className="mt-2 text-xs text-gray-500 text-center">
                AI can make mistakes. Please verify important information.
            </div>
        </div>
    );
}