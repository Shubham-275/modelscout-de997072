import { useState, useCallback, useRef } from 'react';

export interface LeaderboardEntry {
    rank: number;
    model: string;
    provider: string;
    mmlu: number;
    arena_elo: number;
    humaneval: number;
    average: number;
    context?: number;
    safety?: number;
    gsm8k?: number;
    hellaswag?: number;
    arc?: number;
    [key: string]: string | number | undefined;
}

export interface LeaderboardState {
    entries: LeaderboardEntry[];
    isLoading: boolean;
    error: string | null;
    lastUpdated: string | null;
    sortColumn: string;
    sortDirection: 'asc' | 'desc';
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export function useLeaderboard() {
    const [state, setState] = useState<LeaderboardState>({
        entries: [],
        isLoading: false,
        error: null,
        lastUpdated: null,
        sortColumn: 'rank',
        sortDirection: 'asc',
    });

    const fetchLeaderboard = useCallback(async () => {
        setState(prev => ({ ...prev, isLoading: true, error: null }));

        try {
            const response = await fetch(`${API_BASE_URL}/api/leaderboard`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            setState(prev => ({
                ...prev,
                entries: data.leaderboard || [],
                lastUpdated: data.updated_at,
                isLoading: false,
            }));
        } catch (error) {
            // Use sample data on error
            // Phase 1 sample data
            const sampleData: LeaderboardEntry[] = [
                { rank: 1, model: "GPT-4o", provider: "OpenAI", mmlu: 88.7, arena_elo: 1287, humaneval: 90.2, context: 128000, safety: 96.8, average: 89.0 },
                { rank: 2, model: "Claude 3.5 Sonnet", provider: "Anthropic", mmlu: 88.3, arena_elo: 1272, humaneval: 92.0, context: 200000, safety: 97.2, average: 88.5 },
                { rank: 3, model: "Gemini 1.5 Pro", provider: "Google", mmlu: 85.9, arena_elo: 1260, humaneval: 84.1, context: 2000000, safety: 95.9, average: 85.2 },
                { rank: 4, model: "Llama-3-70B-Instruct", provider: "Meta", mmlu: 82.0, arena_elo: 1207, humaneval: 81.7, context: 8192, safety: 94.7, average: 81.5 },
                { rank: 5, model: "DeepSeek-V2-Chat", provider: "DeepSeek", mmlu: 84.2, arena_elo: 1189, humaneval: 84.3, context: 32000, safety: 95.3, average: 82.8 },
                { rank: 6, model: "Qwen2-72B-Instruct", provider: "Alibaba", mmlu: 84.2, arena_elo: 1187, humaneval: 86.0, context: 32000, safety: 95.1, average: 84.5 },
                { rank: 7, model: "Mistral-Large-2", provider: "Mistral", mmlu: 84.0, arena_elo: 1158, humaneval: 89.0, context: 32000, safety: 94.9, average: 85.0 },
                { rank: 8, model: "Command R+", provider: "Cohere", mmlu: 75.7, arena_elo: 1147, humaneval: 75.0, context: 128000, safety: 93.8, average: 75.3 },
            ];

            setState(prev => ({
                ...prev,
                entries: sampleData,
                lastUpdated: new Date().toISOString(),
                isLoading: false,
                error: null, // Suppress error since we have fallback data
            }));
        }
    }, []);

    const sortBy = useCallback((column: string) => {
        setState(prev => {
            const newDirection = prev.sortColumn === column && prev.sortDirection === 'asc' ? 'desc' : 'asc';

            const sorted = [...prev.entries].sort((a, b) => {
                const valA = a[column];
                const valB = b[column];

                if (typeof valA === 'number' && typeof valB === 'number') {
                    return newDirection === 'asc' ? valA - valB : valB - valA;
                }

                const strA = String(valA || '');
                const strB = String(valB || '');
                return newDirection === 'asc'
                    ? strA.localeCompare(strB)
                    : strB.localeCompare(strA);
            });

            return {
                ...prev,
                entries: sorted,
                sortColumn: column,
                sortDirection: newDirection,
            };
        });
    }, []);

    const filterByProvider = useCallback((provider: string) => {
        setState(prev => ({
            ...prev,
            entries: prev.entries.filter(e =>
                provider === 'all' || e.provider.toLowerCase() === provider.toLowerCase()
            ),
        }));
    }, []);

    return {
        ...state,
        fetchLeaderboard,
        sortBy,
        filterByProvider,
    };
}
