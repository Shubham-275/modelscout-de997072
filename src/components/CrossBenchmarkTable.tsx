import { useEffect } from "react";
import { Table, ArrowUpDown, ArrowUp, ArrowDown, RefreshCw, ExternalLink } from "lucide-react";
import { useLeaderboard } from "@/hooks/useLeaderboard";
import { Button } from "@/components/ui/button";

interface CrossBenchmarkTableProps {
    className?: string;
}

const METRIC_COLUMNS = [
    { key: 'rank', label: 'Phase-1 Composite', tooltip: 'Unweighted aggregation of available benchmarks only. Incomplete coverage. For exploratory comparison only.' },
    { key: 'model', label: 'Model', tooltip: 'Model name (Canonical ID)' },
    { key: 'provider', label: 'Provider', tooltip: 'Organization' },
    { key: 'mmlu', label: 'MMLU', tooltip: 'General Intelligence (HuggingFace)' },
    { key: 'arena_elo', label: 'Arena ELO', tooltip: 'User Preference (LMSYS)' },
    { key: 'humaneval', label: 'HumanEval', tooltip: 'Coding (LiveCodeBench)' },
    { key: 'context', label: 'Ctx Window', tooltip: 'Economics/Context (Vellum)' },
    { key: 'safety', label: 'Safety', tooltip: 'Safety Score (MASK/Vectara)' },
    { key: 'average', label: 'Composite Score', tooltip: 'mean of available normalized scores only. Missing benchmarks do not penalize.' },
];

