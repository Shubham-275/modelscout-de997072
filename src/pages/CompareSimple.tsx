/**
 * MODEL SCOUT - COMPARISON ARENA
 * 
 * High-impact, visual comparison for AI models.
 */

import { useState } from "react";
import { ArrowLeft, Check, X, ChevronDown, Trophy, Zap, DollarSign, Brain, Shield } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import DashboardHeader from "@/components/DashboardHeader";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://modelscout-production.up.railway.app';

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

    const models = [
        "gpt-4o", "gpt-4o-mini", "claude-3.5-sonnet",
        "gemini-1.5-pro", "gemini-1.5-flash",
        "llama-3-70b-instruct", "deepseek-v3"
    ];

    const handleCompare = async () => {
        if (modelA === modelB) {
            setError("Please select two different models to compare.");
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/api/v2/analyst/compare`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_a: modelA, model_b: modelB }),
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            setComparison(data.comparison);
        } catch (err) {
            setError("Comparison failed. Please try again.");
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const formatModelName = (id: string) => id.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

    // Helper to determine the "Winner" for cost visualization
    const getCostStats = (id: string) => {
        if (!comparison) return { total: 0, pct: 0, isCheaper: false };
        const costData = comparison.cost_comparison[id] as { total_per_1m: number } | undefined;
        const total = costData?.total_per_1m || 0;
        const isCheaper = comparison.cost_comparison.cheaper_model === id;
        return { total, isCheaper };
    };

    return (
        <div className="min-h-screen bg-[#0A0A0B] text-foreground grid-pattern font-sans selection:bg-primary/30">
            <DashboardHeader />

            <main className="container mx-auto px-4 py-8 max-w-7xl">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-8">
                    <div className="flex items-center gap-4 w-full md:w-auto">
                        <Link to="/">
                            <Button variant="ghost" size="icon" className="hover:bg-primary/10 hover:text-primary rounded-full">
                                <ArrowLeft className="w-5 h-5" />
                            </Button>
                        </Link>
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                                Comparison Arena
                            </h1>
                            <p className="text-muted-foreground text-sm">Head-to-head AI model analysis</p>
                        </div>
                    </div>
                </div>

                {/* Selection Card */}
                <Card className="p-6 mb-10 border-white/10 bg-white/5 backdrop-blur-md shadow-2xl relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-primary/5 pointer-events-none" />

                    <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr] gap-6 items-end relative z-10">
                        {/* Model A Selector */}
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-primary/80 uppercase tracking-widest pl-1">Challenger A</label>
                            <div className="relative group">
                                <select
                                    value={modelA}
                                    onChange={(e) => setModelA(e.target.value)}
                                    className="w-full h-14 pl-4 pr-10 bg-black/40 border border-white/10 rounded-xl appearance-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all font-mono text-lg hover:bg-black/60 cursor-pointer"
                                >
                                    {models.map(m => <option key={m} value={m}>{formatModelName(m)}</option>)}
                                </select>
                                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground pointer-events-none group-hover:text-primary transition-colors" />
                            </div>
                        </div>

                        {/* VS Badge */}
                        <div className="flex items-center justify-center pb-2">
                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-cyan-600 flex items-center justify-center shadow-[0_0_20px_rgba(6,182,212,0.5)] border-4 border-[#0A0A0B] z-10">
                                <span className="font-black text-white text-sm italic">VS</span>
                            </div>
                        </div>

                        {/* Model B Selector */}
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-cyan-400/80 uppercase tracking-widest pl-1">Challenger B</label>
                            <div className="relative group">
                                <select
                                    value={modelB}
                                    onChange={(e) => setModelB(e.target.value)}
                                    className="w-full h-14 pl-4 pr-10 bg-black/40 border border-white/10 rounded-xl appearance-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all font-mono text-lg hover:bg-black/60 cursor-pointer"
                                >
                                    {models.map(m => <option key={m} value={m}>{formatModelName(m)}</option>)}
                                </select>
                                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground pointer-events-none group-hover:text-cyan-400 transition-colors" />
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 flex justify-center">
                        <Button
                            onClick={handleCompare}
                            disabled={isLoading}
                            className="h-12 px-8 bg-gradient-to-r from-primary to-cyan-600 hover:from-primary/90 hover:to-cyan-600/90 text-white font-bold tracking-wide rounded-full shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] transition-all scale-100 hover:scale-105 active:scale-95 uppercase text-sm"
                        >
                            {isLoading ? (
                                <span className="flex items-center gap-2"><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Analyzing Matchup...</span>
                            ) : (
                                <span className="flex items-center gap-2"><Zap className="w-4 h-4 fill-current" /> Analyze Matchup</span>
                            )}
                        </Button>
                    </div>

                    {error && <p className="text-red-400 text-center mt-4 text-sm font-medium animate-in fade-in">{error}</p>}
                </Card>

                {/* RESULTS ARENA */}
                {comparison && (
                    <div className="space-y-8 animate-in slide-in-from-bottom-10 fade-in duration-700">
                        {/* 1. The Verdict */}
                        <div className="bg-gradient-to-b from-primary/10 to-transparent p-[1px] rounded-2xl">
                            <Card className="bg-[#0A0A0B]/80 backdrop-blur-xl border-none p-8 md:p-10 text-center relative overflow-hidden">
                                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-1 bg-gradient-to-r from-transparent via-primary to-transparent" />
                                <Trophy className="w-12 h-12 text-primary mx-auto mb-4 drop-shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
                                <h2 className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-white to-white/70 mb-4">
                                    The Verdict
                                </h2>
                                <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
                                    {comparison.verdict}
                                </p>
                            </Card>
                        </div>

                        {/* 2. Head-to-Head Grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {/* Left Corner: Model A */}
                            <div className="space-y-6">
                                <div className="flex items-center gap-4 mb-2">
                                    <div className="h-10 w-1 bg-primary rounded-full" />
                                    <div>
                                        <h3 className="text-2xl font-bold text-white">{formatModelName(comparison.models_compared.model_a)}</h3>
                                        <Badge variant="outline" className="border-primary/20 text-primary bg-primary/5">Challenger A</Badge>
                                    </div>
                                </div>
                                <ComparisonCard
                                    modelId={comparison.models_compared.model_a}
                                    comparison={comparison}
                                    color="primary"
                                />
                            </div>

                            {/* Right Corner: Model B */}
                            <div className="space-y-6">
                                <div className="flex items-center gap-4 mb-2 lg:flex-row-reverse text-right">
                                    <div className="h-10 w-1 bg-cyan-400 rounded-full" />
                                    <div>
                                        <h3 className="text-2xl font-bold text-white">{formatModelName(comparison.models_compared.model_b)}</h3>
                                        <Badge variant="outline" className="border-cyan-400/20 text-cyan-400 bg-cyan-400/5">Challenger B</Badge>
                                    </div>
                                </div>
                                <ComparisonCard
                                    modelId={comparison.models_compared.model_b}
                                    comparison={comparison}
                                    color="cyan"
                                    align="right"
                                />
                            </div>
                        </div>

                        {/* 3. Cost Showdown */}
                        <Card className="p-8 border-white/5 bg-white/5 backdrop-blur-md">
                            <h3 className="text-lg font-bold flex items-center gap-2 mb-8">
                                <DollarSign className="w-5 h-5 text-green-400" />
                                <span className="bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">Cost Efficiency Showdown</span>
                            </h3>

                            <div className="space-y-8">
                                <CostBar
                                    modelName={formatModelName(comparison.models_compared.model_a)}
                                    stats={getCostStats(comparison.models_compared.model_a)}
                                    max={Math.max(getCostStats(comparison.models_compared.model_a).total, getCostStats(comparison.models_compared.model_b).total)}
                                    color="bg-primary"
                                />
                                <CostBar
                                    modelName={formatModelName(comparison.models_compared.model_b)}
                                    stats={getCostStats(comparison.models_compared.model_b)}
                                    max={Math.max(getCostStats(comparison.models_compared.model_a).total, getCostStats(comparison.models_compared.model_b).total)}
                                    color="bg-cyan-500"
                                />
                            </div>
                        </Card>

                        {/* 4. Tradeoffs */}
                        <Card className="p-6 md:p-8 border-white/10 bg-black/40">
                            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-6 flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-yellow-500" />
                                Critical Tradeoffs
                            </h3>
                            <div className="grid gap-4">
                                {comparison.key_tradeoffs.map((tradeoff, i) => (
                                    <div key={i} className="flex gap-4 items-start p-4 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                                        <div className="mt-1 min-w-[24px] h-6 flex items-center justify-center rounded bg-yellow-500/10 text-yellow-500 font-mono text-sm">
                                            {i + 1}
                                        </div>
                                        <p className="text-base text-gray-300 leading-relaxed">{tradeoff}</p>
                                    </div>
                                ))}
                            </div>
                        </Card>
                    </div>
                )}
            </main>
        </div>
    );
};

// Sub-components for cleanliness

const ComparisonCard = ({ modelId, comparison, color, align = 'left' }: { modelId: string, comparison: ComparisonResult, color: 'primary' | 'cyan', align?: 'left' | 'right' }) => {
    const isPrimary = color === 'primary';
    const accentColor = isPrimary ? 'text-primary' : 'text-cyan-400';
    const borderColor = isPrimary ? 'border-primary/20' : 'border-cyan-400/20';
    const strengths = comparison.strengths[modelId] || [];
    const useCases = comparison.choose_if[modelId] || [];

    return (
        <Card className={`h-full bg-card/30 backdrop-blur-sm border ${borderColor} overflow-hidden flex flex-col`}>
            {/* Strengths Section */}
            <div className="p-6 flex-grow">
                <div className={`flex items-center gap-2 mb-4 ${align === 'right' ? 'flex-row-reverse' : ''}`}>
                    <Brain className={`w-4 h-4 ${accentColor}`} />
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Superpowers</span>
                </div>
                <ul className="space-y-3">
                    {strengths.map((s, i) => (
                        <li key={i} className={`flex gap-3 text-sm text-gray-300 ${align === 'right' ? 'flex-row-reverse text-right' : ''}`}>
                            <div className={`mt-1 min-w-[6px] h-1.5 rounded-full ${isPrimary ? 'bg-primary' : 'bg-cyan-400'}`} />
                            {s}
                        </li>
                    ))}
                </ul>
            </div>

            {/* Use Cases Section */}
            <div className="bg-white/5 p-6 border-t border-white/5">
                <div className={`flex items-center gap-2 mb-4 ${align === 'right' ? 'flex-row-reverse' : ''}`}>
                    <Shield className={`w-4 h-4 ${accentColor}`} />
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Best For</span>
                </div>
                <div className={`flex flex-wrap gap-2 ${align === 'right' ? 'justify-end' : ''}`}>
                    {useCases.map((u, i) => (
                        <Badge key={i} variant="secondary" className="bg-white/10 hover:bg-white/20 text-gray-200 border-none px-3 py-1.5 font-normal">
                            {u}
                        </Badge>
                    ))}
                </div>
            </div>
        </Card>
    );
};

const CostBar = ({ modelName, stats, max, color }: { modelName: string, stats: { total: number, isCheaper: boolean }, max: number, color: string }) => {
    // Determine bar width percentage
    const percentage = max > 0 ? (stats.total / max) * 100 : 0;

    return (
        <div>
            <div className="flex justify-between items-end mb-2">
                <div>
                    <span className="text-base font-medium text-white mr-2">{modelName}</span>
                    {stats.isCheaper && (
                        <Badge className="bg-green-500/20 text-green-400 hover:bg-green-500/30 border-none uppercase text-[10px] tracking-wide">
                            Best Value
                        </Badge>
                    )}
                </div>
                <div className="text-right">
                    <span className="text-2xl font-mono font-bold text-white">${stats.total.toFixed(2)}</span>
                    <span className="text-muted-foreground text-xs ml-1">/ 1M tokens</span>
                </div>
            </div>
            <div className="h-3 w-full bg-white/10 rounded-full overflow-hidden relative">
                <div
                    className={`h-full ${color} rounded-full transition-all duration-1000 ease-out`}
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
};

export default ComparePage;
