import { useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import DashboardHeader from "@/components/DashboardHeader";
import ModelComparisonSelector from "@/components/ModelComparisonSelector";
import ComparisonResults from "@/components/ComparisonResults";
import TerminalFeed from "@/components/TerminalFeed";
import { useModelComparison } from "@/hooks/useModelComparison";
import { Button } from "@/components/ui/button";

interface LogEntry {
    id: string;
    timestamp: Date;
    type: "info" | "success" | "warning" | "error" | "system";
    message: string;
}

const ComparePage = () => {
    const {
        modelA,
        modelB,
        logs: streamLogs,
        isLoading,
        error,
        modelAName,
        modelBName,
        compareModels,
        cancelComparison,
        reset,
    } = useModelComparison();

    // Transform stream logs to the format expected by TerminalFeed
    const terminalLogs: LogEntry[] = streamLogs.map((log, idx) => ({
        id: `${idx}-${log.timestamp}`,
        timestamp: new Date(log.timestamp),
        type: log.type === 'error' ? 'error'
            : log.type === 'complete' || log.type === 'done' ? 'success'
                : log.type === 'system' ? 'system'
                    : 'info',
        message: typeof log.data === 'string' ? log.data : JSON.stringify(log.data),
    }));

    const handleCompare = (a: string, b: string) => {
        compareModels(a, b);
    };

    return (
        <div className="min-h-screen bg-background grid-pattern">
            <DashboardHeader />

            <main className="container mx-auto px-4 py-8">
                {/* Back Navigation */}
                <div className="mb-6">
                    <Link to="/">
                        <Button variant="ghost" size="sm" className="font-mono text-muted-foreground hover:text-foreground">
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Back to Dashboard
                        </Button>
                    </Link>
                </div>

                {/* Page Title */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-foreground mb-2">
                        Model Comparison
                    </h1>
                    <p className="text-muted-foreground font-mono text-sm">
                        Compare AI models side-by-side across multiple benchmarks
                    </p>
                </div>

                {/* Bento Grid Layout */}
                <section className="grid grid-cols-1 lg:grid-cols-12 gap-4 auto-rows-min">
                    {/* Comparison Selector - Full Width */}
                    <div className="lg:col-span-12">
                        <ModelComparisonSelector
                            onCompare={handleCompare}
                            isLoading={isLoading}
                            onCancel={cancelComparison}
                        />
                    </div>

                    {/* Terminal Feed - 5 columns */}
                    <div className="lg:col-span-5 min-h-[400px]">
                        <TerminalFeed logs={terminalLogs} isActive={isLoading} />
                    </div>

                    {/* Comparison Results - 7 columns */}
                    <div className="lg:col-span-7 min-h-[400px]">
                        <ComparisonResults
                            modelAName={modelAName}
                            modelBName={modelBName}
                            modelAResults={modelA}
                            modelBResults={modelB}
                            isLoading={isLoading}
                        />
                    </div>
                </section>

                {/* Error Display */}
                {error && (
                    <div className="mt-4 p-4 bg-destructive/10 border border-destructive/30 rounded-lg">
                        <p className="text-destructive font-mono text-sm">{error}</p>
                    </div>
                )}
            </main>
        </div>
    );
};

export default ComparePage;
