import { useState, useCallback, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { GitCompare, Zap } from "lucide-react";
import DashboardHeader from "@/components/DashboardHeader";
import SearchCommand from "@/components/SearchCommand";
import TerminalFeed from "@/components/TerminalFeed";
import TopModelsCard from "@/components/TopModelsCard";
import BenchmarkChart from "@/components/BenchmarkChart";
import SourceStatusCard from "@/components/SourceStatusCard";
import ModelDetailPanel from "@/components/ModelDetailPanel";
import CrossBenchmarkTable from "@/components/CrossBenchmarkTable";
import QuickBenchmarksModal from "@/components/QuickBenchmarksModal";
import ExpertiseRadarChart from "@/components/ExpertiseRadarChart";
import { Button } from "@/components/ui/button";

interface LogEntry {
  id: string;
  timestamp: Date;
  type: "info" | "success" | "warning" | "error" | "system";
  message: string;
}

interface ModelRanking {
  rank: number;
  name: string;
  score: number;
  change: "up" | "down" | "same";
  source: string;
}

interface BenchmarkData {
  name: string;
  score: number;
  maxScore: number;
}

interface SourceStatus {
  name: string;
  url: string;
  status: "idle" | "connecting" | "fetching" | "success" | "error" | "not_found" | "partial";
  lastUpdate?: Date;
}

interface ModelDetail {
  name: string;
  source: string;
  metrics: {
    rank: number;
    score: number;
    elo?: number;
    mmlu?: number;
    coding?: number;
  };
  secondaryMetrics?: Record<string, number>;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const Index = () => {
  const [isSearching, setIsSearching] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [searchedModel, setSearchedModel] = useState("");
  const [topModels, setTopModels] = useState<ModelRanking[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkData[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelDetail | null>(null);
  const [showModelDetail, setShowModelDetail] = useState(false);
  const [showQuickBenchmarks, setShowQuickBenchmarks] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Radar chart data for expertise fingerprint
  const [radarData, setRadarData] = useState<{ category: string; score: number; maxScore: number }[]>([]);

  // Phase 1 sources (6 benchmarks only)
  const [sources, setSources] = useState<SourceStatus[]>([
    { name: "HuggingFace", url: "huggingface.co/spaces/open-llm-leaderboard", status: "idle" },
    { name: "LMSYS Arena", url: "lmarena.ai/leaderboard", status: "idle" },
    { name: "LiveCodeBench", url: "livecodebench.github.io/leaderboard.html", status: "idle" },
    { name: "Vellum", url: "vellum.ai/llm-leaderboard", status: "idle" },
    { name: "MASK", url: "scale.com/leaderboard/mask", status: "idle" },
    { name: "Vectara", url: "github.com/vectara/hallucination-leaderboard", status: "idle" },
  ]);

  const addLog = useCallback((type: LogEntry["type"], message: string) => {
    const newLog: LogEntry = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      type,
      message,
    };
    setLogs((prev) => [...prev, newLog]);
  }, []);

  const updateSourceStatus = useCallback(
    (name: string, status: SourceStatus["status"]) => {
      setSources((prev) =>
        prev.map((s) =>
          s.name === name
            ? { ...s, status, lastUpdate: status === "success" ? new Date() : s.lastUpdate }
            : s
        )
      );
    },
    []
  );

  const parseMinoEvent = useCallback((data: string, query: string) => {
    try {
      const parsed = JSON.parse(data);

      // Handle MODEL_NOT_FOUND explicitly
      if (parsed.error === 'MODEL_NOT_FOUND' && parsed.source) {
        const sourceNameMap: Record<string, string> = {
          'huggingface': 'HuggingFace',
          'lmsys_arena': 'LMSYS Arena',
          'livecodebench': 'LiveCodeBench',
          'vellum': 'Vellum',
          'mask': 'MASK',
          'vectara': 'Vectara'
        };
        const uiName = sourceNameMap[parsed.source.toLowerCase()] || parsed.source;
        updateSourceStatus(uiName, "not_found");
        addLog("warning", `${uiName}: Model not found.`);
        return;
      }

      // Handle different event types from Mino
      if (parsed.type === 'log' || parsed.type === 'system') {
        const message = parsed.data || parsed.message || '';

        // Detect source status from log messages or parsed.source field
        const lowerMessage = message.toLowerCase();
        const sourceKey = parsed.source?.toLowerCase() || '';

        // HuggingFace
        if (lowerMessage.includes('huggingface') || lowerMessage.includes('hf.co') || sourceKey === 'huggingface') {
          if (lowerMessage.includes('connecting') || parsed.status === 'running') {
            updateSourceStatus("HuggingFace", "connecting");
          } else if (lowerMessage.includes('fetching')) {
            updateSourceStatus("HuggingFace", "fetching");
          } else if (lowerMessage.includes('complete') || lowerMessage.includes('success') || parsed.status === 'completed') {
            updateSourceStatus("HuggingFace", "success");
          } else if (parsed.status === 'failed') {
            updateSourceStatus("HuggingFace", "error");
          }
        }
        // LMSYS Arena
        if (lowerMessage.includes('lmsys') || lowerMessage.includes('arena') || sourceKey === 'lmsys_arena') {
          if (lowerMessage.includes('connecting') || parsed.status === 'running') {
            updateSourceStatus("LMSYS Arena", "connecting");
          } else if (lowerMessage.includes('fetching')) {
            updateSourceStatus("LMSYS Arena", "fetching");
          } else if (lowerMessage.includes('complete') || lowerMessage.includes('success') || parsed.status === 'completed') {
            updateSourceStatus("LMSYS Arena", "success");
          } else if (parsed.status === 'failed') {
            updateSourceStatus("LMSYS Arena", "error");
          }
        }
        // LiveCodeBench
        if (lowerMessage.includes('livecodebench') || lowerMessage.includes('livecode') || sourceKey === 'livecodebench') {
          if (lowerMessage.includes('connecting') || parsed.status === 'running') {
            updateSourceStatus("LiveCodeBench", "connecting");
          } else if (lowerMessage.includes('fetching')) {
            updateSourceStatus("LiveCodeBench", "fetching");
          } else if (lowerMessage.includes('complete') || lowerMessage.includes('success') || parsed.status === 'completed') {
            updateSourceStatus("LiveCodeBench", "success");
          } else if (parsed.status === 'failed') {
            updateSourceStatus("LiveCodeBench", "error");
          }
        }
        // Vellum
        if (lowerMessage.includes('vellum') || sourceKey === 'vellum') {
          if (lowerMessage.includes('connecting') || parsed.status === 'running') {
            updateSourceStatus("Vellum", "connecting");
          } else if (lowerMessage.includes('fetching')) {
            updateSourceStatus("Vellum", "fetching");
          } else if (lowerMessage.includes('complete') || lowerMessage.includes('success') || parsed.status === 'completed') {
            updateSourceStatus("Vellum", "success");
          } else if (parsed.status === 'failed') {
            updateSourceStatus("Vellum", "error");
          }
        }
        // MASK (Safety benchmark)
        if (lowerMessage.includes('mask') || lowerMessage.includes('deception') || sourceKey === 'mask') {
          if (lowerMessage.includes('connecting') || parsed.status === 'running') {
            updateSourceStatus("MASK", "connecting");
          } else if (lowerMessage.includes('fetching')) {
            updateSourceStatus("MASK", "fetching");
          } else if (lowerMessage.includes('complete') || lowerMessage.includes('success') || parsed.status === 'completed') {
            updateSourceStatus("MASK", "success");
          } else if (parsed.status === 'failed') {
            updateSourceStatus("MASK", "error");
          }
        }
        // Vectara (Hallucination benchmark)
        if (lowerMessage.includes('vectara') || lowerMessage.includes('hallucination') || sourceKey === 'vectara') {
          if (lowerMessage.includes('connecting') || parsed.status === 'running') {
            updateSourceStatus("Vectara", "connecting");
          } else if (lowerMessage.includes('fetching')) {
            updateSourceStatus("Vectara", "fetching");
          } else if (lowerMessage.includes('complete') || lowerMessage.includes('success') || parsed.status === 'completed') {
            updateSourceStatus("Vectara", "success");
          } else if (parsed.status === 'failed') {
            updateSourceStatus("Vectara", "error");
          }
        }

        // Determine log type from message content
        let logType: LogEntry["type"] = "info";
        if (lowerMessage.includes('error') || lowerMessage.includes('failed')) {
          logType = "error";
        } else if (lowerMessage.includes('success') || lowerMessage.includes('found') || lowerMessage.includes('complete')) {
          logType = "success";
        } else if (lowerMessage.includes('warning')) {
          logType = "warning";
        } else if (parsed.type === 'system') {
          logType = "system";
        }

        addLog(logType, message);
      } else if (parsed.type === 'result' || parsed.type === 'data') {
        // Handle final results
        console.log('[Model Scout] Received result:', parsed);
        const result = parsed.data || parsed;

        if (result && !result.error) {
          // Extract score - could be average_score, arena_elo, or score
          const score = result.average_score || result.arena_elo || result.score || 0;

          const model: ModelRanking = {
            rank: result.rank || 1,
            name: result.model || query,
            score: typeof score === 'number' ? score : Number(score) || 0,
            change: "same" as const,
            source: result.source || parsed.source || "Unknown",
          };
          console.log('[Model Scout] Adding model:', model);
          setTopModels(prev => [...prev, model]);

          // Extract benchmarks from metrics
          const metrics = result.benchmark_metrics || result.metrics || result;
          if (metrics && typeof metrics === 'object') {
            // Filter out non-numeric fields (allow numeric strings like "7.0 %")
            const numericMetrics = Object.entries(metrics).filter(
              ([key, val]) => {
                if (['rank', 'model', 'source', 'display_name'].includes(key)) return false;
                if (typeof val === 'number') return true;
                if (typeof val === 'string' && !isNaN(parseFloat(val))) return true;
                return false;
              }
            );

            if (numericMetrics.length > 0) {
              const benchmarkData: BenchmarkData[] = numericMetrics.map(
                ([name, score]) => {
                  let cleanScore = score;
                  // Handle "7.0 %" string case
                  if (typeof score === 'string') {
                    cleanScore = parseFloat(score.replace('%', ''));
                  }
                  return {
                    name: name.toUpperCase().replace(/_/g, ' '),
                    score: Number(cleanScore) || 0,
                    maxScore: name.toLowerCase().includes('elo') ? 1400 : 100,
                  };
                }
              );
              console.log('[Model Scout] Adding benchmarks:', benchmarkData);
              setBenchmarks(prev => {
                // Merge with existing, avoiding duplicates
                const existing = new Set(prev.map(b => b.name));
                const newBenchmarks = benchmarkData.filter(b => !existing.has(b.name));
                return [...prev, ...newBenchmarks];
              });

              // Also update radar chart data based on source category
              // Phase 1 axes: Logic, Coding, Economics, Safety
              const sourceCategory = (result.source || parsed.source || '').toLowerCase();
              let category = 'Logic'; // Default

              if (sourceCategory.includes('livecode') || sourceCategory.includes('coding') || sourceCategory.includes('humaneval')) {
                category = 'Coding';
              } else if (sourceCategory.includes('vellum') || sourceCategory.includes('token') || sourceCategory.includes('economics')) {
                category = 'Economics';
              } else if (sourceCategory.includes('mask') || sourceCategory.includes('vectara') || sourceCategory.includes('safety') || sourceCategory.includes('hallucination')) {
                category = 'Safety';
              } else if (sourceCategory.includes('hugging') || sourceCategory.includes('arena') || sourceCategory.includes('logic')) {
                category = 'Logic';
              }

              const avgScore = numericMetrics.reduce((sum, [, val]) => {
                let cleanVal = val;
                if (typeof val === 'string') {
                  cleanVal = parseFloat(val.replace('%', ''));
                }
                return sum + (Number(cleanVal) || 0);
              }, 0) / numericMetrics.length;

              if (avgScore > 0) {
                setRadarData(prev => {
                  const existing = prev.find(r => r.category === category);
                  if (existing) {
                    // Update existing category with average
                    return prev.map(r =>
                      r.category === category
                        ? { ...r, score: (r.score + avgScore) / 2 }
                        : r
                    );
                  }
                  return [...prev, { category, score: avgScore, maxScore: 100 }];
                });
              }
            }
          }

          addLog("success", `Found ${result.model || query} on ${result.source || parsed.source}`);
        }
      } else if (parsed.type === 'done') {
        addLog("success", parsed.data || "Source extraction complete");
      } else if (parsed.type === 'complete') {
        addLog("system", "Search complete. All sources processed.");
      } else if (parsed.type === 'error') {
        addLog("error", parsed.data || "An error occurred");
      }
    } catch {
      // If not JSON, treat as plain text log
      if (data.trim()) {
        addLog("info", data);
      }
    }
  }, [addLog, updateSourceStatus]);

  const searchWithAPI = useCallback(
    async (query: string) => {
      setIsSearching(true);
      setSearchedModel(query);
      setLogs([]);
      setTopModels([]);
      setBenchmarks([]);
      setRadarData([]);

      // Reset sources
      setSources((prev) => prev.map((s) => ({ ...s, status: "idle" as const })));

      // Cancel any existing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      addLog("system", `Initializing search for "${query}"...`);
      addLog("info", "Connecting to Model Scout API...");

      try {
        const response = await fetch(`${API_BASE_URL}/api/search`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model_name: query,
            // Phase 1 sources only
            sources: ['huggingface', 'lmsys_arena', 'livecodebench', 'vellum', 'mask', 'vectara'],
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        addLog("success", "API connection established");

        // Read SSE stream
        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("No response body");
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              parseMinoEvent(data, query);
            }
          }
        }

        // Process remaining buffer
        if (buffer.startsWith('data: ')) {
          parseMinoEvent(buffer.slice(6), query);
        }

      } catch (error: unknown) {
        const err = error as Error;
        if (err.name === 'AbortError') {
          addLog("warning", "Search cancelled");
        } else {
          console.error('API error:', err);
          addLog("error", `API Error: ${err.message}`);

          // Use mock data for demonstration
          addLog("info", "Loading sample data for demonstration...");

          const mockModels: ModelRanking[] = [
            { rank: 1, name: query, score: 85.2, change: "same", source: "HuggingFace" },
            { rank: 3, name: query, score: 1245, change: "up", source: "LMSys Arena" },
            { rank: 2, name: query, score: 82.1, change: "same", source: "Papers With Code" },
          ];
          setTopModels(mockModels);

          const mockBenchmarks: BenchmarkData[] = [
            { name: "MMLU", score: 85.2, maxScore: 100 },
            { name: "ARC", score: 78.4, maxScore: 100 },
            { name: "HellaSwag", score: 89.1, maxScore: 100 },
            { name: "HumanEval", score: 76.3, maxScore: 100 },
            { name: "GSM8K", score: 68.9, maxScore: 100 },
          ];
          setBenchmarks(mockBenchmarks);

          // Update source statuses
          updateSourceStatus("HuggingFace", "success");
          updateSourceStatus("LMSYS Arena", "success");
          updateSourceStatus("PapersWithCode", "success");

          addLog("success", "Sample data loaded successfully");
        }
      } finally {
        setIsSearching(false);
      }
    },
    [addLog, parseMinoEvent, updateSourceStatus]
  );

  const handleSearch = (query: string) => {
    searchWithAPI(query);
  };

  const handleModelClick = (model: ModelRanking) => {
    const detail: ModelDetail = {
      name: model.name,
      source: model.source,
      metrics: {
        rank: model.rank,
        score: model.score,
        elo: 1287,
        mmlu: 86.8,
        coding: 81.5,
      },
      secondaryMetrics: {
        MMLU: 86.8,
        GSM8K: 92.3,
        HumanEval: 81.5,
      },
    };
    setSelectedModel(detail);
    setShowModelDetail(true);
  };

  return (
    <div className="min-h-screen bg-background grid-pattern">
      <DashboardHeader />

      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <section className="mb-8 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-4 tracking-tight">
            Model <span className="text-primary text-glow-cyber">Scout</span>
          </h1>
          {/* Hero Section */}
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto mb-6">
            AI Model Benchmark Radar — Unified insights across HuggingFace, LMSys Arena, and more.
          </p>

          {/* Quick Actions */}
          <div className="flex justify-center gap-4 mb-8">
            <Link to="/compare">
              <Button variant="outline" className="font-mono border-primary/50 hover:bg-primary/10">
                <GitCompare className="w-4 h-4 mr-2" />
                Overlay Models
              </Button>
            </Link>
            <Button
              variant="ghost"
              className="font-mono"
              onClick={() => setShowQuickBenchmarks(true)}
            >
              <Zap className="w-4 h-4 mr-2" />
              Quick Benchmarks
            </Button>
          </div>
        </section>

        {/* Search Section */}
        <section className="mb-8">
          <SearchCommand onSearch={handleSearch} isSearching={isSearching} />
        </section>

        {/* Bento Grid Layout */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-4 auto-rows-min">
          {/* Terminal Feed - Spans 8 columns on large screens */}
          <div className="lg:col-span-8 min-h-[350px] relative">
            <div className="absolute top-2 right-2 z-10">
              <span className="text-[10px] font-mono text-muted-foreground/70 bg-background/80 px-2 py-1 rounded border border-border/50">
                On-demand extraction only. No scheduled refresh in Phase-1.
              </span>
            </div>
            <TerminalFeed logs={logs} isActive={isSearching} />
          </div>

          {/* Source Status - Spans 4 columns on large screens */}
          <div className="lg:col-span-4 min-h-[350px]">
            <SourceStatusCard sources={sources} />
          </div>

          {/* Top Models - Spans 4 columns on large screens */}
          <div className="lg:col-span-4 min-h-[400px]">
            <TopModelsCard models={topModels} isLoading={isSearching} />
          </div>

          {/* Benchmark Chart - Spans 4 columns on large screens */}
          <div className="lg:col-span-4 min-h-[400px]">
            <BenchmarkChart
              data={benchmarks}
              modelName={searchedModel}
              isLoading={isSearching}
            />
          </div>

          {/* Expertise Radar Chart - Spans 4 columns on large screens */}
          <div className="lg:col-span-4 min-h-[400px]">
            <div className="h-full bg-card/50 backdrop-blur-sm border border-border/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-mono text-primary flex items-center gap-2">
                  <span className="w-2 h-2 bg-secondary rounded-full animate-pulse" />
                  EXPERTISE FINGERPRINT
                </h3>
                <span className="text-xs text-muted-foreground font-mono">
                  Capability Radar
                </span>
              </div>
              <ExpertiseRadarChart
                data={radarData}
                modelName={searchedModel}
              />
            </div>
          </div>

          {/* Cross-Benchmark Table - Full Width */}
          <div className="lg:col-span-12">
            <CrossBenchmarkTable />
          </div>
        </section>
      </main>

      {/* Model Detail Modal */}
      <ModelDetailPanel
        model={selectedModel}
        isVisible={showModelDetail}
        onClose={() => setShowModelDetail(false)}
      />

      {/* Quick Benchmarks Modal */}
      <QuickBenchmarksModal
        isOpen={showQuickBenchmarks}
        onClose={() => setShowQuickBenchmarks(false)}
        onSelectModel={(model) => {
          setShowQuickBenchmarks(false);
          handleSearch(model);
        }}
      />
    </div>
  );
};

export default Index;
