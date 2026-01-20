import { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export interface PRSComponents {
    capability_consistency: {
        value: number;
        weight: number;
        weighted_contribution: number;
        definition: string;
    };
    benchmark_stability: {
        value: number;
        weight: number;
        weighted_contribution: number;
        definition: string;
    };
    temporal_reliability: {
        value: number;
        weight: number;
        weighted_contribution: number;
        definition: string;
    };
}

export interface PRSData {
    final_prs: number;
    components: PRSComponents;
    audit: {
        benchmarks_included: string[];
        extraction_count: number;
        missing_benchmarks: string[];
        computation_timestamp: string;
        formula: string;
    };
    disclaimer: string;
}

export interface PRSResponse {
    model_id: string;
    prs: PRSData;
    snapshot_id: string;
    raw_scores: Record<string, number>;
}

export interface Snapshot {
    snapshot_id: string;
    timestamp_utc: string;
    content_hash: string;
    model_count: number;
    models: string[];
}

export interface SnapshotDiff {
    status: 'comparable' | 'incomparable_version_mismatch' | 'incomparable_benchmark_mismatch' | 'no_previous_snapshot';
    current_snapshot_id: string;
    previous_snapshot_id: string | null;
    score_deltas: Record<string, Record<string, number>>;
    explanation: string;
    is_comparable: boolean;
    version_mismatches?: Array<{
        benchmark_id: string;
        current_version: string;
        previous_version: string;
    }>;
}

export interface RegressionEvent {
    model_id: string;
    benchmark: {
        id: string;
        category: string;
    };
    scores: {
        current: number;
        previous: number;
        delta_absolute: number;
        delta_percentage: number;
    };
    severity: 'none' | 'minor' | 'major';
    is_regression: boolean;
    explanation: string;
}

export interface RegressionReport {
    model_id: string;
    summary: {
        benchmarks_analyzed: number;
        regressions_found: number;
        minor_regressions: number;
        major_regressions: number;
        has_major_regression: boolean;
    };
    events: RegressionEvent[];
    snapshots?: {
        current: string;
        previous: string;
    };
}

export interface FrontierPoint {
    model_id: string;
    raw: { cost: number; capability: number };
    normalized: { cost: number; capability: number };
    is_pareto_optimal: boolean;
}

export interface FrontierData {
    points: FrontierPoint[];
    pareto_frontier: string[];
    warnings: string[];
    tooltips: Record<string, string>;
}

// Hook: Fetch PRS for a model
export function usePRS(modelId: string | null) {
    const [data, setData] = useState<PRSResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!modelId) {
            setData(null);
            return;
        }

        const fetchPRS = async () => {
            setLoading(true);
            setError(null);

            try {
                const response = await fetch(`${API_BASE}/api/v2/prs/${encodeURIComponent(modelId)}`);

                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.error || `HTTP ${response.status}`);
                }

                const result = await response.json();
                setData(result);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        };

        fetchPRS();
    }, [modelId]);

    return { data, loading, error };
}

// Hook: Fetch snapshots
export function useSnapshots(limit: number = 10) {
    const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchSnapshots = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/v2/snapshots?limit=${limit}`);

                if (!response.ok) throw new Error('Failed to fetch snapshots');

                const result = await response.json();
                setSnapshots(result.snapshots || []);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        };

        fetchSnapshots();
    }, [limit]);

    return { snapshots, loading, error };
}

// Hook: Fetch snapshot diff
export function useSnapshotDiff() {
    const [diff, setDiff] = useState<SnapshotDiff | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchDiff = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/v2/snapshots/diff`);

                if (!response.ok) {
                    const errData = await response.json();
                    // Handle "no snapshots" gracefully
                    if (response.status === 404) {
                        setDiff(null);
                        return;
                    }
                    throw new Error(errData.error || 'Failed to fetch diff');
                }

                const result = await response.json();
                setDiff(result);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        };

        fetchDiff();
    }, []);

    return { diff, loading, error };
}

// Hook: Detect regressions for a model
export function useRegressionDetection(modelId: string | null) {
    const [report, setReport] = useState<RegressionReport | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const detect = async (customThresholds?: { minor: number; major: number }) => {
        if (!modelId) return;

        setLoading(true);
        setError(null);

        try {
            const body = customThresholds ? {
                thresholds: {
                    minor_threshold_pct: customThresholds.minor,
                    major_threshold_pct: customThresholds.major
                }
            } : {};

            const response = await fetch(`${API_BASE}/api/v2/regressions/detect/${encodeURIComponent(modelId)}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Regression detection failed');
            }

            const result = await response.json();
            setReport(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    return { report, loading, error, detect };
}

// Hook: Fetch frontier data
export function useFrontier(costMetric: string = 'input_price', capabilityMetric: string = 'average_score') {
    const [frontier, setFrontier] = useState<FrontierData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchFrontier = async () => {
            try {
                const response = await fetch(
                    `${API_BASE}/api/v2/frontier?cost_metric=${costMetric}&capability_metric=${capabilityMetric}`
                );

                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.error || 'Failed to fetch frontier');
                }

                const result = await response.json();
                setFrontier(result);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        };

        fetchFrontier();
    }, [costMetric, capabilityMetric]);

    return { frontier, loading, error };
}
