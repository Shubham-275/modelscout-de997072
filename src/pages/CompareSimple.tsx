/**
 * MODEL SCOUT - COMPARE PAGE (PHASE 2)
 * 
 * DESIGN PRINCIPLE: Vertical comparison, plain-English verdict
 * 
 * Structure:
 * - Side-by-side model columns
 * - Strengths/Weaknesses (not raw scores)
 * - "Choose Model A if... Choose Model B if..."
 * 
 * Cognitive Load: Max 5 visible sections
 */

import { useState } from "react";
import { ArrowLeft, Check, X, ChevronDown } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import DashboardHeader from "@/components/DashboardHeader";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface ModelInfo {
    id: string;
    provider: string;
    strengths: string[];
    weaknesses: string[];
}

interface ComparisonResult {
    models_compared: {
        model_a: string;
        model_b: string;
    };
    verdict: string;
    strengths: Record<string, string[]>;
    key_tradeoffs: string[];
    choose_if: Record<string, string[]>;
    benchmark_deltas: Record<string, any>;
    cost_comparison: {
        cheaper_model: string;
        cost_difference_pct: number;
        // Allow dynamic model keys with cost data
        [key: string]: {
            input_per_1m: number;
            output_per_1m: number;
            total_per_1m: number;
        } | string | number;
    };
    data_freshness: string;
}

