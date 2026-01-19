import { useState, useCallback } from "react";
import DashboardHeader from "@/components/DashboardHeader";
import SearchCommand from "@/components/SearchCommand";
import TerminalFeed from "@/components/TerminalFeed";
import TopModelsCard from "@/components/TopModelsCard";
import BenchmarkChart from "@/components/BenchmarkChart";
import SourceStatusCard from "@/components/SourceStatusCard";
import ModelDetailPanel from "@/components/ModelDetailPanel";

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
  status: "idle" | "connecting" | "fetching" | "success" | "error";
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

const Index = () => {
  const [isSearching, setIsSearching] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [searchedModel, setSearchedModel] = useState("");
  const [topModels, setTopModels] = useState<ModelRanking[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkData[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelDetail | null>(null);
  const [showModelDetail, setShowModelDetail] = useState(false);

  const [sources, setSources] = useState<SourceStatus[]>([
    { name: "HuggingFace", url: "huggingface.co/spaces/open-llm-leaderboard", status: "idle" },
    { name: "LMSYS Arena", url: "lmarena.ai/leaderboard", status: "idle" },
    { name: "PapersWithCode", url: "paperswithcode.com/sota", status: "idle" },
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

  const simulateSearch = useCallback(
    async (query: string) => {
      setIsSearching(true);
      setSearchedModel(query);
      setLogs([]);
      setTopModels([]);
      setBenchmarks([]);

      // Reset sources
      setSources((prev) => prev.map((s) => ({ ...s, status: "idle" as const })));

      // Initial system log
      addLog("system", `Initializing search for "${query}"...`);
      await new Promise((r) => setTimeout(r, 500));

      // Simulate API connection
      addLog("info", "Connecting to Mino API gateway...");
      await new Promise((r) => setTimeout(r, 800));
      addLog("success", "API connection established");

      // HuggingFace
      updateSourceStatus("HuggingFace", "connecting");
      addLog("info", "Navigating to HuggingFace Open LLM Leaderboard...");
      await new Promise((r) => setTimeout(r, 1200));
      updateSourceStatus("HuggingFace", "fetching");
      addLog("info", "Detected Gradio table component");
      addLog("info", "Scanning for model: " + query);
      await new Promise((r) => setTimeout(r, 1500));
      updateSourceStatus("HuggingFace", "success");
      addLog("success", `Found ${query} on HuggingFace (#2 ranked)`);

      // LMSYS
      updateSourceStatus("LMSYS Arena", "connecting");
      addLog("info", "Connecting to LMSYS Chatbot Arena...");
      await new Promise((r) => setTimeout(r, 1000));
      updateSourceStatus("LMSYS Arena", "fetching");
      addLog("info", "Parsing ELO rankings table...");
      await new Promise((r) => setTimeout(r, 1200));
      updateSourceStatus("LMSYS Arena", "success");
      addLog("success", "Retrieved ELO score: 1287");

      // PapersWithCode
      updateSourceStatus("PapersWithCode", "connecting");
      addLog("info", "Querying PapersWithCode benchmarks...");
      await new Promise((r) => setTimeout(r, 800));
      updateSourceStatus("PapersWithCode", "fetching");
      addLog("info", "Aggregating benchmark results...");
      await new Promise((r) => setTimeout(r, 1400));
      updateSourceStatus("PapersWithCode", "success");
      addLog("success", "Compiled 3 benchmark scores");

      // Generate mock results
      addLog("system", "Compiling final results...");
      await new Promise((r) => setTimeout(r, 600));

      const mockModels: ModelRanking[] = [
        { rank: 1, name: "GPT-4o", score: 92.4, change: "same", source: "OpenAI" },
        { rank: 2, name: query, score: 89.7, change: "up", source: "Meta" },
        { rank: 3, name: "Claude 3.5 Sonnet", score: 88.9, change: "down", source: "Anthropic" },
        { rank: 4, name: "Gemini 1.5 Pro", score: 87.2, change: "same", source: "Google" },
        { rank: 5, name: "Mistral Large", score: 84.6, change: "up", source: "Mistral AI" },
      ];

      const mockBenchmarks: BenchmarkData[] = [
        { name: "MMLU", score: 86.8, maxScore: 100 },
        { name: "GSM8K", score: 92.3, maxScore: 100 },
        { name: "HumanEval", score: 81.5, maxScore: 100 },
        { name: "BBH", score: 78.4, maxScore: 100 },
        { name: "MATH", score: 64.2, maxScore: 100 },
      ];

      setTopModels(mockModels);
      setBenchmarks(mockBenchmarks);

      addLog("success", `Search complete. Found ${mockModels.length} models.`);
      addLog("system", "Ready for next query.");

      setIsSearching(false);
    },
    [addLog, updateSourceStatus]
  );

  const handleSearch = (query: string) => {
    simulateSearch(query);
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
        {/* Search Section */}
        <section className="mb-8">
          <SearchCommand onSearch={handleSearch} isSearching={isSearching} />
        </section>

        {/* Bento Grid Layout */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-4 auto-rows-min">
          {/* Terminal Feed - Spans 8 columns on large screens */}
          <div className="lg:col-span-8 min-h-[350px]">
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

          {/* Benchmark Chart - Spans 8 columns on large screens */}
          <div className="lg:col-span-8 min-h-[400px]">
            <BenchmarkChart
              data={benchmarks}
              modelName={searchedModel}
              isLoading={isSearching}
            />
          </div>
        </section>
      </main>

      {/* Model Detail Modal */}
      <ModelDetailPanel
        model={selectedModel}
        isVisible={showModelDetail}
        onClose={() => setShowModelDetail(false)}
      />
    </div>
  );
};

export default Index;
