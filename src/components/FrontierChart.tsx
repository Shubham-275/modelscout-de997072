/**
 * FrontierChart - Cost-Performance Frontier Visualization
 * 
 * MANDATORY DISCLOSURES:
 * - Normalization scope is the filtered model set
 * - Frontier ≠ recommendation
 * - Frontier ≠ universal optimality
 * - Frontier ≠ ranking
 */

import { useMemo } from 'react';
import {
    ScatterChart,
    Scatter,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    Cell
} from 'recharts';
import { Info, AlertTriangle } from 'lucide-react';
import { FrontierData, FrontierPoint } from '@/hooks/usePhase2';

interface FrontierChartProps {
    data: FrontierData | null;
    loading?: boolean;
    error?: string | null;
}

// Custom tooltip component
const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    const point = payload[0].payload as FrontierPoint;

    return (
        <div className="bg-card/95 backdrop-blur-sm border border-border rounded-lg p-3 shadow-lg">
            <p className="font-mono text-sm font-bold text-foreground mb-2">
                {point.model_id}
            </p>
            <div className="space-y-1 text-xs font-mono">
                <p className="text-muted-foreground">
                    Cost (raw): <span className="text-foreground">${point.raw.cost.toFixed(4)}</span>
                </p>
                <p className="text-muted-foreground">
                    Capability (raw): <span className="text-foreground">{point.raw.capability.toFixed(2)}</span>
                </p>
                <p className="text-muted-foreground">
                    Normalized: ({point.normalized.cost.toFixed(2)}, {point.normalized.capability.toFixed(2)})
                </p>
                {point.is_pareto_optimal && (
                    <p className="text-secondary font-semibold">✓ On Pareto Frontier</p>
                )}
            </div>
        </div>
    );
};

const FrontierChart = ({ data, loading, error }: FrontierChartProps) => {
    // Prepare chart data
    const chartData = useMemo(() => {
        if (!data?.points) return [];

        return data.points.map(p => ({
            ...p,
            x: p.normalized.cost,
            y: p.normalized.capability,
        }));
    }, [data]);

    // Pareto frontier line data
    const paretoLine = useMemo(() => {
        if (!data?.points) return [];

        return data.points
            .filter(p => p.is_pareto_optimal)
            .sort((a, b) => a.normalized.cost - b.normalized.cost)
            .map(p => ({
                x: p.normalized.cost,
                y: p.normalized.capability,
            }));
    }, [data]);

    if (loading) {
        return (
            <div className="bento-card animate-pulse">
                <div className="h-4 bg-muted rounded w-1/3 mb-4"></div>
                <div className="h-64 bg-muted/50 rounded"></div>
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

    if (!data || !data.points.length) {
        return (
            <div className="bento-card">
                <div className="flex items-center gap-2 text-muted-foreground">
                    <Info className="w-4 h-4" />
                    <span className="font-mono text-sm">No frontier data available</span>
                </div>
            </div>
        );
    }

    return (
        <div className="bento-card">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-border">
                <h3 className="font-mono text-sm font-semibold text-foreground">
                    COST-PERFORMANCE FRONTIER
                </h3>
                <span className="text-xs font-mono text-muted-foreground">
                    {data.points.length} models
                </span>
            </div>

            {/* MANDATORY Warnings */}
            <div className="mt-4 p-2 bg-warning/10 border border-warning/30 rounded text-xs font-mono space-y-1">
                {data.warnings.map((warning, idx) => (
                    <p key={idx} className="text-warning/90">
                        <Info className="w-3 h-3 inline mr-1" />
                        {warning}
                    </p>
                ))}
            </div>

            {/* Chart */}
            <div className="mt-4 h-80">
                <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 40 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />

                        <XAxis
                            type="number"
                            dataKey="x"
                            domain={[0, 1]}
                            tickFormatter={(v) => v.toFixed(1)}
                            label={{
                                value: 'Cost (normalized) →',
                                position: 'bottom',
                                offset: 0,
                                style: { fill: 'hsl(var(--muted-foreground))', fontSize: 10, fontFamily: 'JetBrains Mono' }
                            }}
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                        />

                        <YAxis
                            type="number"
                            dataKey="y"
                            domain={[0, 1]}
                            tickFormatter={(v) => v.toFixed(1)}
                            label={{
                                value: '↑ Capability (normalized)',
                                angle: -90,
                                position: 'left',
                                offset: 10,
                                style: { fill: 'hsl(var(--muted-foreground))', fontSize: 10, fontFamily: 'JetBrains Mono' }
                            }}
                            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                        />

                        <Tooltip content={<CustomTooltip />} />

                        {/* Pareto frontier line */}
                        {paretoLine.length > 1 && (
                            <Scatter
                                name="Pareto Frontier"
                                data={paretoLine}
                                line={{ stroke: '#00d4ff', strokeWidth: 2, strokeDasharray: '5 5' }}
                                shape={() => null}
                            />
                        )}

                        {/* Data points */}
                        <Scatter
                            name="Models"
                            data={chartData}
                            fill="#00d4ff"
                        >
                            {chartData.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={entry.is_pareto_optimal ? '#00ff88' : '#00d4ff'}
                                    r={entry.is_pareto_optimal ? 8 : 5}
                                    stroke={entry.is_pareto_optimal ? '#ffffff' : 'transparent'}
                                    strokeWidth={2}
                                />
                            ))}
                        </Scatter>
                    </ScatterChart>
                </ResponsiveContainer>
            </div>

            {/* Legend */}
            <div className="mt-4 flex items-center justify-center gap-6 text-xs font-mono">
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-secondary border-2 border-white" />
                    <span className="text-muted-foreground">Pareto Optimal</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-primary" />
                    <span className="text-muted-foreground">Other Models</span>
                </div>
            </div>

            {/* Pareto Frontier Models */}
            {data.pareto_frontier.length > 0 && (
                <div className="mt-4 p-3 bg-secondary/10 border border-secondary/30 rounded">
                    <p className="text-xs font-mono text-secondary mb-2">
                        Pareto Frontier ({data.pareto_frontier.length} models):
                    </p>
                    <p className="text-xs font-mono text-muted-foreground">
                        {data.pareto_frontier.join(', ')}
                    </p>
                </div>
            )}

            {/* Tooltips (for hover/accessibility) */}
            <div className="mt-4 p-3 bg-muted/20 rounded border border-border/50 text-xs font-mono space-y-1">
                <p className="text-muted-foreground">
                    <strong>X-axis:</strong> {data.tooltips.x_axis}
                </p>
                <p className="text-muted-foreground">
                    <strong>Y-axis:</strong> {data.tooltips.y_axis}
                </p>
                <p className="text-muted-foreground">
                    <strong>Pareto:</strong> {data.tooltips.pareto}
                </p>
            </div>
        </div>
    );
};

export default FrontierChart;