const CrossBenchmarkTable = ({ className }: CrossBenchmarkTableProps) => {
    const { entries, isLoading, lastUpdated, sortColumn, sortDirection, fetchLeaderboard, sortBy } = useLeaderboard();

    useEffect(() => {
        fetchLeaderboard();
    }, [fetchLeaderboard]);

    const getSortIcon = (column: string) => {
        if (sortColumn !== column) {
            return <ArrowUpDown className="w-3 h-3 text-muted-foreground" />;
        }
        return sortDirection === 'asc'
            ? <ArrowUp className="w-3 h-3 text-primary" />
            : <ArrowDown className="w-3 h-3 text-primary" />;
    };

    const getRankBadgeColor = (rank: number) => {
        switch (rank) {
            case 1: return 'bg-warning/20 text-warning border-warning/30';
            case 2: return 'bg-slate-400/20 text-slate-300 border-slate-400/30';
            case 3: return 'bg-amber-600/20 text-amber-400 border-amber-600/30';
            default: return 'bg-muted text-muted-foreground border-border';
        }
    };

    const getScoreColor = (value: number, max: number = 100) => {
        const ratio = value / max;
        if (ratio >= 0.85) return 'text-secondary';
        if (ratio >= 0.7) return 'text-primary';
        if (ratio >= 0.5) return 'text-warning';
        return 'text-muted-foreground';
    };

    return (
        <div className={`bento-card ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center gap-2">
                    <Table className="w-4 h-4 text-primary" />
                    <h3 className="font-mono text-sm font-semibold text-foreground">
                        CROSS-BENCHMARK SNAPSHOT
                    </h3>
                </div>
                <div className="flex items-center gap-3">
                    {lastUpdated && (
                        <span className="text-xs font-mono text-muted-foreground">
                            Extracted at {new Date(lastUpdated).toUTCString().split(' ')[4].substring(0, 5)} UTC
                        </span>
                    )}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={fetchLeaderboard}
                        disabled={isLoading}
                        className="h-7 px-2"
                    >
                        <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
                    </Button>
                </div>
            </div>

            {/* Table */}
            <div className="mt-4 overflow-x-auto custom-scrollbar">
                <table className="w-full min-w-[700px]">
                    <thead>
                        <tr className="border-b border-border">
                            {METRIC_COLUMNS.map((col) => (
                                <th
                                    key={col.key}
                                    onClick={() => sortBy(col.key)}
                                    className="px-3 py-3 text-left cursor-pointer hover:bg-muted/30 transition-colors"
                                    title={col.tooltip}
                                >
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs font-mono font-semibold text-muted-foreground uppercase">
                                            {col.label}
                                        </span>
                                        {getSortIcon(col.key)}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {isLoading && entries.length === 0 ? (
                            // Loading skeleton
                            [...Array(5)].map((_, i) => (
                                <tr key={i} className="border-b border-border/50">
                                    {METRIC_COLUMNS.map((col) => (
                                        <td key={col.key} className="px-3 py-3">
                                            <div className="h-5 bg-muted/50 rounded animate-pulse" />
                                        </td>
                                    ))}
                                </tr>
                            ))
                        ) : (
                            entries.map((entry, idx) => (
                                <tr
                                    key={`${entry.model}-${idx}`}
                                    className="border-b border-border/30 hover:bg-muted/20 transition-colors group"
                                >
                                    {/* Rank */}
                                    <td className="px-3 py-3">
                                        <span className={`
                      inline-flex items-center justify-center w-7 h-7 rounded-full
                      font-mono font-bold text-sm border
                      ${getRankBadgeColor(entry.rank)}
                    `}>
                                            {entry.rank}
                                        </span>
                                    </td>

                                    {/* Model */}
                                    <td className="px-3 py-3">
                                        <div className="flex items-center gap-2">
                                            <span className="font-mono text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                                                {entry.model}
                                            </span>
                                            <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                        </div>
                                    </td>

                                    {/* Provider */}
                                    <td className="px-3 py-3">
                                        <span className="text-sm text-muted-foreground">
                                            {entry.provider}
                                        </span>
                                    </td>

                                    {/* MMLU */}
                                    <td className="px-3 py-3">
                                        <span className={`font-mono text-sm font-semibold ${getScoreColor(entry.mmlu)}`}>
                                            {entry.mmlu.toFixed(1)}
                                        </span>
                                    </td>

                                    {/* Arena ELO */}
                                    <td className="px-3 py-3">
                                        <span className={`font-mono text-sm font-semibold ${getScoreColor(entry.arena_elo, 1400)}`}>
                                            {entry.arena_elo}
                                        </span>
                                    </td>

                                    {/* HumanEval */}
                                    <td className="px-3 py-3">
                                        <span className={`font-mono text-sm font-semibold ${getScoreColor(entry.humaneval)}`}>
                                            {entry.humaneval.toFixed(1)}
                                        </span>
                                    </td>

                                    {/* Context */}
                                    <td className="px-3 py-3">
                                        <span className="font-mono text-sm text-foreground">
                                            {typeof entry.context === 'number' ? `${(entry.context / 1000).toFixed(0)}k` : '-'}
                                        </span>
                                    </td>

                                    {/* Safety */}
                                    <td className="px-3 py-3">
                                        <span className={`font-mono text-sm font-semibold ${typeof entry.safety === 'number' ? getScoreColor(entry.safety) : ''}`}>
                                            {typeof entry.safety === 'number' ? entry.safety.toFixed(1) : '-'}
                                        </span>
                                    </td>

                                    {/* Average */}
                                    <td className="px-3 py-3">
                                        <div className="flex items-center gap-2">
                                            <span className={`font-mono text-sm font-bold ${getScoreColor(entry.average)}`}>
                                                {entry.average.toFixed(1)}
                                            </span>
                                            {/* Mini progress bar */}
                                            <div className="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-primary to-secondary rounded-full transition-all"
                                                    style={{ width: `${entry.average}%` }}
                                                />
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Source Legend (Phase 1) */}
            <div className="mt-4 pt-4 border-t border-border flex flex-wrap items-center gap-4 text-xs font-mono text-muted-foreground">
                <span>Sources:</span>
                <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-primary" />
                    HuggingFace
                </span>
                <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-secondary" />
                    LMSYS Arena
                </span>
                <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-warning" />
                    Vellum
                </span>
                <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-blue-400" />
                    LiveCodeBench
                </span>
                <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-red-400" />
                    MASK/Vectara
                </span>
            </div>
        </div>
    );
};

export default CrossBenchmarkTable;
