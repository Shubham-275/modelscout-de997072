/**
 * MODEL SCOUT - PROFESSIONAL COMPARISON (PHASE 3)
 * 
 * Focus: Decision Support, Data Density, Clarity.
 * Features: Radar Charts, Spec Tables, Scenario Winners.
 */

import { useState, useMemo } from "react";
import { ArrowLeft, Check, Zap, Brain, Code, BookOpen, Clock } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer,
    Legend
} from "recharts";
import DashboardHeader from "@/components/DashboardHeader";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://modelscout-production.up.railway.app';

// --- DATA & TYPES ---

interface ComparisonResult {
    models_compared: { model_a: string; model_b: string; };
    verdict: string;
    strengths: Record<string, string[]>;
    key_tradeoffs: string[];
    choose_if: Record<string, string[]>;
    cost_comparison: {
        cheaper_model: string;
        cost_difference_pct: number;
        [key: string]: any;
    };
    data_freshness: string;
}

// Static specs for the Radar Chart and Table (since these don't change often)
// Scores are conceptual (0-100) based on current benchmarks
const MODEL_SPECS: Record<string, {
    name: string;
    provider: string;
    context: string;
    maxOutput: string;
    knowledgeDate: string;
    scores: { subject: string; value: number }[];
}> = {
    "gpt-4o": {
        name: "GPT-4o",
        provider: "OpenAI",
        context: "128k",
        maxOutput: "4k",
        knowledgeDate: "Oct 2023",
        scores: [
            { subject: "Reasoning", value: 95 },
            { subject: "Coding", value: 90 },
            { subject: "Creativity", value: 88 },
            { subject: "Context", value: 85 },
            { subject: "Speed", value: 92 },
        ]
    },
    "gpt-4o-mini": {
        name: "GPT-4o Mini",
        provider: "OpenAI",
        context: "128k",
        maxOutput: "16k",
        knowledgeDate: "Oct 2023",
        scores: [
            { subject: "Reasoning", value: 75 },
            { subject: "Coding", value: 70 },
            { subject: "Creativity", value: 75 },
            { subject: "Context", value: 80 },
            { subject: "Speed", value: 98 },
        ]
    },
    "claude-3.5-sonnet": {
        name: "Claude 3.5 Sonnet",
        provider: "Anthropic",
        context: "200k",
        maxOutput: "8k",
        knowledgeDate: "Apr 2024",
        scores: [
            { subject: "Reasoning", value: 94 },
            { subject: "Coding", value: 98 },
            { subject: "Creativity", value: 95 },
            { subject: "Context", value: 96 },
            { subject: "Speed", value: 88 },
        ]
    },
    "gemini-1.5-pro": {
        name: "Gemini 1.5 Pro",
        provider: "Google",
        context: "2M",
        maxOutput: "8k",
        knowledgeDate: "Feb 2024",
        scores: [
            { subject: "Reasoning", value: 91 },
            { subject: "Coding", value: 85 },
            { subject: "Creativity", value: 89 },
            { subject: "Context", value: 100 },
            { subject: "Speed", value: 75 },
        ]
    },
    "gemini-1.5-flash": {
        name: "Gemini 1.5 Flash",
        provider: "Google",
        context: "1M",
        maxOutput: "8k",
        knowledgeDate: "Feb 2024",
        scores: [
            { subject: "Reasoning", value: 78 },
            { subject: "Coding", value: 75 },
            { subject: "Creativity", value: 80 },
            { subject: "Context", value: 95 },
            { subject: "Speed", value: 99 },
        ]
    },
    "llama-3-70b-instruct": {
        name: "Llama 3 70B",
        provider: "Meta (Open Source)",
        context: "8k",
        maxOutput: "8k",
        knowledgeDate: "Dec 2023",
        scores: [
            { subject: "Reasoning", value: 85 },
            { subject: "Coding", value: 82 },
            { subject: "Creativity", value: 85 },
            { subject: "Context", value: 60 },
            { subject: "Speed", value: 90 },
        ]
    },
    "deepseek-v3": {
        name: "DeepSeek V3",
        provider: "DeepSeek",
        context: "64k",
        maxOutput: "4k",
        knowledgeDate: "Dec 2023",
        scores: [
            { subject: "Reasoning", value: 92 },
            { subject: "Coding", value: 94 },
            { subject: "Creativity", value: 85 },
            { subject: "Context", value: 80 },
            { subject: "Speed", value: 85 },
        ]
    }
};

