import React, { useMemo } from 'react';
import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer,
    Tooltip,
} from 'recharts';

/**
 * ExpertiseRadarChart - Recharts-based Spider/Radar chart
 * Displays 5 axes: Logic, Coding, Math, Safety, Cyber
 * All metrics normalized to 0-100 scale
 */

interface RadarDataPoint {
    category: string;
    score: number;
    maxScore?: number;
}

interface ExpertiseRadarChartProps {
    data: RadarDataPoint[];
    modelName?: string;
    className?: string;
}

// Phase 1: 4 axes for capability fingerprint
const RADAR_AXES = ['Logic', 'Coding', 'Economics', 'Safety'];

// Map Phase 1 source categories to the 4 axes
const CATEGORY_MAPPING: Record<string, string> = {
    // Logic axis (General intelligence benchmarks)
    'logic': 'Logic',
    'reasoning': 'Logic',
    'huggingface': 'Logic',
    'lmsys_arena': 'Logic',
    'general': 'Logic',

    // Coding axis
    'coding': 'Coding',
    'livecodebench': 'Coding',
    'humaneval': 'Coding',

    // Economics axis (Cost, speed, efficiency)
    'economics': 'Economics',
    'vellum': 'Economics',

    // Safety axis (Hallucination, deception)
    'safety': 'Safety',
    'mask': 'Safety',
    'vectara': 'Safety',
    'hallucination': 'Safety',
};

// Normalize score to 0-100 scale
const normalizeScore = (score: number, maxScore: number = 100): number => {
    if (maxScore <= 0) return 0;
    // Handle ELO scores (typically 1000-1400 range)
    if (maxScore > 1000) {
        // Normalize ELO to 0-100 (assuming 1000-1400 range)
        const normalized = ((score - 1000) / 400) * 100;
        return Math.max(0, Math.min(100, normalized));
    }
    // Standard percentage normalization
    const normalized = (score / maxScore) * 100;
    return Math.max(0, Math.min(100, normalized));
};

// Custom tooltip component
const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload;
        return (
            <div className="bg-card/95 backdrop-blur-sm border border-primary/50 rounded-lg px-3 py-2 shadow-lg">
                <p className="text-primary font-mono text-sm font-bold">{data.category}</p>
                <p className="text-foreground font-mono text-xs">
                    Score: <span className="text-secondary">{data.value.toFixed(1)}</span>
                </p>
            </div>
        );
    }
    return null;
};

export const ExpertiseRadarChart: React.FC<ExpertiseRadarChartProps> = ({
    data,
    modelName = 'Model',
    className = '',
}) => {
    // Transform and normalize data for Recharts
    const chartData = useMemo(() => {
        // Create a map of axis -> aggregated scores
        const axisScores: Record<string, { total: number; count: number }> = {};

        // Initialize all axes with 0
        RADAR_AXES.forEach(axis => {
            axisScores[axis] = { total: 0, count: 0 };
        });

        // Map incoming data to axes
        data.forEach(item => {
            const categoryLower = item.category.toLowerCase();
            const mappedAxis = CATEGORY_MAPPING[categoryLower] || 'Logic'; // Default to Logic

            if (axisScores[mappedAxis]) {
                const normalizedScore = normalizeScore(item.score, item.maxScore || 100);
                axisScores[mappedAxis].total += normalizedScore;
                axisScores[mappedAxis].count += 1;
            }
        });

        // Convert to Recharts format with averaged scores
        return RADAR_AXES.map(axis => ({
            category: axis,
            value: axisScores[axis].count > 0
                ? axisScores[axis].total / axisScores[axis].count
                : 0,
            fullMark: 100,
        }));
    }, [data]);

    // Check if we have any real data
    const hasData = chartData.some(d => d.value > 0);

    return (
        <div className={`relative ${className}`}>
            {/* Title */}
            {modelName && (
                <div className="text-center mb-2">
                    <h3 className="text-sm font-mono text-primary">{modelName}</h3>
                    <p className="text-xs text-muted-foreground">Expertise Fingerprint</p>
                </div>
            )}

            {hasData ? (
                <ResponsiveContainer width="100%" height={280}>
                    <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
                        {/* Grid lines */}
                        <PolarGrid
                            stroke="hsl(var(--border))"
                            strokeOpacity={0.5}
                            gridType="polygon"
                        />

                        {/* Axis labels */}
                        <PolarAngleAxis
                            dataKey="category"
                            tick={{
                                fill: 'hsl(var(--foreground))',
                                fontSize: 11,
                                fontFamily: 'JetBrains Mono, monospace',
                            }}
                            tickLine={false}
                        />

                        {/* Radius axis (0-100) */}
                        <PolarRadiusAxis
                            angle={90}
                            domain={[0, 100]}
                            tick={{
                                fill: 'hsl(var(--muted-foreground))',
                                fontSize: 9
                            }}
                            tickCount={5}
                            axisLine={false}
                        />

                        {/* Data polygon - Cyan color, 0.6 opacity fill, 2px stroke */}
                        <Radar
                            name={modelName}
                            dataKey="value"
                            stroke="#00d4ff"
                            strokeWidth={2}
                            fill="#00d4ff"
                            fillOpacity={0.6}
                            dot={{
                                r: 4,
                                fill: '#00d4ff',
                                stroke: 'hsl(var(--background))',
                                strokeWidth: 2,
                            }}
                            activeDot={{
                                r: 6,
                                fill: '#00d4ff',
                                stroke: '#ffffff',
                                strokeWidth: 2,
                            }}
                        />

                        {/* Tooltip */}
                        <Tooltip content={<CustomTooltip />} />
                    </RadarChart>
                </ResponsiveContainer>
            ) : (
                <div className="flex flex-col items-center justify-center h-64 text-muted-foreground p-4 text-center">
                    <svg
                        className="w-16 h-16 mb-3 opacity-30"
                        viewBox="0 0 100 100"
                        fill="none"
                        stroke="currentColor"
                    >
                        {/* Pentagon shape */}
                        <polygon
                            points="50,10 90,40 75,85 25,85 10,40"
                            strokeWidth="2"
                            fill="none"
                        />
                        <circle cx="50" cy="50" r="3" fill="currentColor" opacity="0.5" />
                    </svg>
                    <p className="text-sm font-mono text-warning">Insufficient Coverage</p>
                    <p className="text-xs mt-1 text-muted-foreground max-w-[200px]">
                        Requires &ge; 1 benchmark categories<br />
                        (currently: {chartData.filter(d => d.value > 0).length} / 4 available)
                    </p>
                </div>
            )}

            {/* Score Legend */}
            {hasData && (
                <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 mt-2 px-2">
                    {chartData.map((item) => (
                        <div
                            key={item.category}
                            className="flex items-center gap-1 text-xs font-mono"
                        >
                            <div
                                className="w-2 h-2 rounded-full"
                                style={{ backgroundColor: '#00d4ff' }}
                            />
                            <span className="text-muted-foreground">
                                {item.category}:{' '}
                                <span className={item.value > 0 ? 'text-primary' : 'text-muted-foreground'}>
                                    {item.value > 0 ? item.value.toFixed(1) : 'N/A'}
                                </span>
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ExpertiseRadarChart;
