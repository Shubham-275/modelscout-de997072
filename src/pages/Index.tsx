import { useState, useCallback, useRef } from "react";
import DashboardHeader from "@/components/DashboardHeader";
import SearchCommand from "@/components/SearchCommand";
import TerminalFeed from "@/components/TerminalFeed";
import TopModelsCard from "@/components/TopModelsCard";
import BenchmarkChart from "@/components/BenchmarkChart";
import SourceStatusCard from "@/components/SourceStatusCard";
import ModelDetailPanel from "@/components/ModelDetailPanel";
import { supabase } from "@/integrations/supabase/client";

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
  const abortControllerRef = useRef<AbortController | null>(null);

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

  const parseMinoEvent = useCallback((data: string, query: string) => {
    try {
      const parsed = JSON.parse(data);
      
      // Handle different event types from Mino
      if (parsed.type === 'log') {
        const message = parsed.message || '';
        
        // Detect source status from log messages
        if (message.toLowerCase().includes('huggingface') || message.toLowerCase().includes('hf.co')) {
          if (message.includes('navigating') || message.includes('connecting')) {
            updateSourceStatus("HuggingFace", "connecting");
          } else if (message.includes('fetching') || message.includes('loading')) {
            updateSourceStatus("HuggingFace", "fetching");
          } else if (message.includes('found') || message.includes('success')) {
            updateSourceStatus("HuggingFace", "success");
          }
        }
        if (message.toLowerCase().includes('lmsys') || message.toLowerCase().includes('arena')) {
          if (message.includes('navigating') || message.includes('connecting')) {
            updateSourceStatus("LMSYS Arena", "connecting");
          } else if (message.includes('fetching') || message.includes('loading')) {
            updateSourceStatus("LMSYS Arena", "fetching");
          } else if (message.includes('found') || message.includes('success')) {
            updateSourceStatus("LMSYS Arena", "success");
          }
        }
        if (message.toLowerCase().includes('paperswithcode') || message.toLowerCase().includes('pwc')) {
          if (message.includes('navigating') || message.includes('connecting')) {
            updateSourceStatus("PapersWithCode", "connecting");
          } else if (message.includes('fetching') || message.includes('loading')) {
            updateSourceStatus("PapersWithCode", "fetching");
          } else if (message.includes('found') || message.includes('success')) {
            updateSourceStatus("PapersWithCode", "success");
          }
        }
        
        // Determine log type from message content
        let logType: LogEntry["type"] = "info";
        if (message.includes('error') || message.includes('failed')) {
          logType = "error";
        } else if (message.includes('success') || message.includes('found') || message.includes('complete')) {
          logType = "success";
        } else if (message.includes('warning')) {
          logType = "warning";
        }
        
        addLog(logType, message);
      } else if (parsed.type === 'result' || parsed.type === 'data') {
        // Handle final results
        const results = parsed.data || parsed.results || [];
        if (Array.isArray(results) && results.length > 0) {
          const models: ModelRanking[] = results.map((r: any, idx: number) => ({
            rank: r.rank || idx + 1,
            name: r.model || query,
            score: r.score || 0,
            change: "same" as const,
            source: r.source || "Unknown",
          }));
          setTopModels(models);

          // Extract benchmarks from secondary metrics
          const firstResult = results[0];
          if (firstResult?.secondary_metrics) {
            const benchmarkData: BenchmarkData[] = Object.entries(firstResult.secondary_metrics).map(
              ([name, score]) => ({
                name,
                score: Number(score) || 0,
                maxScore: 100,
              })
            );
            setBenchmarks(benchmarkData);
          }
          
          addLog("success", `Received ${results.length} model results`);
        }
      } else if (parsed.type === 'done') {
        addLog("system", "Search complete. Ready for next query.");
      } else if (parsed.type === 'error') {
        addLog("error", parsed.message || "An error occurred");
      }
    } catch {
      // If not JSON, treat as plain text log
      if (data.trim()) {
        addLog("info", data);
      }
    }
  }, [addLog, updateSourceStatus]);

  const searchWithMinoAPI = useCallback(
    async (query: string) => {
      setIsSearching(true);
      setSearchedModel(query);
      setLogs([]);
      setTopModels([]);
      setBenchmarks([]);

      // Reset sources
      setSources((prev) => prev.map((s) => ({ ...s, status: "idle" as const })));

      // Cancel any existing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      addLog("system", `Initializing search for "${query}"...`);
      addLog("info", "Connecting to Mino API gateway...");

      try {
        const response = await fetch(
          `https://xctdxbrwsdyazhpybqhk.supabase.co/functions/v1/mino-proxy`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token || ''}`,
            },
            body: JSON.stringify({
              model_name: query,
              sources: ['HuggingFace', 'LMSYS', 'PapersWithCode'],
            }),
            signal: abortControllerRef.current.signal,
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
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

      } catch (error: any) {
        if (error.name === 'AbortError') {
          addLog("warning", "Search cancelled");
        } else {
          console.error('Mino API error:', error);
          addLog("error", `API Error: ${error.message}`);
          
          // Mark all sources as error
          setSources((prev) => prev.map((s) => ({ ...s, status: "error" as const })));
        }
      } finally {
        setIsSearching(false);
      }
    },
    [addLog, parseMinoEvent]
  );

  const handleSearch = (query: string) => {
    searchWithMinoAPI(query);
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