const ComparePage = () => {
    const [modelA, setModelA] = useState<string>("gpt-4o");
    const [modelB, setModelB] = useState<string>("claude-3.5-sonnet");
    const [isLoading, setIsLoading] = useState(false);
    const [comparison, setComparison] = useState<ComparisonResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleCompare = async () => {
        if (modelA === modelB) {
            setError("Select two different models to compare.");
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
            setError("Failed to fetch comparison. Please try again.");
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    // Prepare Radar Data
    const radarData = useMemo(() => {
        const specsA = MODEL_SPECS[modelA]?.scores || [];
        const specsB = MODEL_SPECS[modelB]?.scores || [];

        return specsA.map((s, i) => ({
            subject: s.subject,
            A: s.value,
            B: specsB[i]?.value || 0,
            fullMark: 100
        }));
    }, [modelA, modelB]);

    const getCost = (id: string, key: string = 'total_per_1m') => {
        if (!comparison) return 0;
        const c = comparison.cost_comparison[id];
        return (typeof c === 'object' && c !== null) ? Number(Number(c[key]).toFixed(2)) : 0;
    };

    return (
        <div className="min-h-screen bg-background text-foreground grid-pattern font-sans">
            <DashboardHeader />

            <main className="container mx-auto px-4 py-8 max-w-7xl">
                {/* Header */}
                <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-10">
                    <div className="flex items-center gap-4">
                        <Link to="/">
                            <Button variant="ghost" size="icon" className="rounded-full hover:bg-muted">
                                <ArrowLeft className="w-5 h-5" />
                            </Button>
                        </Link>
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">Model Comparison</h1>
                            <p className="text-muted-foreground">Technical specs and capability analysis</p>
                        </div>
                    </div>

                    {/* Simple Selectors */}
                    <Card className="flex items-center gap-4 p-2 pl-6 pr-2 bg-muted/30 border-muted-foreground/20 rounded-full shadow-lg">
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-primary">A</span>
                            <select
                                value={modelA}
                                onChange={(e) => setModelA(e.target.value)}
                                className="bg-transparent border-none text-sm font-medium focus:ring-0 cursor-pointer text-foreground py-2 outline-none"
                            >
                                {Object.entries(MODEL_SPECS).map(([k, v]) => <option key={k} value={k} className="bg-background text-foreground">{v.name}</option>)}
                            </select>
                        </div>
                        <span className="text-muted-foreground text-xs font-mono">VS</span>
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-cyan-500">B</span>
                            <select
                                value={modelB}
                                onChange={(e) => setModelB(e.target.value)}
                                className="bg-transparent border-none text-sm font-medium focus:ring-0 cursor-pointer text-foreground py-2 outline-none"
                            >
                                {Object.entries(MODEL_SPECS).map(([k, v]) => <option key={k} value={k} className="bg-background text-foreground">{v.name}</option>)}
                            </select>
                        </div>
                        <Button onClick={handleCompare} disabled={isLoading} className="rounded-full px-6 ml-2 font-bold shadow-md">
                            {isLoading ? "Analyzing..." : "Analyze Matchup"}
                        </Button>
                    </Card>
                </div>

                {error && <div className="p-4 mb-6 text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg text-center animate-in fade-in">{error}</div>}

                {comparison && (
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {/* LEFT COLUMN: Visuals & Specs (8 cols) */}
                        <div className="lg:col-span-8 space-y-8">

                            {/* 1. Radar Chart & Verdict */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                {/* Chart */}
                                <Card className="p-6 flex flex-col items-center justify-center bg-card/60 backdrop-blur-sm border-border">
                                    <h3 className="text-xs font-bold mb-4 text-muted-foreground uppercase tracking-widest flex items-center gap-2"><Brain className="w-3 h-3" /> Capability Fingerprint</h3>
                                    <div className="w-full h-[300px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                                                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                                                <PolarAngleAxis dataKey="subject" tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 10, fontWeight: 600 }} />
                                                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                                <Radar name={MODEL_SPECS[modelA]?.name} dataKey="A" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.3} />
                                                <Radar name={MODEL_SPECS[modelB]?.name} dataKey="B" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.3} />
                                                <Legend />
                                            </RadarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </Card>

                                {/* Plain English Verdict */}
                                <Card className="p-8 flex flex-col justify-center bg-gradient-to-br from-primary/5 via-card to-transparent border-primary/20 shadow-lg relative overflow-hidden">
                                    <div className="absolute top-0 right-0 w-20 h-20 bg-primary/10 blur-3xl rounded-full" />
                                    <h3 className="flex items-center gap-2 text-primary font-bold mb-4 text-sm uppercase tracking-wider">
                                        <Zap className="w-4 h-4" />
                                        Analyst Verdict
                                    </h3>
                                    <p className="text-lg leading-relaxed text-foreground/90 font-medium">
                                        "{comparison.verdict}"
                                    </p>
                                    <div className="mt-auto pt-6 border-t border-border/50 grid grid-cols-2 gap-4">
                                        <div>
                                            <p className="text-[10px] text-muted-foreground uppercase mb-1 font-bold tracking-wider">Cheaper Option</p>
                                            <p className="font-bold text-green-400">
                                                {MODEL_SPECS[comparison.cost_comparison.cheaper_model]?.name}
                                                <span className="text-xs font-normal ml-1 opacity-70">(-{comparison.cost_comparison.cost_difference_pct.toFixed(0)}%)</span>
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-[10px] text-muted-foreground uppercase mb-1 font-bold tracking-wider">Data Updated</p>
                                            <p className="font-mono text-sm opacity-70">{comparison.data_freshness}</p>
                                        </div>
                                    </div>
                                </Card>
                            </div>

                            {/* 2. Specs Table */}
                            <Card className="overflow-hidden border-border bg-card/40">
                                <Table>
                                    <TableHeader className="bg-muted/30">
                                        <TableRow className="border-border/50">
                                            <TableHead className="w-[200px] text-xs uppercase font-bold tracking-wider">Spec Feature</TableHead>
                                            <TableHead className="text-primary font-bold">{MODEL_SPECS[modelA]?.name}</TableHead>
                                            <TableHead className="text-cyan-500 font-bold">{MODEL_SPECS[modelB]?.name}</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        <TableRow className="border-border/50 hover:bg-transparent">
                                            <TableCell className="font-medium text-muted-foreground"><Clock className="w-3.5 h-3.5 inline mr-2 opacity-70" />Context Window</TableCell>
                                            <TableCell>{MODEL_SPECS[modelA]?.context}</TableCell>
                                            <TableCell>{MODEL_SPECS[modelB]?.context}</TableCell>
                                        </TableRow>
                                        <TableRow className="border-border/50 hover:bg-transparent">
                                            <TableCell className="font-medium text-muted-foreground"><Zap className="w-3.5 h-3.5 inline mr-2 opacity-70" />Max Output</TableCell>
                                            <TableCell>{MODEL_SPECS[modelA]?.maxOutput}</TableCell>
                                            <TableCell>{MODEL_SPECS[modelB]?.maxOutput}</TableCell>
                                        </TableRow>
                                        <TableRow className="border-border/50 hover:bg-transparent">
                                            <TableCell className="font-medium text-muted-foreground"><BookOpen className="w-3.5 h-3.5 inline mr-2 opacity-70" />Knowledge Cutoff</TableCell>
                                            <TableCell>{MODEL_SPECS[modelA]?.knowledgeDate}</TableCell>
                                            <TableCell>{MODEL_SPECS[modelB]?.knowledgeDate}</TableCell>
                                        </TableRow>
                                        <TableRow className="border-border/50 hover:bg-transparent">
                                            <TableCell className="font-medium text-muted-foreground">Provider</TableCell>
                                            <TableCell>{MODEL_SPECS[modelA]?.provider}</TableCell>
                                            <TableCell>{MODEL_SPECS[modelB]?.provider}</TableCell>
                                        </TableRow>
                                        <TableRow className="bg-muted/10 border-border/50 hover:bg-muted/10">
                                            <TableCell className="font-medium text-muted-foreground">Cost (Input / 1M)</TableCell>
                                            <TableCell>${getCost(modelA, 'input_per_1m')}</TableCell>
                                            <TableCell>${getCost(modelB, 'input_per_1m')}</TableCell>
                                        </TableRow>
                                        <TableRow className="bg-muted/10 border-border/50 hover:bg-muted/10">
                                            <TableCell className="font-medium text-muted-foreground">Cost (Output / 1M)</TableCell>
                                            <TableCell>${getCost(modelA, 'output_per_1m')}</TableCell>
                                            <TableCell>${getCost(modelB, 'output_per_1m')}</TableCell>
                                        </TableRow>
                                    </TableBody>
                                </Table>
                            </Card>

                            {/* 3. Tradeoffs */}
                            <Card className="p-6 bg-card border-border">
                                <h3 className="text-xs font-bold mb-4 text-muted-foreground uppercase tracking-widest">Critical Tradeoffs</h3>
                                <ul className="space-y-4">
                                    {comparison.key_tradeoffs.map((tradeoff, i) => (
                                        <li key={i} className="flex gap-4 items-start p-3 rounded-lg bg-muted/20 border border-white/5">
                                            <div className="mt-1 min-w-[20px] h-5 flex items-center justify-center rounded-full bg-yellow-500/20 text-yellow-500 font-bold text-xs ring-1 ring-yellow-500/50">
                                                !
                                            </div>
                                            <p className="text-sm text-foreground/80 leading-relaxed">{tradeoff}</p>
                                        </li>
                                    ))}
                                </ul>
                            </Card>
                        </div>

                        {/* RIGHT COLUMN: Key Decisions (4 cols) */}
                        <div className="lg:col-span-4 space-y-6">

                            {/* Scenario Winners */}
                            <Card className="p-6 bg-card border-border h-auto shadow-lg">
                                <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
                                    <Trophy className="w-5 h-5 text-yellow-500" />
                                    Recommended For...
                                </h3>
                                <div className="space-y-3">
                                    <ScenarioItem
                                        icon={<Code className="w-4 h-4" />}
                                        title="Coding Tasks"
                                        winner={MODEL_SPECS[modelA].scores.find(s => s.subject === "Coding")!.value > MODEL_SPECS[modelB].scores.find(s => s.subject === "Coding")!.value ? modelA : modelB}
                                    />
                                    <ScenarioItem
                                        icon={<Brain className="w-4 h-4" />}
                                        title="Complex Reasoning"
                                        winner={MODEL_SPECS[modelA].scores.find(s => s.subject === "Reasoning")!.value > MODEL_SPECS[modelB].scores.find(s => s.subject === "Reasoning")!.value ? modelA : modelB}
                                    />
                                    <ScenarioItem
                                        icon={<BookOpen className="w-4 h-4" />}
                                        title="Long Documents"
                                        winner={parseInt(MODEL_SPECS[modelA].context) > parseInt(MODEL_SPECS[modelB].context) ? modelA : modelB}
                                    />
                                    <ScenarioItem
                                        icon={<Zap className="w-4 h-4" />}
                                        title="Speed/Latency"
                                        winner={MODEL_SPECS[modelA].scores.find(s => s.subject === "Speed")!.value > MODEL_SPECS[modelB].scores.find(s => s.subject === "Speed")!.value ? modelA : modelB}
                                    />
                                </div>
                            </Card>

                            {/* Strengths Lists */}
                            <Card className="p-5 border-l-4 border-l-primary bg-primary/5">
                                <h4 className="font-bold text-primary mb-3 text-xs uppercase tracking-wider">{MODEL_SPECS[modelA]?.name} Wins On:</h4>
                                <ul className="space-y-2">
                                    {comparison.strengths[modelA]?.slice(0, 4).map((s, i) => (
                                        <li key={i} className="text-sm text-foreground/80 flex gap-2">
                                            <Check className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                                            <span className="leading-tight">{s}</span>
                                        </li>
                                    ))}
                                </ul>
                            </Card>

                            <Card className="p-5 border-l-4 border-l-cyan-500 bg-cyan-500/5">
                                <h4 className="font-bold text-cyan-500 mb-3 text-xs uppercase tracking-wider">{MODEL_SPECS[modelB]?.name} Wins On:</h4>
                                <ul className="space-y-2">
                                    {comparison.strengths[modelB]?.slice(0, 4).map((s, i) => (
                                        <li key={i} className="text-sm text-foreground/80 flex gap-2">
                                            <Check className="w-4 h-4 text-cyan-500 shrink-0 mt-0.5" />
                                            <span className="leading-tight">{s}</span>
                                        </li>
                                    ))}
                                </ul>
                            </Card>

                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

// Helper for Scenario Winners
const ScenarioItem = ({ icon, title, winner }: { icon: any, title: string, winner: string }) => {
    // Only show if we have valid winner data
    if (!winner) return null;

    return (
        <div className="flex items-center justify-between p-3 rounded-lg bg-muted/40 hover:bg-muted/60 transition-colors border border-transparent hover:border-border/50 cursor-default">
            <div className="flex items-center gap-3">
                <div className="p-2 rounded bg-background text-muted-foreground shadow-sm">
                    {icon}
                </div>
                <span className="text-sm font-medium">{title}</span>
            </div>
            <Badge variant="outline" className="font-bold bg-background text-foreground border-border">
                {MODEL_SPECS[winner]?.name}
            </Badge>
        </div>
    )
}

function Trophy(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
            <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
            <path d="M4 22h16" />
            <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" />
            <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" />
            <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" />
        </svg>
    )
}

export default ComparePage;
