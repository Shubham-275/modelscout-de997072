import { TrendingUp, TrendingDown, Minus, Trophy, Medal } from "lucide-react";
import type { ModelResult, BenchmarkMetrics } from "@/hooks/useModelComparison";

interface ComparisonResultsProps {
    modelAName: string;
    modelBName: string;
    modelAResults: Record<string, ModelResult>;
    modelBResults: Record<string, ModelResult>;
    isLoading: boolean;
}

const METRIC_LABELS: Record<string, string> = {
    mmlu: "MMLU",
    arc_challenge: "ARC-Challenge",
    hellaswag: "HellaSwag",
    truthfulqa: "TruthfulQA",
    winogrande: "WinoGrande",
    gsm8k: "GSM8K",
    arena_elo: "Arena ELO",
    humaneval: "HumanEval",
    mbpp: "MBPP",
    mt_bench: "MT-Bench",
    alpaca_eval: "AlpacaEval",
    average_score: "Average",
};

const SOURCE_LABELS: Record<string, string> = {
    huggingface: "HuggingFace",
    lmsys_arena: "LMSys Arena",
    papers_with_code: "Papers With Code",
};

const ComparisonResults = ({
    modelAName,
    modelBName,
    modelAResults,
    modelBResults,
    isLoading,
}: ComparisonResultsProps) => {
    const sources = [...new Set([...Object.keys(modelAResults), ...Object.keys(modelBResults)])];

    if (sources.length === 0 && !isLoading) {
        return (
            <div className="bento-card flex flex-col items-center justify-center py-12">
                <Trophy className="w-12 h-12 text-muted-foreground/30 mb-4" />
                <p className="text-muted-foreground font-mono text-sm">
                    Select two models to compare
                </p>
            </div>
        );
    }

    // Calculate overall winners
    const calculateWinner = () => {
        let aWins = 0;
        let bWins = 0;

        for (const source of sources) {
            const resultA = modelAResults[source];
            const resultB = modelBResults[source];

            if (resultA && resultB) {
                if ((resultA.average_score || 0) > (resultB.average_score || 0)) {
                    aWins++;
                } else if ((resultB.average_score || 0) > (resultA.average_score || 0)) {
                    bWins++;
                }
            }
        }

        return { aWins, bWins, winner: aWins > bWins ? 'A' : bWins > aWins ? 'B' : 'tie' };
    };

    const { aWins, bWins, winner } = calculateWinner();

    return (
        <div className="bento-card overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center gap-2">
                    <Trophy className="w-4 h-4 text-warning" />
                    <h3 className="font-mono text-sm font-semibold text-foreground">
                        COMPARISON RESULTS
                    </h3>
                </div>
                {sources.length > 0 && (
                    <div className="flex items-center gap-2">
                        <span className={`text-xs font-mono ${winner === 'A' ? 'text-secondary' : 'text-muted-foreground'}`}>
                            {modelAName.split('/').pop()}: {aWins}
                        </span>
                        <span className="text-xs font-mono text-muted-foreground">vs</span>
                        <span className={`text-xs font-mono ${winner === 'B' ? 'text-secondary' : 'text-muted-foreground'}`}>
                            {modelBName.split('/').pop()}: {bWins}
                        </span>
                    </div>
                )}
            </div>

            {/* Loading State */}
            {isLoading && sources.length === 0 && (
                <div className="py-12 flex flex-col items-center justify-center">
                    <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full mb-4" />
                    <p className="text-muted-foreground font-mono text-sm">
                        Fetching benchmark data...
                    </p>
                </div>
            )}

            {/* Results Grid */}
            <div className="mt-4 space-y-6">
                {sources.map((source) => {
                    const resultA = modelAResults[source];
                    const resultB = modelBResults[source];

                    if (!resultA && !resultB) return null;

                    // Combine all metrics from both models
                    const allMetrics = new Set<string>();
                    if (resultA?.average_score) allMetrics.add('average_score');
                    if (resultB?.average_score) allMetrics.add('average_score');

                    Object.keys(resultA?.benchmark_metrics || {}).forEach(m => allMetrics.add(m));
                    Object.keys(resultB?.benchmark_metrics || {}).forEach(m => allMetrics.add(m));

                    return (
                        <div key={source} className="bg-muted/20 rounded-lg p-4">
                            {/* Source Header */}
                            <div className="flex items-center justify-between mb-4">
                                <span className="text-xs font-mono font-semibold text-primary uppercase">
                                    {SOURCE_LABELS[source] || source}
                                </span>
                                <div className="flex gap-4 text-xs font-mono text-muted-foreground">
                                    <span className="w-24 text-center">{modelAName.split('/').pop()}</span>
                                    <span className="w-16 text-center">Delta</span>
                                    <span className="w-24 text-center">{modelBName.split('/').pop()}</span>
                                </div>
                            </div>

                            {/* Metrics Rows */}
                            <div className="space-y-2">
                                {Array.from(allMetrics).map((metric) => {
                                    const valA = metric === 'average_score'
                                        ? resultA?.average_score
                                        : resultA?.benchmark_metrics?.[metric];
                                    const valB = metric === 'average_score'
                                        ? resultB?.average_score
                                        : resultB?.benchmark_metrics?.[metric];

                                    const delta = (valA || 0) - (valB || 0);
                                    const isAWinner = delta > 0;
                                    const isBWinner = delta < 0;

                                    return (
                                        <div
                                            key={metric}
                                            className="flex items-center justify-between py-2 px-3 rounded bg-background/50"
                                        >
                                            <span className="text-sm font-mono text-foreground">
                                                {METRIC_LABELS[metric] || metric}
                                            </span>

                                            <div className="flex gap-4 items-center">
                                                {/* Model A Value */}
                                                <span className={`
                          w-24 text-center font-mono text-sm font-semibold
                          ${isAWinner ? 'text-secondary' : 'text-foreground'}
                        `}>
                                                    {valA?.toFixed(1) ?? '—'}
                                                    {isAWinner && <Medal className="inline w-3 h-3 ml-1 text-secondary" />}
                                                </span>

                                                {/* Delta */}
                                                <span className={`
                          w-16 text-center font-mono text-xs flex items-center justify-center gap-1
                          ${delta > 0 ? 'text-secondary' : delta < 0 ? 'text-destructive' : 'text-muted-foreground'}
                        `}>
                                                    {delta > 0 ? (
                                                        <TrendingUp className="w-3 h-3" />
                                                    ) : delta < 0 ? (
                                                        <TrendingDown className="w-3 h-3" />
                                                    ) : (
                                                        <Minus className="w-3 h-3" />
                                                    )}
                                                    {delta !== 0 ? `${delta > 0 ? '+' : ''}${delta.toFixed(1)}` : '0.0'}
                                                </span>

                                                {/* Model B Value */}
                                                <span className={`
                          w-24 text-center font-mono text-sm font-semibold
                          ${isBWinner ? 'text-secondary' : 'text-foreground'}
                        `}>
                                                    {valB?.toFixed(1) ?? '—'}
                                                    {isBWinner && <Medal className="inline w-3 h-3 ml-1 text-secondary" />}
                                                </span>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Legend */}
            {sources.length > 0 && (
                <div className="mt-4 pt-4 border-t border-border flex items-center justify-center gap-6 text-xs font-mono text-muted-foreground">
                    <span className="flex items-center gap-1">
                        <TrendingUp className="w-3 h-3 text-secondary" />
                        Model A leads
                    </span>
                    <span className="flex items-center gap-1">
                        <TrendingDown className="w-3 h-3 text-destructive" />
                        Model B leads
                    </span>
                    <span className="flex items-center gap-1">
                        <Medal className="w-3 h-3 text-secondary" />
                        Winner
                    </span>
                </div>
            )}
        </div>
    );
};

export default ComparisonResults;
