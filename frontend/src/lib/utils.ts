import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

export function formatTimestamp(date: Date): string {
    return new Intl.DateTimeFormat('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    }).format(date)
}

export function generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}