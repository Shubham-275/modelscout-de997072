/**
 * SnapshotDiffPanel - Temporal Snapshot Comparison
 * 
 * STRICT SEMANTICS:
 * - "T-1" = last successful extraction with identical benchmark IDs + versions
 * - If benchmark versions differ → diff is disabled and labeled "Incomparable"
 * - No cross-version comparisons allowed
 */

import { useState } from 'react';
import { GitCompare, AlertTriangle, Info, Check, X } from 'lucide-react';
import { SnapshotDiff, Snapshot } from '@/hooks/usePhase2';

interface SnapshotDiffPanelProps {
    diff: SnapshotDiff | null;
    snapshots: Snapshot[];
    loading: boolean;
    error: string | null;
}

const SnapshotDiffPanel = ({ diff, snapshots, loading, error }: SnapshotDiffPanelProps) => {
    const [expandedModel, setExpandedModel] = useState<string | null>(null);

    if (loading) {
        return (
            <div className="bento-card animate-pulse">
                <div className="h-4 bg-muted rounded w-1/3 mb-4"></div>
                <div className="h-32 bg-muted/50 rounded"></div>
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

    return (
        <div className="bento-card">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center gap-2">
                    <GitCompare className="w-4 h-4 text-primary" />
                    <h3 className="font-mono text-sm font-semibold text-foreground">
                        TEMPORAL SNAPSHOT DIFF
                    </h3>
                </div>
                <span className="text-xs font-mono text-muted-foreground">
                    {snapshots.length} snapshots
                </span>
            </div>

            {/* No Snapshots */}
            {snapshots.length === 0 && (
                <div className="mt-4 text-center py-8">
                    <GitCompare className="w-8 h-8 text-muted-foreground mx-auto mb-2 opacity-50" />
                    <p className="text-sm font-mono text-muted-foreground">
                        No snapshots available
                    </p>
                    <p className="text-xs text-muted-foreground/70 mt-1">
                        Run an extraction to create the first snapshot
                    </p>
                </div>
            )}

            {/* Single Snapshot */}
            {snapshots.length === 1 && (
                <div className="mt-4 p-3 bg-muted/20 rounded border border-border/50">
                    <div className="flex items-center gap-2 text-warning mb-2">
                        <Info className="w-4 h-4" />
                        <span className="font-mono text-sm">Only one snapshot available</span>
                    </div>
                    <p className="text-xs font-mono text-muted-foreground">
                        Cannot compute diff without a previous snapshot.
                    </p>
                    <div className="mt-3 p-2 bg-background/50 rounded text-xs font-mono">
                        <p><span className="text-muted-foreground">Snapshot:</span> {snapshots[0].snapshot_id}</p>
                        <p><span className="text-muted-foreground">Models:</span> {snapshots[0].model_count}</p>
                        <p><span className="text-muted-foreground">Time:</span> {new Date(snapshots[0].timestamp_utc).toUTCString()}</p>
                    </div>
                </div>
            )}

            {/* Diff Result */}
            {diff && (
                <div className="mt-4 space-y-4">
                    {/* Status Badge */}
                    <div className={`p-3 rounded border ${diff.is_comparable
                        ? 'bg-secondary/10 border-secondary/30'
                        : 'bg-destructive/10 border-destructive/30'
                        }`}>
                        <div className="flex items-center gap-2">
                            {diff.is_comparable ? (
                                <Check className="w-4 h-4 text-secondary" />
                            ) : (
                                <X className="w-4 h-4 text-destructive" />
                            )}
                            <span className={`font-mono text-sm font-semibold ${diff.is_comparable ? 'text-secondary' : 'text-destructive'
                                }`}>
                                {diff.is_comparable ? 'COMPARABLE' : diff.status.toUpperCase().replace(/_/g, ' ')}
                            </span>
                        </div>
                        <p className="mt-2 text-xs font-mono text-muted-foreground">
                            {diff.explanation}
                        </p>
                    </div>

                    {/* Version Mismatches (if any) */}
                    {diff.version_mismatches && diff.version_mismatches.length > 0 && (
                        <div className="p-3 bg-warning/10 border border-warning/30 rounded">
                            <p className="text-xs font-mono text-warning font-semibold mb-2">
                                Version Mismatches (Cross-version comparison prohibited):
                            </p>
                            {diff.version_mismatches.map((mismatch, idx) => (
                                <div key={idx} className="text-xs font-mono text-muted-foreground">
                                    <span className="text-foreground">{mismatch.benchmark_id}:</span>{' '}
                                    {mismatch.previous_version} → {mismatch.current_version}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Score Deltas (if comparable) */}
                    {diff.is_comparable && Object.keys(diff.score_deltas).length > 0 && (
                        <div className="space-y-2">
                            <p className="text-xs font-mono text-muted-foreground">
                                Score Changes by Model:
                            </p>

                            {Object.entries(diff.score_deltas).map(([modelId, benchmarks]) => (
                                <div
                                    key={modelId}
                                    className="p-3 bg-muted/20 rounded border border-border/50"
                                >
                                    <button
                                        onClick={() => setExpandedModel(expandedModel === modelId ? null : modelId)}
                                        className="w-full flex items-center justify-between text-left"
                                    >
                                        <span className="font-mono text-sm text-foreground">{modelId}</span>
                                        <span className="text-xs font-mono text-muted-foreground">
                                            {Object.keys(benchmarks).length} benchmarks
                                        </span>
                                    </button>

                                    {expandedModel === modelId && (
                                        <div className="mt-3 grid grid-cols-2 gap-2">
                                            {Object.entries(benchmarks).map(([benchmark, delta]) => (
                                                <div key={benchmark} className="flex justify-between text-xs font-mono">
                                                    <span className="text-muted-foreground">{benchmark}:</span>
                                                    <span className={
                                                        (delta as number) > 0
                                                            ? 'text-secondary'
                                                            : (delta as number) < 0
                                                                ? 'text-destructive'
                                                                : 'text-muted-foreground'
                                                    }>
                                                        {(delta as number) > 0 ? '+' : ''}{(delta as number).toFixed(2)}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Snapshot IDs */}
                    <div className="p-3 bg-muted/20 rounded border border-border/50 text-xs font-mono">
                        <p className="text-muted-foreground mb-1">Comparison:</p>
                        <p>
                            <span className="text-muted-foreground">Current:</span>{' '}
                            <span className="text-primary">{diff.current_snapshot_id}</span>
                        </p>
                        <p>
                            <span className="text-muted-foreground">Previous:</span>{' '}
                            <span className="text-primary">{diff.previous_snapshot_id || 'None'}</span>
                        </p>
                    </div>
                </div>
            )}

            {/* Snapshot List */}
            {snapshots.length > 1 && (
                <div className="mt-4">
                    <p className="text-xs font-mono text-muted-foreground mb-2">Recent Snapshots:</p>
                    <div className="space-y-2">
                        {snapshots.slice(0, 5).map((snap, idx) => (
                            <div
                                key={snap.snapshot_id}
                                className={`p-2 rounded text-xs font-mono ${idx === 0 ? 'bg-primary/10 border border-primary/30' : 'bg-muted/20'
                                    }`}
                            >
                                <div className="flex justify-between">
                                    <span className={idx === 0 ? 'text-primary' : 'text-muted-foreground'}>
                                        {idx === 0 ? '● Current' : `T-${idx}`}
                                    </span>
                                    <span className="text-muted-foreground">
                                        {snap.model_count} models
                                    </span>
                                </div>
                                <p className="text-muted-foreground/70 truncate">
                                    {snap.snapshot_id}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default SnapshotDiffPanel;
