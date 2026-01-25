import { useState } from "react";
import DashboardHeader from "@/components/DashboardHeader";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Search, Loader2, TrendingUp, Award, Zap, ChevronDown, ChevronUp } from "lucide-react";

interface AnalysisSection {
  title: string;
  content: string;
  key_benchmarks?: string[];
}

interface QuickStats {
  overall_rank?: string;
  best_category?: string;
  avg_score?: string;
  release_date?: string;
}

interface BenchmarksTable {
  headers: string[];
  rows: Record<string, string>[];
}

interface BenchmarkReport {
  model_name: string;
  introduction: string;
  quick_stats?: QuickStats;
  analysis: AnalysisSection[];
  summary: string;
  benchmarks_table: BenchmarksTable;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const Benchmarks = () => {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set());

  const handleAnalyze = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setReport(null);
    setLogs([]); // Clear logs

    try {
      // Use streaming endpoint
      const response = await fetch(`${API_BASE_URL}/api/v2/analyst/benchmarks/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_name: query }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch benchmark analysis");
      }

      // Handle SSE Stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("Processing failed: No response body");

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim().startsWith('data: ')) {
            const dataStr = line.trim().slice(6);
            try {
              const event = JSON.parse(dataStr);

              if (event.type === 'log') {
                setLogs(prev => [...prev, event.message]);
              } else if (event.type === 'result') {
                let reportData = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;

                // Normalization for Streamed Data (Aggregator Format)
                if (!reportData.analysis && !reportData.benchmarks_table && reportData.metrics) {
                  reportData = {
                    model_name: reportData.model_name,
                    introduction: reportData.consensus || "Analysis complete.",
                    summary: reportData.consensus,
                    quick_stats: {
                      avg_score: reportData.overall_score > 0 ? reportData.overall_score.toString() : "N/A",
                      overall_rank: "Top Tier", // Placeholder or derived
                      best_category: "General Capabilities",
                      release_date: "2024-2025"
                    },
                    analysis: [
                      {
                        title: "Strengths & Advantages",
                        content: (reportData.strengths || []).join(". "),
                        key_benchmarks: []
                      },
                      {
                        title: "Weaknesses & Limitations",
                        content: (reportData.weaknesses || []).join(". "),
                        key_benchmarks: []
                      }
                    ],
                    benchmarks_table: {
                      headers: ["Model", ...Object.keys(reportData.metrics)],
                      rows: [
                        {
                          "Model": reportData.model_name,
                          ...reportData.metrics
                        }
                      ]
                    }
                  };
                }

                setReport(reportData);
              } else if (event.type === 'error') {
                throw new Error(event.message);
              }
            } catch (e) {
              console.warn("Failed to parse event:", dataStr);
            }
          }
        }
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to generate analysis. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSection = (idx: number) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(idx)) {
      newExpanded.delete(idx);
    } else {
      newExpanded.add(idx);
    }
    setExpandedSections(newExpanded);
  };

  const getScoreColor = (score: string) => {
    const num = parseFloat(score);
    if (isNaN(num)) return "text-muted-foreground";
    if (num >= 90) return "text-green-400";
    if (num >= 80) return "text-cyan-400";
    if (num >= 70) return "text-yellow-400";
    return "text-orange-400";
  };

  const getScoreBar = (score: string) => {
    const num = parseFloat(score);
    if (isNaN(num)) return 0;
    return Math.min(num, 100);
  };

  return (
    <div className="min-h-screen bg-background grid-pattern">
      <DashboardHeader />

      <main className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Compact Search Header */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                Benchmark <span className="text-primary text-glow-cyber">Deep Dive</span>
              </h1>
              <p className="text-sm text-muted-foreground mt-1">Comprehensive performance metrics across all categories</p>
            </div>
          </div>

          <div className="flex gap-2">
            <Input
              placeholder="Model name (e.g., DeepSeek R1, GPT-4o, Claude 3.5 Sonnet)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="bg-card/50 border-primary/20 h-11 font-mono"
              onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
            />
            <Button
              onClick={handleAnalyze}
              disabled={isLoading}
              className="h-11 px-6 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/50"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            </Button>
          </div>
        </section>

        {error && (
          <div className="text-red-400 text-center mb-8 bg-red-900/10 p-4 rounded-lg border border-red-900/20 font-mono text-sm">
            {error}
          </div>
        )}

        {isLoading && logs.length > 0 && (
          <div className="mb-8 bg-black font-mono text-xs p-4 rounded-lg border border-primary/30 shadow-[0_0_20px_rgba(0,0,0,0.5)] h-48 overflow-y-auto custom-scrollbar animate-in fade-in slide-in-from-top-2 duration-300 relative group">
            <div className="absolute top-2 right-2 flex gap-1.5 opacity-50 group-hover:opacity-100 transition-opacity">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
              <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
              <div className="w-2.5 h-2.5 rounded-full bg-green-500/50" />
            </div>
            <div className="flex items-center gap-2 mb-3 text-primary border-b border-primary/20 pb-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_#22c55e]" />
              <span className="font-bold tracking-wider">LIVE SQUAD LOGS (4 AGENTS ACTIVE)</span>
              <span className="text-muted-foreground ml-auto pr-8">v2.4.0-squad</span>
            </div>
            <div className="space-y-1.5 font-mono">
              {logs.map((log, i) => (
                <div key={i} className="text-green-400/90 break-all pl-2 flex items-start gap-2 hover:bg-white/5 transition-colors rounded leading-relaxed">
                  <span className="opacity-40 select-none shrink-0 text-[10px] mt-0.5">&gt;</span>
                  <span>{log}</span>
                </div>
              ))}
              <div className="flex items-center gap-2 pl-2">
                <span className="text-green-500 animate-pulse">_</span>
              </div>
            </div>
          </div>
        )}

        {report && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            {/* Model Header with Quick Stats */}
            <div className="bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border border-primary/20 rounded-xl p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold mb-2">{report.model_name}</h2>
                  <p className="text-sm text-muted-foreground max-w-3xl leading-relaxed">
                    {report.introduction}
                  </p>
                </div>
                <Award className="w-8 h-8 text-primary/50" />
              </div>

              {/* Quick Stats Grid */}
              {report.quick_stats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 pt-4 border-t border-primary/10">
                  {report.quick_stats.overall_rank && (
                    <div className="bg-card/40 rounded-lg p-3 border border-border/30">
                      <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Rank</div>
                      <div className="text-lg font-bold text-primary">{report.quick_stats.overall_rank}</div>
                    </div>
                  )}
                  {report.quick_stats.best_category && (
                    <div className="bg-card/40 rounded-lg p-3 border border-border/30">
                      <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Best At</div>
                      <div className="text-sm font-semibold text-foreground">{report.quick_stats.best_category}</div>
                    </div>
                  )}
                  {report.quick_stats.avg_score && (
                    <div className="bg-card/40 rounded-lg p-3 border border-border/30">
                      <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Avg Score</div>
                      <div className="text-lg font-bold text-cyan-400">{report.quick_stats.avg_score}</div>
                    </div>
                  )}
                  {report.quick_stats.release_date && (
                    <div className="bg-card/40 rounded-lg p-3 border border-border/30">
                      <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Released</div>
                      <div className="text-sm font-semibold text-foreground">{report.quick_stats.release_date}</div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Performance Categories - Compact Cards with Inline Stats */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {(report.analysis || []).map((item, idx) => (
                <Card
                  key={idx}
                  className="p-4 bg-card/40 border-border/50 hover:border-primary/30 transition-all cursor-pointer group"
                  onClick={() => toggleSection(idx)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-sm uppercase tracking-wide text-primary/80">{item.title}</h3>
                    {expandedSections.has(idx) ?
                      <ChevronUp className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" /> :
                      <ChevronDown className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    }
                  </div>

                  {/* Inline Benchmark Badges */}
                  {item.key_benchmarks && item.key_benchmarks.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {item.key_benchmarks.map((bench, i) => (
                        <span
                          key={i}
                          className="text-[10px] font-mono bg-primary/10 text-primary px-2 py-0.5 rounded border border-primary/20"
                        >
                          {bench}
                        </span>
                      ))}
                    </div>
                  )}

                  {expandedSections.has(idx) && (
                    <p className="text-xs text-muted-foreground leading-relaxed mt-3 pt-3 border-t border-border/30">
                      {item.content}
                    </p>
                  )}

                  {!expandedSections.has(idx) && !item.key_benchmarks && (
                    <div className="flex items-center gap-2 mt-2">
                      <TrendingUp className="w-3 h-3 text-green-400" />
                      <span className="text-xs text-muted-foreground">Click to expand</span>
                    </div>
                  )}
                </Card>
              ))}
            </div>

            {/* Executive Summary - Compact */}
            <Card className="p-5 bg-primary/5 border-primary/20">
              <div className="flex items-start gap-3">
                <Zap className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-semibold mb-1 text-primary uppercase tracking-wide">Executive Summary</h3>
                  <p className="text-sm text-foreground/80 leading-relaxed">{report.summary || "No summary available."}</p>
                </div>
              </div>
            </Card>

            {/* Benchmarks Table - Enhanced with Visual Bars */}
            <div>
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <span className="w-1 h-5 bg-primary rounded-full"></span>
                Performance Metrics
              </h3>

              <div className="overflow-hidden rounded-xl border border-border/50 bg-card/20">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/50 border-b border-border/50">
                      <tr>
                        {(report.benchmarks_table?.headers || []).map((header, i) => (
                          <th
                            key={i}
                            className={`px-4 py-3 text-left font-semibold text-xs uppercase tracking-wider ${i === 0 ? "text-foreground sticky left-0 bg-muted/50" : "text-muted-foreground"
                              }`}
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/30">
                      {(report.benchmarks_table?.rows || []).map((row, idx) => {
                        const isTargetModel = idx === 0;
                        return (
                          <tr
                            key={idx}
                            className={`hover:bg-muted/20 transition-colors ${isTargetModel ? "bg-primary/5" : ""
                              }`}
                          >
                            {(report.benchmarks_table?.headers || []).map((header, cellIdx) => {
                              const value = row[header] || row[Object.keys(row)[cellIdx]] || "-";
                              const isModelName = cellIdx === 0;
                              const isNumeric = !isNaN(parseFloat(value));

                              return (
                                <td
                                  key={cellIdx}
                                  className={`px-4 py-3 ${isModelName ? "font-bold text-foreground sticky left-0 bg-inherit" : ""
                                    }`}
                                >
                                  {isNumeric && !isModelName ? (
                                    <div className="space-y-1">
                                      <div className="flex items-center justify-between gap-3">
                                        <span className={`font-mono font-semibold ${getScoreColor(value)}`}>
                                          {value}
                                        </span>
                                        {isTargetModel && (
                                          <Award className="w-3 h-3 text-primary/50" />
                                        )}
                                      </div>
                                      <div className="w-full bg-muted/30 rounded-full h-1 overflow-hidden">
                                        <div
                                          className={`h-full rounded-full transition-all ${parseFloat(value) >= 90 ? "bg-green-400" :
                                            parseFloat(value) >= 80 ? "bg-cyan-400" :
                                              parseFloat(value) >= 70 ? "bg-yellow-400" : "bg-orange-400"
                                            }`}
                                          style={{ width: `${getScoreBar(value)}%` }}
                                        />
                                      </div>
                                    </div>
                                  ) : (
                                    <span className={isModelName && isTargetModel ? "text-primary" : ""}>
                                      {value}
                                    </span>
                                  )}
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Legend */}
              <div className="flex items-center gap-6 mt-4 text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-400"></div>
                  <span>Excellent (90+)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-cyan-400"></div>
                  <span>Good (80-89)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                  <span>Average (70-79)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-orange-400"></div>
                  <span>Below Avg (&lt;70)</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Benchmarks;
