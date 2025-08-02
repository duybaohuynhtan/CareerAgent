'use client';

import { useState, useRef } from 'react';
import { Upload, File, X, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api';
import { UploadResponse } from '@/types/chat';

interface FileUploadProps {
    onUploadSuccess?: (response: UploadResponse) => void;
    onUploadError?: (error: string) => void;
    disabled?: boolean;
}

export default function FileUpload({ onUploadSuccess, onUploadError, disabled }: FileUploadProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadedFile, setUploadedFile] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = async (file: File) => {
        // Validate file type
        const allowedTypes = ['.pdf', '.doc', '.docx', '.txt'];
        const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

        if (!allowedTypes.includes(fileExtension)) {
            const error = 'Only PDF, DOC, DOCX, and TXT files are supported';
            onUploadError?.(error);
            return;
        }

        // Validate file size (max 10MB)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            const error = 'File size must be less than 10MB';
            onUploadError?.(error);
            return;
        }

        setIsUploading(true);
        setUploadedFile(file.name);

        try {
            const response = await apiClient.uploadCV(file);

            if (response.success) {
                onUploadSuccess?.(response);
            } else {
                onUploadError?.(response.message);
                setUploadedFile(null);
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Upload failed';
            onUploadError?.(errorMessage);
            setUploadedFile(null);
        } finally {
            setIsUploading(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        if (disabled || isUploading) return;

        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        if (!disabled && !isUploading) {
            setIsDragging(true);
        }
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            handleFileSelect(files[0]);
        }
        // Reset input
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const openFileDialog = () => {
        if (!disabled && !isUploading) {
            fileInputRef.current?.click();
        }
    };

    const clearUploadedFile = () => {
        setUploadedFile(null);
    };

    return (
        <div className="relative">
            <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                onChange={handleFileInputChange}
                className="hidden"
            />

            {uploadedFile ? (
                <div className="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg">
                    <File className="w-4 h-4 text-green-600" />
                    <span className="text-sm text-green-700 font-medium truncate max-w-[200px]">
                        {uploadedFile}
                    </span>
                    {!isUploading && (
                        <button
                            onClick={clearUploadedFile}
                            className="p-1 hover:bg-green-100 rounded transition-colors"
                            title="Remove file"
                        >
                            <X className="w-3 h-3 text-green-600" />
                        </button>
                    )}
                    {isUploading && <Loader2 className="w-4 h-4 animate-spin text-green-600" />}
                </div>
            ) : (
                <div
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onClick={openFileDialog}
                    className={cn(
                        "flex items-center gap-2 px-3 py-2 border-2 border-dashed rounded-lg cursor-pointer transition-colors",
                        "hover:bg-gray-50 hover:border-gray-400",
                        isDragging && "border-blue-400 bg-blue-50",
                        disabled && "opacity-50 cursor-not-allowed hover:bg-white hover:border-gray-300",
                        isUploading && "opacity-50 cursor-not-allowed"
                    )}
                >
                    {isUploading ? (
                        <>
                            <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                            <span className="text-sm text-gray-600">Uploading...</span>
                        </>
                    ) : (
                        <>
                            <Upload className="w-4 h-4 text-gray-500" />
                            <span className="text-sm text-gray-600">
                                {isDragging ? 'Drop your CV here' : 'Upload CV (PDF, DOC, TXT)'}
                            </span>
                        </>
                    )}
                </div>
            )}
        </div>
    );
}