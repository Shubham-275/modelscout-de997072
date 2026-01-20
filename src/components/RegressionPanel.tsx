/**
 * RegressionPanel - Regression Detection Display
 * 
 * UI REQUIREMENTS:
 * - Show exact delta %
 * - Show benchmark source
 * - Show snapshot IDs used
 * - No silent flags
 */

import { useState } from 'react';
import { AlertTriangle, TrendingDown, Info, CheckCircle2 } from 'lucide-react';
import { RegressionReport, RegressionEvent } from '@/hooks/usePhase2';
import { Button } from '@/components/ui/button';

interface RegressionPanelProps {
    modelId: string | null;
    report: RegressionReport | null;
    loading: boolean;
    error: string | null;
    onDetect: () => void;
}

const RegressionPanel = ({ modelId, report, loading, error, onDetect }: RegressionPanelProps) => {
    const [showAllEvents, setShowAllEvents] = useState(false);

    if (!modelId) {
        return (
            <div className="bento-card">
                <div className="flex items-center gap-2 text-muted-foreground">
                    <Info className="w-4 h-4" />
                    <span className="font-mono text-sm">Select a model to detect regressions</span>
                </div>
            </div>
        );
    }

    return (
        <div className="bento-card">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center gap-2">
                    <TrendingDown className="w-4 h-4 text-warning" />
                    <h3 className="font-mono text-sm font-semibold text-foreground">
                        REGRESSION DETECTION
                    </h3>
                </div>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={onDetect}
                    disabled={loading}
                    className="font-mono text-xs"
                >
                    {loading ? 'Analyzing...' : 'Detect'}
                </Button>
            </div>

            {/* Error State */}
            {error && (
                <div className="mt-4 p-3 bg-destructive/10 border border-destructive/30 rounded">
                    <p className="text-xs font-mono text-destructive">{error}</p>
                </div>
            )}

            {/* No Report Yet */}
            {!report && !loading && !error && (
                <div className="mt-4 text-center py-8">
                    <TrendingDown className="w-8 h-8 text-muted-foreground mx-auto mb-2 opacity-50" />
                    <p className="text-sm font-mono text-muted-foreground">
                        Click "Detect" to analyze regressions
                    </p>
                    <p className="text-xs text-muted-foreground/70 mt-1">
                        Compares current vs. previous snapshot
                    </p>
                </div>
            )}

            {/* Report */}
            {report && (
                <div className="mt-4 space-y-4">
                    {/* Summary */}
                    <div className="grid grid-cols-3 gap-4">
                        <div className="text-center p-3 bg-muted/30 rounded">
                            <p className="text-2xl font-mono font-bold text-foreground">
                                {report.summary.benchmarks_analyzed}
                            </p>
                            <p className="text-xs font-mono text-muted-foreground">Benchmarks</p>
                        </div>
                        <div className={`text-center p-3 rounded ${report.summary.regressions_found > 0
                                ? 'bg-warning/10 border border-warning/30'
                                : 'bg-secondary/10 border border-secondary/30'
                            }`}>
                            <p className={`text-2xl font-mono font-bold ${report.summary.regressions_found > 0 ? 'text-warning' : 'text-secondary'
                                }`}>
                                {report.summary.regressions_found}
                            </p>
                            <p className="text-xs font-mono text-muted-foreground">Regressions</p>
                        </div>
                        <div className={`text-center p-3 rounded ${report.summary.has_major_regression
                                ? 'bg-destructive/10 border border-destructive/30'
                                : 'bg-muted/30'
                            }`}>
                            <p className={`text-2xl font-mono font-bold ${report.summary.has_major_regression ? 'text-destructive' : 'text-muted-foreground'
                                }`}>
                                {report.summary.major_regressions}
                            </p>
                            <p className="text-xs font-mono text-muted-foreground">Major</p>
                        </div>
                    </div>

                    {/* Regression Events */}
                    {report.events.length > 0 && (
                        <div className="space-y-2">
                            <p className="text-xs font-mono text-muted-foreground">Benchmark Analysis:</p>

                            {(showAllEvents ? report.events : report.events.slice(0, 5)).map((event, idx) => (
                                <RegressionEventRow key={idx} event={event} />
                            ))}

                            {report.events.length > 5 && (
                                <button
                                    onClick={() => setShowAllEvents(!showAllEvents)}
                                    className="w-full py-2 text-xs font-mono text-primary hover:text-primary/80"
                                >
                                    {showAllEvents ? 'Show less' : `Show ${report.events.length - 5} more`}
                                </button>
                            )}
                        </div>
                    )}

                    {/* Snapshot Audit Trail */}
                    <div className="p-3 bg-muted/20 rounded border border-border/50 text-xs font-mono">
                        <p className="text-muted-foreground mb-1">Snapshot Comparison:</p>
                        <p className="text-foreground">
                            Current: <span className="text-primary">{report.snapshots?.current || 'N/A'}</span>
                        </p>
                        <p className="text-foreground">
                            Previous: <span className="text-primary">{report.snapshots?.previous || 'N/A'}</span>
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

// Sub-component for individual regression events
const RegressionEventRow = ({ event }: { event: RegressionEvent }) => {
    const getSeverityStyles = (severity: string, isRegression: boolean) => {
        if (!isRegression || severity === 'none') {
            return {
                bg: 'bg-secondary/10',
                border: 'border-secondary/30',
                icon: <CheckCircle2 className="w-4 h-4 text-secondary" />,
                text: 'text-secondary'
            };
        }
        if (severity === 'major') {
            return {
                bg: 'bg-destructive/10',
                border: 'border-destructive/30',
                icon: <AlertTriangle className="w-4 h-4 text-destructive" />,
                text: 'text-destructive'
            };
        }
        return {
            bg: 'bg-warning/10',
            border: 'border-warning/30',
            icon: <AlertTriangle className="w-4 h-4 text-warning" />,
            text: 'text-warning'
        };
    };

    const styles = getSeverityStyles(event.severity, event.is_regression);

    return (
        <div className={`p-3 rounded border ${styles.bg} ${styles.border}`}>
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    {styles.icon}
                    <span className="font-mono text-sm text-foreground">
                        {event.benchmark.id}
                    </span>
                    <span className="text-xs text-muted-foreground">
                        ({event.benchmark.category})
                    </span>
                </div>
                <div className="text-right">
                    {/* EXACT DELTA % - Required by spec */}
                    <span className={`font-mono text-sm font-bold ${styles.text}`}>
                        {event.scores.delta_percentage > 0 ? '+' : ''}
                        {event.scores.delta_percentage.toFixed(2)}%
                    </span>
                </div>
            </div>

            {/* Score details */}
            <div className="mt-2 flex justify-between text-xs font-mono text-muted-foreground">
                <span>
                    {event.scores.previous.toFixed(2)} → {event.scores.current.toFixed(2)}
                </span>
                <span className={event.scores.delta_absolute >= 0 ? 'text-secondary' : styles.text}>
                    Δ {event.scores.delta_absolute >= 0 ? '+' : ''}{event.scores.delta_absolute.toFixed(2)}
                </span>
            </div>

            {/* Explanation - No silent flags */}
            <p className="mt-1 text-xs text-muted-foreground/80">
                {event.explanation}
            </p>
        </div>
    );
};

export default RegressionPanel;