const ComparePage = () => {
    const [modelA, setModelA] = useState<string>("gpt-4o");
    const [modelB, setModelB] = useState<string>("claude-3.5-sonnet");
    const [isLoading, setIsLoading] = useState(false);
    const [comparison, setComparison] = useState<ComparisonResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Available models (from analyst)
    const models = [
        "gpt-4o",
        "gpt-4o-mini",
        "claude-3.5-sonnet",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "llama-3-70b-instruct",
        "deepseek-v3",
    ];

    const handleCompare = async () => {
        if (modelA === modelB) {
            setError("Please select two different models");
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/api/v2/analyst/compare`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model_a: modelA,
                    model_b: modelB,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            setComparison(data.comparison);
        } catch (err) {
            setError("Failed to compare models. Please try again.");
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const formatModelName = (modelId: string) => {
        return modelId
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    const getCost = (modelId: string) => {
        if (!comparison) return { total_per_1m: 0 };
        const cost = comparison.cost_comparison[modelId];
        // Type guard to ensure it's the cost object and not the other properties
        if (typeof cost === 'object' && cost !== null && 'total_per_1m' in cost) {
            return cost as { total_per_1m: number }; // Cast for safety
        }
        return { total_per_1m: 0 };
    };

    return (
        <div className="min-h-screen bg-background grid-pattern">
            <DashboardHeader />

            <main className="container mx-auto px-4 py-8 max-w-6xl">
                <div className="flex items-center gap-4 mb-8">
                    <Link to="/">
                        <Button variant="ghost" size="sm" className="hover:bg-primary/10 hover:text-primary transition-colors">
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Back
                        </Button>
                    </Link>
                    <h1 className="text-2xl font-bold tracking-tight">Compare Two Models</h1>
                </div>

                {/* Section 1: Model Selection */}
                <Card className="p-8 mb-8 border border-primary/20 bg-card/50 backdrop-blur-sm shadow-[0_0_15px_rgba(0,0,0,0.5)]">
                    <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
                        <span className="w-1.5 h-6 bg-primary rounded-full" />
                        Select Models to Compare
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        <div>
                            <label className="text-sm font-medium mb-2 block text-muted-foreground">Model A</label>
                            <div className="relative">
                                <select
                                    value={modelA}
                                    onChange={(e) => setModelA(e.target.value)}
                                    className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all font-mono text-sm cursor-pointer hover:bg-background/80"
                                >
                                    {models.map((model) => (
                                        <option key={model} value={model}>
                                            {formatModelName(model)}
                                        </option>
                                    ))}
                                </select>
                                <ChevronDown className="absolute right-3 top-3.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                            </div>
                        </div>

                        <div>
                            <label className="text-sm font-medium mb-2 block text-muted-foreground">Model B</label>
                            <div className="relative">
                                <select
                                    value={modelB}
                                    onChange={(e) => setModelB(e.target.value)}
                                    className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all font-mono text-sm cursor-pointer hover:bg-background/80"
                                >
                                    {models.map((model) => (
                                        <option key={model} value={model}>
                                            {formatModelName(model)}
                                        </option>
                                    ))}
                                </select>
                                <ChevronDown className="absolute right-3 top-3.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                            </div>
                        </div>
                    </div>

                    <Button
                        onClick={handleCompare}
                        disabled={isLoading}
                        className="w-full font-bold h-12 bg-primary hover:bg-primary/90 shadow-[0_0_15px_rgba(6,182,212,0.2)] hover:shadow-[0_0_25px_rgba(6,182,212,0.4)] transition-all uppercase tracking-wider"
                    >
                        {isLoading ? "Comparing..." : "Compare Models"}
                    </Button>

                    {error && (
                        <p className="text-sm text-destructive mt-4 text-center">{error}</p>
                    )}
                </Card>

                {/* Section 2: Comparison Results */}
                {comparison && (
                    <div className="space-y-6 animate-in slide-in-from-bottom-8 duration-500">
                        {/* Verdict - Plain English */}
                        <Card className="p-6 bg-secondary/5 border border-secondary/20 shadow-[0_0_20px_rgba(16,185,129,0.1)]">
                            <h2 className="text-xs font-semibold mb-3 uppercase tracking-wider text-muted-foreground">Verdict</h2>
                            <p className="text-lg md:text-xl leading-relaxed font-medium">
                                {comparison.verdict}
                            </p>
                            <p className="text-xs text-muted-foreground mt-4 pt-4 border-t border-border/30 font-mono">
                                {comparison.data_freshness}
                            </p>
                        </Card>

                        {/* Side-by-Side Comparison */}
                        <div className="grid md:grid-cols-2 gap-6">
                            {/* Model A Column */}
                            <Card className="p-6 bg-card/40 backdrop-blur-sm border border-border/50 flex flex-col h-full hover:border-primary/30 transition-colors">
                                <div className="mb-6 border-b border-border/50 pb-4">
                                    <h3 className="text-2xl font-bold mb-1 text-primary">
                                        {formatModelName(comparison.models_compared.model_a)}
                                    </h3>
                                    <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest">Model A</p>
                                </div>

                                {/* Strengths */}
                                <div className="mb-6 flex-grow">
                                    <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 uppercase tracking-wide text-xs text-muted-foreground">
                                        <Check className="w-4 h-4 text-green-500" />
                                        Strengths
                                    </h4>
                                    <ul className="space-y-2">
                                        {comparison.strengths[comparison.models_compared.model_a]?.map((strength, idx) => (
                                            <li key={idx} className="text-sm text-foreground/90 pl-6 relative">
                                                <span className="absolute left-0 top-1.5 w-1.5 h-1.5 rounded-full bg-green-500/50"></span>
                                                {strength}
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                {/* Weaknesses */}
                                <div className="mb-6">
                                    <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 uppercase tracking-wide text-xs text-muted-foreground">
                                        <X className="w-4 h-4 text-destructive" />
                                        Weaknesses
                                    </h4>
                                    <ul className="space-y-2">
                                        {comparison.strengths[comparison.models_compared.model_b]?.slice(0, 2).map((_, idx) => (
                                            <li key={idx} className="text-sm text-muted-foreground pl-6 relative italic">
                                                <span className="absolute left-0 top-1.5 w-1.5 h-1.5 rounded-full bg-destructive/30"></span>
                                                Lacks Model B benefits
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                {/* Cost */}
                                <div className="bg-background/50 rounded-lg p-4 mb-6 border border-border/30">
                                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Cost per 1M tokens (Total)</p>
                                    <p className="font-mono text-xl font-bold">
                                        ${getCost(comparison.models_compared.model_a).total_per_1m.toFixed(2)}
                                    </p>
                                    {comparison.cost_comparison.cheaper_model === comparison.models_compared.model_a && (
                                        <p className="text-xs text-green-400 mt-1 font-medium bg-green-500/10 inline-block px-2 py-0.5 rounded border border-green-500/20">
                                            {comparison.cost_comparison.cost_difference_pct.toFixed(0)}% cheaper
                                        </p>
                                    )}
                                </div>

                                {/* Choose If */}
                                <div className="mt-auto pt-4 border-t border-border/50">
                                    <h4 className="text-sm font-bold mb-3">Choose this if:</h4>
                                    <ul className="space-y-2">
                                        {comparison.choose_if[comparison.models_compared.model_a]?.map((reason, idx) => (
                                            <li key={idx} className="text-xs text-muted-foreground flex items-start gap-2">
                                                <span className="text-primary mt-0.5">✓</span>
                                                {reason}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </Card>

                            {/* Model B Column */}
                            <Card className="p-6 bg-card/40 backdrop-blur-sm border border-border/50 flex flex-col h-full hover:border-primary/30 transition-colors">
                                <div className="mb-6 border-b border-border/50 pb-4">
                                    <h3 className="text-2xl font-bold mb-1 text-primary">
                                        {formatModelName(comparison.models_compared.model_b)}
                                    </h3>
                                    <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest">Model B</p>
                                </div>

                                {/* Strengths */}
                                <div className="mb-6 flex-grow">
                                    <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 uppercase tracking-wide text-xs text-muted-foreground">
                                        <Check className="w-4 h-4 text-green-500" />
                                        Strengths
                                    </h4>
                                    <ul className="space-y-2">
                                        {comparison.strengths[comparison.models_compared.model_b]?.map((strength, idx) => (
                                            <li key={idx} className="text-sm text-foreground/90 pl-6 relative">
                                                <span className="absolute left-0 top-1.5 w-1.5 h-1.5 rounded-full bg-green-500/50"></span>
                                                {strength}
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                {/* Weaknesses */}
                                <div className="mb-6">
                                    <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 uppercase tracking-wide text-xs text-muted-foreground">
                                        <X className="w-4 h-4 text-destructive" />
                                        Weaknesses
                                    </h4>
                                    <ul className="space-y-2">
                                        {comparison.strengths[comparison.models_compared.model_a]?.slice(0, 2).map((_, idx) => (
                                            <li key={idx} className="text-sm text-muted-foreground pl-6 relative italic">
                                                <span className="absolute left-0 top-1.5 w-1.5 h-1.5 rounded-full bg-destructive/30"></span>
                                                Lacks Model A benefits
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                {/* Cost */}
                                <div className="bg-background/50 rounded-lg p-4 mb-6 border border-border/30">
                                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Cost per 1M tokens (Total)</p>
                                    <p className="font-mono text-xl font-bold">
                                        ${getCost(comparison.models_compared.model_b).total_per_1m.toFixed(2)}
                                    </p>
                                    {comparison.cost_comparison.cheaper_model === comparison.models_compared.model_b && (
                                        <p className="text-xs text-green-400 mt-1 font-medium bg-green-500/10 inline-block px-2 py-0.5 rounded border border-green-500/20">
                                            {comparison.cost_comparison.cost_difference_pct.toFixed(0)}% cheaper
                                        </p>
                                    )}
                                </div>

                                {/* Choose If */}
                                <div className="mt-auto pt-4 border-t border-border/50">
                                    <h4 className="text-sm font-bold mb-3">Choose this if:</h4>
                                    <ul className="space-y-2">
                                        {comparison.choose_if[comparison.models_compared.model_b]?.map((reason, idx) => (
                                            <li key={idx} className="text-xs text-muted-foreground flex items-start gap-2">
                                                <span className="text-primary mt-0.5">✓</span>
                                                {reason}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </Card>
                        </div>

                        {/* Key Tradeoffs */}
                        {comparison.key_tradeoffs && comparison.key_tradeoffs.length > 0 && (
                            <Card className="p-6 border border-border/50 bg-card/30">
                                <h3 className="text-sm font-semibold mb-4 uppercase tracking-wider text-muted-foreground">Key Tradeoffs</h3>
                                <ul className="space-y-3">
                                    {comparison.key_tradeoffs.map((tradeoff, idx) => (
                                        <li key={idx} className="text-sm text-foreground/80 flex items-start gap-3 bg-background/30 p-3 rounded border border-border/30">
                                            <span className="text-primary mt-0.5 font-bold">→</span>
                                            <span>{tradeoff}</span>
                                        </li>
                                    ))}
                                </ul>
                            </Card>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
};

export default ComparePage;
