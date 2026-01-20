/**
 * PRSCard - Performance Reliability Score Display
 * 
 * CRITICAL: PRS is a NON-RANKING metric. This component MUST:
 * - Display the explicit "non-ranking" disclaimer
 * - Show full component breakdown
 * - Provide access to raw scores
 * - Never imply model preference
 */

import { useState } from 'react';
import { Info, AlertTriangle, TrendingUp, Shield, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { PRSResponse } from '@/hooks/usePhase2';

interface PRSCardProps {
    data: PRSResponse | null;
    loading?: boolean;
    error?: string | null;
}

const PRSCard = ({ data, loading, error }: PRSCardProps) => {
    const [showDetails, setShowDetails] = useState(false);
    const [showRawScores, setShowRawScores] = useState(false);

    if (loading) {
        return (
            <div className="bento-card animate-pulse">
                <div className="h-4 bg-muted rounded w-1/3 mb-4"></div>
                <div className="h-20 bg-muted/50 rounded"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bento-card border-destructive/50">
                <div className="flex items-center gap-2 text-destructive">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="font-mono text-sm">{error}</span>
                </div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="bento-card">
                <div className="flex items-center gap-2 text-muted-foreground">
                    <Info className="w-4 h-4" />
                    <span className="font-mono text-sm">Search a model to see PRS</span>
                </div>
            </div>
        );
    }

    const { prs, model_id, raw_scores, snapshot_id } = data;
    const { final_prs, components, audit, disclaimer } = prs;

    // Color based on PRS value
    const getPRSColor = (value: number) => {
        if (value >= 80) return 'text-secondary';
        if (value >= 60) return 'text-primary';
        if (value >= 40) return 'text-warning';
        return 'text-destructive';
    };

    // Progress bar color
    const getBarColor = (value: number) => {
        if (value >= 80) return 'bg-secondary';
        if (value >= 60) return 'bg-primary';
        if (value >= 40) return 'bg-warning';
        return 'bg-destructive';
    };

    return (
        <div className="bento-card">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-primary" />
                    <h3 className="font-mono text-sm font-semibold text-foreground">
                        PERFORMANCE RELIABILITY SCORE
                    </h3>
                </div>
                <span className="text-xs font-mono text-muted-foreground">
                    NON-RANKING
                </span>
            </div>

            {/* Disclaimer Banner */}
            <div className="mt-4 p-2 bg-warning/10 border border-warning/30 rounded text-xs text-warning/90 font-mono">
                <Info className="w-3 h-3 inline mr-1" />
                {disclaimer}
            </div>

            {/* Model & Score */}
            <div className="mt-4 flex items-center justify-between">
                <div>
                    <p className="text-xs text-muted-foreground font-mono">Model</p>
                    <p className="text-lg font-mono font-bold text-foreground">{model_id}</p>
                </div>
                <div className="text-right">
                    <p className="text-xs text-muted-foreground font-mono">PRS</p>
                    <p className={`text-3xl font-mono font-bold ${getPRSColor(final_prs)}`}>
                        {final_prs.toFixed(1)}
                    </p>
                </div>
            </div>

            {/* Component Bars */}
            <div className="mt-6 space-y-3">
                {/* Capability Consistency */}
                <div>
                    <div className="flex justify-between text-xs font-mono mb-1">
                        <span className="flex items-center gap-1 text-muted-foreground">
                            <TrendingUp className="w-3 h-3" />
                            Capability Consistency
                            <span className="text-primary/60">40%</span>
                        </span>
                        <span className={getPRSColor(components.capability_consistency.value)}>
                            {components.capability_consistency.value.toFixed(1)}
                        </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                            className={`h-full ${getBarColor(components.capability_consistency.value)} transition-all duration-500`}
                            style={{ width: `${components.capability_consistency.value}%` }}
                        />
                    </div>
                </div>

                {/* Benchmark Stability */}
                <div>
                    <div className="flex justify-between text-xs font-mono mb-1">
                        <span className="flex items-center gap-1 text-muted-foreground">
                            <Shield className="w-3 h-3" />
                            Benchmark Stability
                            <span className="text-primary/60">35%</span>
                        </span>
                        <span className={getPRSColor(components.benchmark_stability.value)}>
                            {components.benchmark_stability.value.toFixed(1)}
                        </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                            className={`h-full ${getBarColor(components.benchmark_stability.value)} transition-all duration-500`}
                            style={{ width: `${components.benchmark_stability.value}%` }}
                        />
                    </div>
                </div>

                {/* Temporal Reliability */}
                <div>
                    <div className="flex justify-between text-xs font-mono mb-1">
                        <span className="flex items-center gap-1 text-muted-foreground">
                            <Clock className="w-3 h-3" />
                            Temporal Reliability
                            <span className="text-primary/60">25%</span>
                        </span>
                        <span className={getPRSColor(components.temporal_reliability.value)}>
                            {components.temporal_reliability.value.toFixed(1)}
                        </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                            className={`h-full ${getBarColor(components.temporal_reliability.value)} transition-all duration-500`}
                            style={{ width: `${components.temporal_reliability.value}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* Expandable Details */}
            <button
                onClick={() => setShowDetails(!showDetails)}
                className="mt-4 w-full flex items-center justify-between py-2 px-3 bg-muted/30 rounded text-xs font-mono text-muted-foreground hover:bg-muted/50 transition-colors"
            >
                <span>Formula & Audit Trail</span>
                {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showDetails && (
                <div className="mt-3 p-3 bg-muted/20 rounded border border-border/50 text-xs font-mono space-y-2">
                    <div>
                        <span className="text-muted-foreground">Formula: </span>
                        <span className="text-foreground">{audit.formula}</span>
                    </div>
                    <div>
                        <span className="text-muted-foreground">Benchmarks: </span>
                        <span className="text-foreground">{audit.benchmarks_included.join(', ') || 'None'}</span>
                    </div>
                    {audit.missing_benchmarks.length > 0 && (
                        <div>
                            <span className="text-warning">Missing: </span>
                            <span className="text-warning/80">{audit.missing_benchmarks.join(', ')}</span>
                        </div>
                    )}
                    <div>
                        <span className="text-muted-foreground">Extractions: </span>
                        <span className="text-foreground">{audit.extraction_count}</span>
                    </div>
                    <div>
                        <span className="text-muted-foreground">Computed: </span>
                        <span className="text-foreground">{new Date(audit.computation_timestamp).toUTCString()}</span>
                    </div>
                    <div>
                        <span className="text-muted-foreground">Snapshot: </span>
                        <span className="text-foreground">{snapshot_id}</span>
                    </div>
                </div>
            )}

            {/* Raw Scores (DATA TRANSPARENCY) */}
            <button
                onClick={() => setShowRawScores(!showRawScores)}
                className="mt-2 w-full flex items-center justify-between py-2 px-3 bg-secondary/10 rounded text-xs font-mono text-secondary hover:bg-secondary/20 transition-colors"
            >
                <span>📊 View Raw Benchmark Scores</span>
                {showRawScores ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showRawScores && (
                <div className="mt-3 p-3 bg-secondary/5 rounded border border-secondary/30 text-xs font-mono">
                    <p className="text-muted-foreground mb-2">Raw values (unmodified from source):</p>
                    <div className="grid grid-cols-2 gap-2">
                        {Object.entries(raw_scores).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                                <span className="text-muted-foreground">{key}:</span>
                                <span className="text-foreground">{typeof value === 'number' ? value.toFixed(2) : value}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default PRSCard;
