'use client';

import { useState } from 'react';
import { ChevronDown, Brain } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ModelOption } from '@/types/chat';

interface ModelSelectorProps {
    selectedModel: string;
    onModelChange: (modelId: string) => void;
}

const AVAILABLE_MODELS: ModelOption[] = [
    {
        id: 'deepseek-r1-distill-llama-70b',
        name: 'DeepSeek R1 Distill Llama 70B',
        description: 'Advanced reasoning model for complex tasks'
    },
    {
        id: 'llama-3.3-70b-versatile',
        name: 'Llama 3.3 70B Versatile',
        description: 'Versatile model for general conversations'
    },
    {
        id: 'gemma2-9b-it',
        name: 'Gemma2 9B IT',
        description: 'Efficient model for instruction following'
    }
];

export default function ModelSelector({ selectedModel, onModelChange }: ModelSelectorProps) {
    const [isOpen, setIsOpen] = useState(false);

    const selectedModelOption = AVAILABLE_MODELS.find(model => model.id === selectedModel) || AVAILABLE_MODELS[0];

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={cn(
                    "flex items-center gap-3 px-4 py-2 rounded-lg border",
                    "bg-white hover:bg-gray-50 transition-colors",
                    "text-sm font-medium text-gray-700",
                    "min-w-[250px] justify-between",
                    isOpen && "ring-2 ring-blue-500 ring-opacity-50"
                )}
            >
                <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4 text-blue-600" />
                    <div className="text-left">
                        <div className="font-medium">{selectedModelOption.name}</div>
                        <div className="text-xs text-gray-500 truncate max-w-[180px]">
                            {selectedModelOption.description}
                        </div>
                    </div>
                </div>
                <ChevronDown
                    className={cn(
                        "w-4 h-4 transition-transform",
                        isOpen && "transform rotate-180"
                    )}
                />
            </button>

            {isOpen && (
                <>
                    <div
                        className="fixed inset-0 z-10"
                        onClick={() => setIsOpen(false)}
                    />
                    <div className="absolute top-full left-0 mt-1 w-full bg-white border rounded-lg shadow-lg z-20 py-1">
                        {AVAILABLE_MODELS.map((model) => (
                            <button
                                key={model.id}
                                onClick={() => {
                                    onModelChange(model.id);
                                    setIsOpen(false);
                                }}
                                className={cn(
                                    "w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors",
                                    "border-b border-gray-100 last:border-b-0",
                                    selectedModel === model.id && "bg-blue-50 text-blue-700"
                                )}
                            >
                                <div className="font-medium text-sm">{model.name}</div>
                                <div className="text-xs text-gray-500 mt-1">{model.description}</div>
                            </button>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}