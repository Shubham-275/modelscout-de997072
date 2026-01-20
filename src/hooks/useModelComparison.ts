import { useState, useCallback, useRef } from 'react';

export interface BenchmarkMetrics {
    mmlu?: number;
    arc_challenge?: number;
    hellaswag?: number;
    truthfulqa?: number;
    winogrande?: number;
    gsm8k?: number;
    arena_elo?: number;
    humaneval?: number;
    mbpp?: number;
    mt_bench?: number;
    alpaca_eval?: number;
    [key: string]: number | undefined;
}

export interface ModelResult {
    model: string;
    rank: number;
    average_score: number;
    benchmark_metrics: BenchmarkMetrics;
    source: string;
    scraped_at: string;
}

export interface StreamEvent {
    source: string;
    model?: string;
    type: 'log' | 'error' | 'result' | 'done' | 'complete' | 'system' | 'cache_hit' | 'init';
    data: string | ModelResult;
    timestamp: string;
}

export interface ComparisonState {
    modelA: Record<string, ModelResult>;
    modelB: Record<string, ModelResult>;
    logs: StreamEvent[];
    isLoading: boolean;
    error: string | null;
    modelAName: string;
    modelBName: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export function useModelComparison() {
    const [state, setState] = useState<ComparisonState>({
        modelA: {},
        modelB: {},
        logs: [],
        isLoading: false,
        error: null,
        modelAName: '',
        modelBName: '',
    });

    const abortControllerRef = useRef<AbortController | null>(null);

    const compareModels = useCallback(async (
        modelA: string,
        modelB: string,
        // Phase 1 sources only
        sources: string[] = ['huggingface', 'lmsys_arena', 'livecodebench', 'vellum', 'mask', 'vectara']
    ) => {
        // Abort any existing request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        abortControllerRef.current = new AbortController();

        setState(prev => ({
            ...prev,
            modelA: {},
            modelB: {},
            logs: [],
            isLoading: true,
            error: null,
            modelAName: modelA,
            modelBName: modelB,
        }));

        try {
            const response = await fetch(`${API_BASE_URL}/api/compare`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_a: modelA, model_b: modelB, sources }),
                signal: abortControllerRef.current.signal,
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const reader = response.body?.getReader();
            if (!reader) throw new Error('No response body');

            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // Parse SSE events from buffer
                const events = buffer.split('\n\n');
                buffer = events.pop() || ''; // Keep incomplete event in buffer

                for (const eventStr of events) {
                    if (!eventStr.startsWith('data: ')) continue;

                    const jsonStr = eventStr.slice(6); // Remove "data: " prefix

                    try {
                        const event: StreamEvent = JSON.parse(jsonStr);

                        setState(prev => {
                            const newLogs = [...prev.logs, event];
                            let newModelA = { ...prev.modelA };
                            let newModelB = { ...prev.modelB };

                            // If this is a result, parse and store it
                            if (event.type === 'result' && typeof event.data === 'object') {
                                const result = event.data as ModelResult;
                                const isModelA = event.model === modelA ||
                                    result.model?.toLowerCase().includes(modelA.toLowerCase());

                                if (isModelA) {
                                    newModelA[event.source] = result;
                                } else {
                                    newModelB[event.source] = result;
                                }
                            }

                            if (event.type === 'complete') {
                                return {
                                    ...prev,
                                    logs: newLogs,
                                    modelA: newModelA,
                                    modelB: newModelB,
                                    isLoading: false
                                };
                            }

                            return {
                                ...prev,
                                logs: newLogs,
                                modelA: newModelA,
                                modelB: newModelB,
                            };
                        });

                    } catch {
                        console.warn('Failed to parse SSE event:', jsonStr);
                    }
                }
            }

            setState(prev => ({ ...prev, isLoading: false }));

        } catch (error) {
            if ((error as Error).name === 'AbortError') {
                console.log('Comparison aborted');
                return;
            }

            setState(prev => ({
                ...prev,
                isLoading: false,
                error: (error as Error).message,
            }));
        }
    }, []);

    const cancelComparison = useCallback(() => {
        abortControllerRef.current?.abort();
        setState(prev => ({ ...prev, isLoading: false }));
    }, []);

    const reset = useCallback(() => {
        abortControllerRef.current?.abort();
        setState({
            modelA: {},
            modelB: {},
            logs: [],
            isLoading: false,
            error: null,
            modelAName: '',
            modelBName: '',
        });
    }, []);

    // Calculate deltas between models
    const getDeltas = useCallback(() => {
        const deltas: Record<string, { metric: string; delta: number; winner: 'A' | 'B' | 'tie' }[]> = {};

        const sources = new Set([
            ...Object.keys(state.modelA),
            ...Object.keys(state.modelB)
        ]);

        for (const source of sources) {
            const resultA = state.modelA[source];
            const resultB = state.modelB[source];

            if (resultA && resultB) {
                const metrics: { metric: string; delta: number; winner: 'A' | 'B' | 'tie' }[] = [];

                // Average score
                const avgDelta = (resultA.average_score || 0) - (resultB.average_score || 0);
                metrics.push({
                    metric: 'average_score',
                    delta: avgDelta,
                    winner: avgDelta > 0 ? 'A' : avgDelta < 0 ? 'B' : 'tie'
                });

                // Individual metrics
                const allMetrics = new Set([
                    ...Object.keys(resultA.benchmark_metrics || {}),
                    ...Object.keys(resultB.benchmark_metrics || {})
                ]);

                for (const metric of allMetrics) {
                    const valA = resultA.benchmark_metrics?.[metric] ?? 0;
                    const valB = resultB.benchmark_metrics?.[metric] ?? 0;
                    const delta = valA - valB;

                    metrics.push({
                        metric,
                        delta,
                        winner: delta > 0 ? 'A' : delta < 0 ? 'B' : 'tie'
                    });
                }

                deltas[source] = metrics;
            }
        }

        return deltas;
    }, [state.modelA, state.modelB]);

    return {
        ...state,
        compareModels,
        cancelComparison,
        reset,
        getDeltas,
    };
}
