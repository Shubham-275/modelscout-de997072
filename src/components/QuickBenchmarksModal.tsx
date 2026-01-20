import { useState } from "react";
import { Zap, X, Trophy, TrendingUp, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

interface QuickBenchmark {
    rank: number;
    model: string;
    provider: string;
    score: number;
    metric: string;
    source: string;
    url: string;
}

const QUICK_BENCHMARKS: QuickBenchmark[] = [
    { rank: 1, model: "GPT-4o", provider: "OpenAI", score: 88.7, metric: "MMLU", source: "HuggingFace", url: "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard" },
    { rank: 1, model: "GPT-4o", provider: "OpenAI", score: 1287, metric: "Arena ELO", source: "LMSYS Arena", url: "https://lmarena.ai/leaderboard" },
    { rank: 1, model: "Claude 3.5 Sonnet", provider: "Anthropic", score: 55.4, metric: "Pass@1", source: "LiveCodeBench", url: "https://livecodebench.github.io/leaderboard.html" },
    { rank: 1, model: "Claude 3.5 Sonnet", provider: "Anthropic", score: 98.2, metric: "Context", source: "Vellum", url: "https://vellum.ai/llm-leaderboard" },
    { rank: 1, model: "Gemini 1.5 Pro", provider: "Google", score: 1.5, metric: "Hallucination %", source: "Vectara", url: "https://github.com/vectara/hallucination-leaderboard" },
    { rank: 2, model: "Llama 3 70B", provider: "Meta", score: 2.1, metric: "Deception", source: "MASK", url: "https://scale.com/leaderboard/mask" },
];

interface QuickBenchmarksModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSelectModel: (model: string) => void;
}

const QuickBenchmarksModal = ({ isOpen, onClose, onSelectModel }: QuickBenchmarksModalProps) => {
    if (!isOpen) return null;

    const handleSelectModel = (model: string) => {
        onSelectModel(model);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-background/80 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative z-10 w-full max-w-2xl mx-4 bento-card max-h-[80vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between pb-4 border-b border-border">
                    <div className="flex items-center gap-2">
                        <Zap className="w-5 h-5 text-warning" />
                        <h2 className="font-mono text-lg font-bold text-foreground">
                            Quick Benchmarks
                        </h2>
                    </div>
                    <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
                        <X className="w-4 h-4" />
                    </Button>
                </div>

                {/* Subtitle */}
                <p className="text-sm text-muted-foreground mt-4 mb-4">
                    Top performing models across key benchmarks. Click a model to search for detailed metrics.
                </p>

                {/* Benchmarks Grid */}
                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {QUICK_BENCHMARKS.map((benchmark, idx) => (
                            <div
                                key={`${benchmark.model}-${benchmark.metric}-${idx}`}
                                className="
                  p-4 rounded-lg bg-muted/20 border border-border
                  hover:border-primary/50 hover:bg-muted/40
                  transition-all duration-200 cursor-pointer group
                "
                                onClick={() => handleSelectModel(benchmark.model)}
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        <span className={`
                      flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold
                      ${benchmark.rank === 1 ? 'bg-warning/20 text-warning' : 'bg-muted text-muted-foreground'}
                    `}>
                                            {benchmark.rank}
                                        </span>
                                        <span className="text-xs font-mono text-primary uppercase">
                                            {benchmark.metric}
                                        </span>
                                    </div>
                                    <span className={`
                    font-mono font-bold text-lg
                    ${benchmark.rank === 1 ? 'text-secondary' : 'text-foreground'}
                  `}>
                                        {benchmark.score.toLocaleString()}
                                    </span>
                                </div>

                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="font-mono text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                                            {benchmark.model}
                                        </p>
                                        <p className="text-xs text-muted-foreground">
                                            {benchmark.provider} • {benchmark.source}
                                        </p>
                                    </div>
                                    <TrendingUp className="w-4 h-4 text-secondary opacity-0 group-hover:opacity-100 transition-opacity" />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Footer */}
                <div className="mt-4 pt-4 border-t border-border flex items-center justify-between">
                    <div className="flex items-center gap-4 text-xs font-mono text-muted-foreground">
                        <span className="flex items-center gap-1">
                            <Trophy className="w-3 h-3 text-warning" />
                            #1 Ranked
                        </span>
                        <span className="flex items-center gap-1">
                            <TrendingUp className="w-3 h-3 text-secondary" />
                            Top Performer
                        </span>
                    </div>
                    <a
                        href="https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs font-mono text-primary hover:underline"
                    >
                        View Full Leaderboard
                        <ExternalLink className="w-3 h-3" />
                    </a>
                </div>
            </div>
        </div>
    );
};

export default QuickBenchmarksModal;
