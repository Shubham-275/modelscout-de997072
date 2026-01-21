/**
 * MODEL SCOUT - HOME PAGE (PHASE 2)
 * Simplified version with basic HTML inputs for reliability
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { GitCompare, Search, BarChart3, ChevronDown, ChevronUp, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import DashboardHeader from "@/components/DashboardHeader";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface UserRequirements {
    use_case: string;
    priorities: {
        cost: string;
        quality: string;
        latency: string;
        context_length: string;
    };
    monthly_budget_usd?: number;
    expected_tokens_per_month?: number;
}

// Enhanced AI-powered recommendation structure (Mino)
interface AIRecommendation {
    recommended_model: string;
    provider: string;
    confidence: string;
    reasoning: string;
    cost_analysis: {
        per_1k_input_tokens: number;
        per_1k_output_tokens: number;
        estimated_monthly_usd: number;
        within_budget: boolean;
    };
    advantages: string[];
    disadvantages: string[];
    similar_models: Array<{
        model: string;
        provider: string;
        why_not: string;
    }>;
    why_better: string;
    use_case_fit: string;
    technical_specs: {
        context_window: number;
        supports_streaming: boolean;
        latency_estimate_ms: number;
    };
    models_analyzed?: number;
}

// Keep old interface for backwards compatibility
interface Recommendation {
    primary_recommendation: {
        model: string;
        provider: string;
        confidence: string;
    };
    reasoning: string;
    why_not_alternatives: Array<{
        model: string;
        reasons: string[];
    }>;
    cost_estimate: {
        monthly_estimate_usd: number;
        assumptions: {
            input_tokens_per_month: number;
            output_tokens_per_month: number;
        };
        within_budget?: boolean;
    };
    caveats: string[];
    data_freshness: string;
}

const Home = () => {
    // Form state
    const [useCase, setUseCase] = useState("");
    const [costPriority, setCostPriority] = useState("medium");
    const [qualityPriority, setQualityPriority] = useState("high");
    const [latencyPriority, setLatencyPriority] = useState("medium");
    const [contextPriority, setContextPriority] = useState("medium");
    const [monthlyBudget, setMonthlyBudget] = useState(100);
    const [usageLevel, setUsageLevel] = useState("medium");

    // Results state
    const [isLoading, setIsLoading] = useState(false);
    const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
    const [aiRecommendation, setAiRecommendation] = useState<AIRecommendation | null>(null);
    const [showAlternatives, setShowAlternatives] = useState(false);
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [showAdvancedMetrics, setShowAdvancedMetrics] = useState(false);
    const [showComparison, setShowComparison] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [useAI, setUseAI] = useState(true); // Use AI by default

    const getTokensFromUsage = (level: string): number => {
        switch (level) {
            case "low": return 1_000_000;
            case "medium": return 5_000_000;
            case "high": return 20_000_000;
            default: return 5_000_000;
        }
    };

    const handleGetRecommendation = async () => {
        if (!useCase.trim()) {
            setError("Please describe your use case");
            return;
        }

        setIsLoading(true);
        setError(null);

        const requirements: UserRequirements = {
            use_case: useCase,
            priorities: {
                cost: costPriority,
                quality: qualityPriority,
                latency: latencyPriority,
                context_length: contextPriority,
            },
            monthly_budget_usd: monthlyBudget,
            expected_tokens_per_month: getTokensFromUsage(usageLevel),
        };

        try {
            // Use AI-powered endpoint
            const endpoint = useAI
                ? `${API_BASE_URL}/api/v2/analyst/recommend/ai`
                : `${API_BASE_URL}/api/v2/analyst/recommend`;

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requirements),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (useAI && data.recommendation) {
                setAiRecommendation(data.recommendation);
                setRecommendation(null);
            } else if (data.recommendation) {
                setRecommendation(data.recommendation);
                setAiRecommendation(null);
            }
        } catch (err) {
            setError("Failed to get recommendation. Please try again.");
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background grid-pattern">
            <DashboardHeader />

            <main className="container mx-auto px-4 py-12 max-w-4xl">
                {/* Section 1: Hero - Clear Value Prop */}
                <section className="text-center mb-12">
                    <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4 tracking-tight">
                        Find the Right <span className="text-primary text-glow-cyber">AI Model</span>
                    </h1>
                    <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                        Get a clear recommendation based on your needs, not just benchmark rankings.
                    </p>
                </section>

                {/* Section 2: Describe Your Needs (Primary Interaction) */}
                <Card className="p-8 mb-12 border border-primary/20 bg-card/50 backdrop-blur-sm shadow-[0_0_15px_rgba(0,0,0,0.5)]">
                    <h2 className="text-xl font-semibold mb-6 flex items-center gap-3">
                        <span className="bg-primary/20 text-primary border border-primary/50 rounded-full w-8 h-8 flex items-center justify-center text-sm font-mono shadow-[0_0_10px_rgba(6,182,212,0.3)]">1</span>
                        Describe Your Needs
                    </h2>

                    <div className="space-y-6">
                        {/* Use Case - Free Text */}
                        <div>
                            <label className="text-sm font-medium mb-2 block text-muted-foreground">
                                What do you want to build? (1-2 lines)
                            </label>
                            <textarea
                                placeholder="e.g., A code assistant for Python developers, or a chatbot for customer support"
                                value={useCase}
                                onChange={(e) => setUseCase(e.target.value)}
                                rows={2}
                                className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground placeholder-muted-foreground/50 resize-none focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all font-mono text-sm"
                            />
                        </div>

                        {/* Priority - Simple Selectors */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="text-sm font-medium mb-2 block text-muted-foreground">Cost Priority</label>
                                <div className="relative">
                                    <select
                                        value={costPriority}
                                        onChange={(e) => setCostPriority(e.target.value)}
                                        className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all font-mono text-sm cursor-pointer hover:bg-background/80"
                                    >
                                        <option value="low">Low (minimize cost)</option>
                                        <option value="medium">Medium (balanced)</option>
                                        <option value="high">High (quality over cost)</option>
                                    </select>
                                    <ChevronDown className="absolute right-3 top-3.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                                </div>
                            </div>

                            <div>
                                <label className="text-sm font-medium mb-2 block text-muted-foreground">Quality Priority</label>
                                <div className="relative">
                                    <select
                                        value={qualityPriority}
                                        onChange={(e) => setQualityPriority(e.target.value)}
                                        className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all font-mono text-sm cursor-pointer hover:bg-background/80"
                                    >
                                        <option value="low">Low (basic)</option>
                                        <option value="medium">Medium (good enough)</option>
                                        <option value="high">High (best available)</option>
                                    </select>
                                    <ChevronDown className="absolute right-3 top-3.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                                </div>
                            </div>
                        </div>

                        {/* Progressive Disclosure - Advanced Options */}
                        <div className="border-t border-border/50 pt-6">
                            <button
                                onClick={() => setShowAdvanced(!showAdvanced)}
                                className="text-sm text-primary hover:text-primary/80 flex items-center gap-2 font-medium transition-colors"
                            >
                                {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                Advanced Settings (Latency & Context)
                            </button>

                            {showAdvanced && (
                                <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6 animate-in slide-in-from-top-2 duration-200">
                                    <div>
                                        <label className="text-sm font-medium mb-2 block text-muted-foreground">Latency Priority</label>
                                        <div className="relative">
                                            <select
                                                value={latencyPriority}
                                                onChange={(e) => setLatencyPriority(e.target.value)}
                                                className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all font-mono text-sm cursor-pointer hover:bg-background/80"
                                            >
                                                <option value="low">Low (fast responses needed)</option>
                                                <option value="medium">Medium (normal)</option>
                                                <option value="high">High (can wait)</option>
                                            </select>
                                            <ChevronDown className="absolute right-3 top-3.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="text-sm font-medium mb-2 block text-muted-foreground">Context Length</label>
                                        <div className="relative">
                                            <select
                                                value={contextPriority}
                                                onChange={(e) => setContextPriority(e.target.value)}
                                                className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all font-mono text-sm cursor-pointer hover:bg-background/80"
                                            >
                                                <option value="short">Short (few pages)</option>
                                                <option value="medium">Medium (documents)</option>
                                                <option value="long">Long (entire books)</option>
                                            </select>
                                            <ChevronDown className="absolute right-3 top-3.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Budget - Slider */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <label className="text-sm font-medium text-muted-foreground">
                                    Monthly Budget
                                </label>
                                <span className="font-mono text-xl text-primary font-bold">
                                    ${monthlyBudget}
                                </span>
                            </div>
                            <input
                                type="range"
                                min="10"
                                max="1000"
                                step="10"
                                value={monthlyBudget}
                                onChange={(e) => setMonthlyBudget(parseInt(e.target.value))}
                                className="w-full h-2 bg-secondary/30 rounded-lg appearance-none cursor-pointer accent-primary"
                            />
                            <p className="text-xs text-muted-foreground">
                                Assuming ~5M tokens/month (adjustable below)
                            </p>
                        </div>

                        {/* Usage Level - Simple Selector */}
                        <div>
                            <label className="text-sm font-medium mb-2 block text-muted-foreground">Expected Usage</label>
                            <div className="relative">
                                <select
                                    value={usageLevel}
                                    onChange={(e) => setUsageLevel(e.target.value)}
                                    className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all font-mono text-sm cursor-pointer hover:bg-background/80"
                                >
                                    <option value="low">Low (testing/hobby - 1M tokens)</option>
                                    <option value="medium">Medium (small app - 5M tokens)</option>
                                    <option value="high">High (production - 20M tokens)</option>
                                </select>
                                <ChevronDown className="absolute right-3 top-3.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                            </div>
                        </div>

                        {/* Single Primary Action */}
                        <Button
                            onClick={handleGetRecommendation}
                            disabled={isLoading}
                            size="lg"
                            className="w-full font-bold text-lg h-14 bg-primary hover:bg-primary/90 shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] transition-all uppercase tracking-wider"
                        >
                            {isLoading ? (
                                <span className="flex items-center gap-2">
                                    <span className="w-2 h-2 bg-background rounded-full animate-bounce" />
                                    Analyzing...
                                </span>
                            ) : "Get Recommendation"}
                        </Button>

                        {error && (
                            <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive text-sm flex items-center gap-2">
                                <span className="font-bold">Error:</span> {error}
                            </div>
                        )}
                    </div>
                </Card>

                {/* Section 3: Recommendation Results (Scannable Hierarchy) */}
                {recommendation && (
                    <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
                        {/* Recommended Model - Headline */}
                        <Card className="p-8 border-2 border-primary bg-card/50 backdrop-blur-md shadow-[0_0_30px_rgba(6,182,212,0.15)] glow-border">
                            <div className="flex flex-col md:flex-row md:items-start justify-between mb-6 gap-4">
                                <div>
                                    <p className="text-sm font-mono text-primary mb-2 flex items-center gap-2">
                                        <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                                        RECOMMENDED MODEL
                                    </p>
                                    <h2 className="text-4xl md:text-5xl font-bold text-foreground tracking-tight text-glow">
                                        {recommendation.primary_recommendation.model}
                                    </h2>
                                    <div className="flex items-center gap-3 mt-3">
                                        <span className="text-sm text-muted-foreground">
                                            by {recommendation.primary_recommendation.provider}
                                        </span>
                                        <span className="px-2 py-0.5 bg-green-500/20 text-green-400 border border-green-500/30 rounded text-xs font-mono uppercase">
                                            {recommendation.primary_recommendation.confidence} confidence
                                        </span>
                                    </div>
                                </div>

                                {/* Cost Badge */}
                                <div className="bg-background/40 backdrop-blur-sm border border-border/50 rounded-xl p-4 min-w-[200px]">
                                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Est. Monthly Cost</h3>
                                    <p className="text-3xl font-mono font-bold text-primary">
                                        ${recommendation.cost_estimate.monthly_estimate_usd.toFixed(2)}
                                    </p>
                                    {recommendation.cost_estimate.within_budget !== undefined && (
                                        <div className={`text-xs mt-2 flex items-center gap-1.5 ${recommendation.cost_estimate.within_budget ? 'text-green-400' : 'text-destructive'}`}>
                                            {recommendation.cost_estimate.within_budget ? <CheckIcon /> : <XIcon />}
                                            {recommendation.cost_estimate.within_budget ? 'Within budget' : 'Exceeds budget'}
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Why it Fits - Max 3 Bullets */}
                            <div className="mb-6 bg-secondary/5 rounded-lg p-5 border border-secondary/20">
                                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2 text-foreground">
                                    <Info className="w-4 h-4 text-primary" />
                                    Why this model fits your needs
                                </h3>
                                <p className="text-muted-foreground leading-relaxed text-sm md:text-base">
                                    {recommendation.reasoning}
                                </p>
                            </div>

                            {/* Caveats - Important Limitations */}
                            {recommendation.caveats && recommendation.caveats.length > 0 && (
                                <div className="mb-4">
                                    <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">Important to know</h3>
                                    <ul className="space-y-2">
                                        {recommendation.caveats.map((caveat, idx) => (
                                            <li key={idx} className="text-sm text-warning/90 flex items-start gap-2 bg-warning/5 p-2 rounded border border-warning/10">
                                                <span className="text-warning mt-0.5">•</span>
                                                <span>{caveat}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Data Freshness - Trust Indicator */}
                            <div className="mt-6 pt-4 border-t border-border/30 flex items-center gap-2 text-xs text-muted-foreground font-mono">
                                <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                                {recommendation.data_freshness}
                            </div>
                        </Card>

                        {/* Alternative Models - Collapsed by Default */}
                        {recommendation.why_not_alternatives && recommendation.why_not_alternatives.length > 0 && (
                            <Card className="border border-border/50 bg-card/30">
                                <button
                                    onClick={() => setShowAlternatives(!showAlternatives)}
                                    className="w-full flex items-center justify-between p-4 text-sm font-semibold hover:bg-white/5 transition-colors"
                                >
                                    <span className="flex items-center gap-2 text-muted-foreground">
                                        Why not other models?
                                    </span>
                                    {showAlternatives ? (
                                        <ChevronUp className="w-4 h-4 text-muted-foreground" />
                                    ) : (
                                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                                    )}
                                </button>

                                {showAlternatives && (
                                    <div className="p-4 pt-0 space-y-3">
                                        {recommendation.why_not_alternatives.map((alt, idx) => (
                                            <div key={idx} className="border-l-2 border-muted pl-4 py-1">
                                                <p className="font-bold text-sm text-foreground">{alt.model}</p>
                                                <ul className="mt-1 space-y-1">
                                                    {alt.reasons.map((reason, ridx) => (
                                                        <li key={ridx} className="text-xs text-muted-foreground">
                                                            • {reason}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </Card>
                        )}
                    </div>
                )}

                {/* AI-Powered Recommendation Results (Enhanced) */}
                {aiRecommendation && (
                    <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
                        {/* AI Badge and Actions */}
                        <div className="flex items-center justify-between flex-wrap gap-4">
                            <div className="flex items-center gap-2 text-xs font-mono text-primary">
                                <span className="px-2 py-1 bg-primary/10 border border-primary/30 rounded">
                                    ✨ Powered by Mino AI
                                </span>
                                <span className="text-muted-foreground">
                                    Analyzed {aiRecommendation.models_analyzed || '30+'} models
                                </span>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => setShowAdvancedMetrics(!showAdvancedMetrics)}
                                    className="px-3 py-1.5 text-xs font-medium bg-secondary/20 hover:bg-secondary/30 border border-secondary/30 rounded-lg transition-colors flex items-center gap-1.5"
                                >
                                    <BarChart3 className="w-3.5 h-3.5" />
                                    {showAdvancedMetrics ? 'Hide' : 'Show'} Advanced Metrics
                                </button>
                                <button
                                    onClick={() => setShowComparison(!showComparison)}
                                    className="px-3 py-1.5 text-xs font-medium bg-primary/10 hover:bg-primary/20 border border-primary/30 rounded-lg transition-colors flex items-center gap-1.5 text-primary"
                                >
                                    <GitCompare className="w-3.5 h-3.5" />
                                    Compare Top 3
                                </button>
                            </div>
                        </div>

                        {/* Recommended Model - Headline */}
                        <Card className="p-8 border-2 border-primary bg-card/50 backdrop-blur-md shadow-[0_0_30px_rgba(6,182,212,0.15)] glow-border">
                            <div className="flex flex-col md:flex-row md:items-start justify-between mb-6 gap-4">
                                <div>
                                    <p className="text-sm font-mono text-primary mb-2 flex items-center gap-2">
                                        <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                                        AI RECOMMENDED MODEL
                                    </p>
                                    <h2 className="text-4xl md:text-5xl font-bold text-foreground tracking-tight text-glow">
                                        {aiRecommendation.recommended_model}
                                    </h2>
                                    <div className="flex items-center gap-3 mt-3">
                                        <span className="text-sm text-muted-foreground">
                                            by {aiRecommendation.provider}
                                        </span>
                                        <span className={`px-2 py-0.5 rounded text-xs font-mono uppercase ${aiRecommendation.confidence === 'high'
                                            ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                                            : aiRecommendation.confidence === 'medium'
                                                ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                                                : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                                            }`}>
                                            {aiRecommendation.confidence} confidence
                                        </span>
                                    </div>
                                    <div className="mt-4 text-sm text-foreground/80 leading-relaxed border-l-2 border-primary/30 pl-3">
                                        <span className="text-xs font-bold text-primary uppercase block mb-1">Analyst Reasoning</span>
                                        {aiRecommendation.reasoning}
                                    </div>
                                </div>

                                {/* Cost Details */}
                                <div className="bg-background/40 backdrop-blur-sm border border-border/50 rounded-xl p-4 min-w-[220px]">
                                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Pricing</h3>
                                    <div className="space-y-2">
                                        <div className="flex justify-between items-center">
                                            <span className="text-xs text-muted-foreground">Input (1K tokens)</span>
                                            <span className="font-mono text-sm text-foreground">${aiRecommendation.cost_analysis.per_1k_input_tokens.toFixed(4)}</span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-xs text-muted-foreground">Output (1K tokens)</span>
                                            <span className="font-mono text-sm text-foreground">${aiRecommendation.cost_analysis.per_1k_output_tokens.toFixed(4)}</span>
                                        </div>
                                        <div className="pt-2 border-t border-border/30">
                                            <div className="flex justify-between items-center">
                                                <span className="text-xs text-muted-foreground">Est. Monthly</span>
                                                <span className="font-mono text-xl font-bold text-primary">${aiRecommendation.cost_analysis.estimated_monthly_usd.toFixed(2)}</span>
                                            </div>
                                            {/* Budget check */}
                                            <div className={`text-xs mt-1 text-right flex items-center justify-end gap-1 ${aiRecommendation.cost_analysis.within_budget ? 'text-green-400' : 'text-orange-400'}`}>
                                                {aiRecommendation.cost_analysis.within_budget ? <CheckIcon /> : <XIcon />}
                                                {aiRecommendation.cost_analysis.within_budget ? 'Within budget' : 'Over budget'}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Strategic Fit */}
                            <div className="mb-6 bg-cyan-500/5 rounded-lg p-5 border border-cyan-500/20">
                                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2 text-foreground">
                                    <span className="text-lg">🎯</span>
                                    Strategic Fit
                                </h3>
                                <p className="text-muted-foreground leading-relaxed text-sm md:text-base">
                                    {aiRecommendation.use_case_fit}
                                </p>
                                {aiRecommendation.use_case_fit && (
                                    <p className="mt-3 text-sm text-primary/80 italic">
                                        {aiRecommendation.use_case_fit}
                                    </p>
                                )}
                            </div>

                            {/* Strengths & Weaknesses Grid */}
                            <div className="grid md:grid-cols-2 gap-4 mb-6">
                                {/* Advantages */}
                                <div className="bg-green-500/5 rounded-lg p-4 border border-green-500/20">
                                    <h3 className="text-sm font-semibold text-green-400 mb-3 flex items-center gap-2">
                                        <span className="text-lg">💪</span> Advantages
                                    </h3>
                                    <ul className="space-y-2">
                                        {aiRecommendation.advantages.map((strength, idx) => (
                                            <li key={idx} className="text-sm text-foreground/90 flex items-start gap-2">
                                                <span className="text-green-400 mt-0.5">✓</span>
                                                <span>{strength}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                {/* Disadvantages */}
                                <div className="bg-orange-500/5 rounded-lg p-4 border border-orange-500/20">
                                    <h3 className="text-sm font-semibold text-orange-400 mb-3 flex items-center gap-2">
                                        <span className="text-lg">⚠️</span> Disadvantages
                                    </h3>
                                    <ul className="space-y-2">
                                        {aiRecommendation.disadvantages.map((weakness, idx) => (
                                            <li key={idx} className="text-sm text-foreground/90 flex items-start gap-2">
                                                <span className="text-orange-400 mt-0.5">•</span>
                                                <span>{weakness}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>

                            {/* Data Freshness */}
                            {/* Data Freshness REMOVED as it's not in Mino response */}
                        </Card>

                        {/* Why Better Than Alternatives - Collapsed by Default */}
                        {aiRecommendation.similar_models && aiRecommendation.similar_models.length > 0 && (
                            <Card className="border border-border/50 bg-card/30">
                                <button
                                    onClick={() => setShowAlternatives(!showAlternatives)}
                                    className="w-full flex items-center justify-between p-4 text-sm font-semibold hover:bg-white/5 transition-colors"
                                >
                                    <span className="flex items-center gap-2 text-muted-foreground">
                                        🏆 Why better than similar models?
                                    </span>
                                    {showAlternatives ? (
                                        <ChevronUp className="w-4 h-4 text-muted-foreground" />
                                    ) : (
                                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                                    )}
                                </button>

                                {showAlternatives && (
                                    <div className="p-4 pt-0 space-y-3">
                                        <div className="mb-3 p-3 bg-primary/5 rounded border border-primary/10 text-sm text-foreground italic">
                                            "{aiRecommendation.why_better}"
                                        </div>
                                        {aiRecommendation.similar_models.map((alt, idx) => (
                                            <div key={idx} className="border-l-2 border-primary/50 pl-4 py-2 bg-primary/5 rounded-r">
                                                <p className="font-bold text-sm text-foreground">{alt.model} <span className="text-xs font-normal text-muted-foreground">({alt.provider})</span></p>
                                                <p className="text-xs text-muted-foreground mt-1">{alt.why_not}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </Card>
                        )}
                    </div>
                )}
            </main>

            {/* Comparison Modal */}
            {aiRecommendation && (
                <ComparisonModal
                    isOpen={showComparison}
                    onClose={() => setShowComparison(false)}
                    recommended={aiRecommendation}
                    alternatives={aiRecommendation.similar_models || []}
                />
            )}
        </div>
    );
};

// Simple icons for results
const CheckIcon = () => (
    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
    </svg>
);

const XIcon = () => (
    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
    </svg>
);

// Comparison Modal Component
const ComparisonModal = ({
    isOpen,
    onClose,
    recommended,
    alternatives
}: {
    isOpen: boolean;
    onClose: () => void;
    recommended: AIRecommendation;
    alternatives: any[]
}) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-background border border-border rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl relative">
                {/* Header */}
                <div className="p-6 border-b border-border flex justify-between items-center bg-muted/20">
                    <div>
                        <h2 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">Model Comparison</h2>
                        <p className="text-sm text-muted-foreground mt-1">Comparing top candidates for your use case</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                        <XIcon />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {/* Recommended Model Column */}
                        <div className="p-4 rounded-xl border-2 border-primary bg-primary/5 relative">
                            <div className="absolute top-0 right-0 bg-primary text-primary-foreground text-[10px] font-bold px-2 py-1 rounded-bl-lg">WINNER</div>
                            <h3 className="font-bold text-lg mb-1">{recommended.recommended_model}</h3>
                            <p className="text-xs text-muted-foreground mb-4">{recommended.provider}</p>

                            <div className="space-y-4">
                                <div>
                                    <h4 className="text-xs font-semibold uppercase text-primary mb-1">Why it won</h4>
                                    <p className="text-sm text-foreground/90 leading-relaxed">{recommended.reasoning}</p>
                                </div>
                                <div className="pt-2 border-t border-primary/20">
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-muted-foreground">Est. Cost</span>
                                        <span className="font-mono">${recommended.cost_analysis?.estimated_monthly_usd.toFixed(2)}</span>
                                    </div>
                                    <div className="flex justify-between text-xs">
                                        <span className="text-muted-foreground">Context</span>
                                        <span className="font-mono">{(recommended.technical_specs?.context_window / 1000).toFixed(0)}k</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Competitors */}
                        {alternatives.slice(0, 3).map((alt, idx) => (
                            <div key={idx} className="p-4 rounded-xl border border-border bg-card/50 hover:bg-card transition-colors">
                                <div className="flex items-center justify-between mb-1">
                                    <h3 className="font-bold text-base">{alt.model}</h3>
                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground border border-border">#{idx + 2}</span>
                                </div>
                                <p className="text-xs text-muted-foreground mb-4">{alt.provider}</p>

                                <div className="space-y-4">
                                    <div>
                                        <h4 className="text-xs font-semibold uppercase text-muted-foreground mb-1">Why not selected</h4>
                                        <p className="text-sm text-muted-foreground leading-relaxed">{alt.why_not}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="mt-8 p-4 bg-muted/20 rounded-lg border border-border/50">
                        <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                            <span className="text-lg">🤖</span> AI Analyst Verdict
                        </h4>
                        <p className="text-sm text-muted-foreground italic">"{recommended.why_better}"</p>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-border bg-muted/20 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition-colors text-sm"
                    >
                        Close Comparison
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Home;
