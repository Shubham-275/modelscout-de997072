import { useState } from "react";
import { GitCompare, Search, ArrowRight, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface ModelComparisonSelectorProps {
    onCompare: (modelA: string, modelB: string) => void;
    isLoading: boolean;
    onCancel?: () => void;
}

const POPULAR_MODELS = [
    "GPT-4o",
    "Claude 3.5 Sonnet",
    "Gemini 1.5 Pro",
    "Llama-3-70B-Instruct",
    "DeepSeek-V2-Chat",
    "Qwen2-72B-Instruct",
    "Mistral-Large-2",
    "Command R+",
];

const ModelComparisonSelector = ({
    onCompare,
    isLoading,
    onCancel
}: ModelComparisonSelectorProps) => {
    const [modelA, setModelA] = useState("");
    const [modelB, setModelB] = useState("");
    const [showSuggestions, setShowSuggestions] = useState<"A" | "B" | null>(null);

    const handleCompare = () => {
        if (modelA.trim() && modelB.trim()) {
            onCompare(modelA.trim(), modelB.trim());
        }
    };

    const filteredSuggestions = (query: string) => {
        if (!query) return POPULAR_MODELS;
        return POPULAR_MODELS.filter(m =>
            m.toLowerCase().includes(query.toLowerCase())
        );
    };

    const handleSelectSuggestion = (model: string, target: "A" | "B") => {
        if (target === "A") {
            setModelA(model);
        } else {
            setModelB(model);
        }
        setShowSuggestions(null);
    };

    const handleSwap = () => {
        const temp = modelA;
        setModelA(modelB);
        setModelB(temp);
    };

    return (
        <div className="bento-card">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center gap-2">
                    <GitCompare className="w-4 h-4 text-primary" />
                    <h3 className="font-mono text-sm font-semibold text-foreground">
                        MODEL COMPARISON
                    </h3>
                </div>
                <span className="text-xs font-mono text-muted-foreground">
                    SIDE-BY-SIDE ANALYSIS
                </span>
            </div>

            {/* Comparison Inputs */}
            <div className="mt-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-[1fr,auto,1fr] gap-4 items-center">
                    {/* Model A Input */}
                    <div className="relative">
                        <label className="block text-xs font-mono text-muted-foreground mb-2">
                            MODEL A
                        </label>
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <Input
                                type="text"
                                placeholder="e.g., GPT-4o"
                                value={modelA}
                                onChange={(e) => setModelA(e.target.value)}
                                onFocus={() => setShowSuggestions("A")}
                                onBlur={() => setTimeout(() => setShowSuggestions(null), 200)}
                                className="pl-10 bg-muted/50 border-border focus:border-primary font-mono"
                                disabled={isLoading}
                            />
                            {showSuggestions === "A" && (
                                <div className="absolute z-10 w-full mt-1 bg-card border border-border rounded-lg shadow-lg overflow-hidden">
                                    {filteredSuggestions(modelA).slice(0, 5).map((model) => (
                                        <button
                                            key={model}
                                            onClick={() => handleSelectSuggestion(model, "A")}
                                            className="w-full px-4 py-2 text-left text-sm font-mono hover:bg-muted/50 transition-colors"
                                        >
                                            {model}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* VS / Swap Button */}
                    <div className="flex justify-center">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleSwap}
                            className="rounded-full w-10 h-10 p-0 hover:bg-primary/10"
                            disabled={isLoading}
                        >
                            <ArrowRight className="w-4 h-4 text-primary rotate-90 md:rotate-0" />
                        </Button>
                    </div>

                    {/* Model B Input */}
                    <div className="relative">
                        <label className="block text-xs font-mono text-muted-foreground mb-2">
                            MODEL B
                        </label>
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <Input
                                type="text"
                                placeholder="e.g., Claude 3.5 Sonnet"
                                value={modelB}
                                onChange={(e) => setModelB(e.target.value)}
                                onFocus={() => setShowSuggestions("B")}
                                onBlur={() => setTimeout(() => setShowSuggestions(null), 200)}
                                className="pl-10 bg-muted/50 border-border focus:border-primary font-mono"
                                disabled={isLoading}
                            />
                            {showSuggestions === "B" && (
                                <div className="absolute z-10 w-full mt-1 bg-card border border-border rounded-lg shadow-lg overflow-hidden">
                                    {filteredSuggestions(modelB).slice(0, 5).map((model) => (
                                        <button
                                            key={model}
                                            onClick={() => handleSelectSuggestion(model, "B")}
                                            className="w-full px-4 py-2 text-left text-sm font-mono hover:bg-muted/50 transition-colors"
                                        >
                                            {model}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-center gap-3 pt-2">
                    <Button
                        onClick={handleCompare}
                        disabled={!modelA.trim() || !modelB.trim() || isLoading}
                        className="bg-primary hover:bg-primary/90 text-primary-foreground font-mono px-6"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Comparing...
                            </>
                        ) : (
                            <>
                                <GitCompare className="w-4 h-4 mr-2" />
                                Compare Models
                            </>
                        )}
                    </Button>

                    {isLoading && onCancel && (
                        <Button
                            variant="outline"
                            onClick={onCancel}
                            className="font-mono"
                        >
                            <X className="w-4 h-4 mr-2" />
                            Cancel
                        </Button>
                    )}
                </div>
            </div>

            {/* Quick Select */}
            <div className="mt-6 pt-4 border-t border-border">
                <label className="block text-xs font-mono text-muted-foreground mb-3">
                    QUICK SELECT
                </label>
                <div className="flex flex-wrap gap-2">
                    {POPULAR_MODELS.slice(0, 6).map((model) => (
                        <button
                            key={model}
                            onClick={() => {
                                if (!modelA) {
                                    setModelA(model);
                                } else if (!modelB && modelA !== model) {
                                    setModelB(model);
                                }
                            }}
                            disabled={isLoading}
                            className={`
                px-3 py-1.5 rounded-full text-xs font-mono
                border border-border hover:border-primary/50
                transition-all duration-200
                ${modelA === model || modelB === model
                                    ? 'bg-primary/20 border-primary text-primary'
                                    : 'bg-muted/30 text-muted-foreground hover:text-foreground'
                                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
                        >
                            {model}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ModelComparisonSelector;
