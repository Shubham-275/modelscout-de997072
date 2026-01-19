import { X, ExternalLink, Copy, Check, Layers } from "lucide-react";
import { useState } from "react";

interface ModelMetrics {
  rank: number;
  score: number;
  elo?: number;
  mmlu?: number;
  coding?: number;
}

interface ModelDetail {
  name: string;
  source: string;
  metrics: ModelMetrics;
  secondaryMetrics?: Record<string, number>;
}

interface ModelDetailPanelProps {
  model: ModelDetail | null;
  onClose: () => void;
  isVisible: boolean;
}

const ModelDetailPanel = ({ model, onClose, isVisible }: ModelDetailPanelProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (model) {
      navigator.clipboard.writeText(JSON.stringify(model, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isVisible || !model) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
      <div
        className="
          w-full max-w-lg bento-card border-primary/30
          fade-in overflow-hidden
        "
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-primary" />
            <h2 className="font-mono text-lg font-bold text-foreground">
              Model Details
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-muted transition-colors"
          >
            <X className="w-5 h-5 text-muted-foreground" />
          </button>
        </div>

        {/* Content */}
        <div className="mt-4 space-y-4">
          {/* Model name */}
          <div>
            <label className="text-xs font-mono text-muted-foreground uppercase">
              Model Name
            </label>
            <p className="mt-1 font-mono text-lg text-primary font-semibold">
              {model.name}
            </p>
          </div>

          {/* Source */}
          <div>
            <label className="text-xs font-mono text-muted-foreground uppercase">
              Source
            </label>
            <p className="mt-1 font-mono text-sm text-foreground flex items-center gap-2">
              {model.source}
              <ExternalLink className="w-3 h-3 text-muted-foreground" />
            </p>
          </div>

          {/* Primary metrics */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-muted/30">
              <label className="text-xs font-mono text-muted-foreground uppercase">
                Global Rank
              </label>
              <p className="mt-1 font-mono text-2xl text-warning font-bold">
                #{model.metrics.rank}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-muted/30">
              <label className="text-xs font-mono text-muted-foreground uppercase">
                Average Score
              </label>
              <p className="mt-1 font-mono text-2xl text-primary font-bold">
                {model.metrics.score.toFixed(1)}
              </p>
            </div>
          </div>

          {/* Secondary metrics */}
          {model.secondaryMetrics && Object.keys(model.secondaryMetrics).length > 0 && (
            <div>
              <label className="text-xs font-mono text-muted-foreground uppercase mb-2 block">
                Benchmark Scores
              </label>
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(model.secondaryMetrics).map(([key, value]) => (
                  <div key={key} className="p-2 rounded-lg bg-muted/20 border border-border">
                    <p className="text-[10px] font-mono text-muted-foreground uppercase">
                      {key}
                    </p>
                    <p className="font-mono text-sm text-secondary font-semibold">
                      {value.toFixed(1)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="mt-6 pt-4 border-t border-border flex gap-3">
          <button
            onClick={handleCopy}
            className="
              flex-1 flex items-center justify-center gap-2 px-4 py-2
              rounded-lg border border-border hover:border-primary/50
              bg-muted/30 hover:bg-muted/50
              text-sm font-mono text-muted-foreground
              transition-all duration-200
            "
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-secondary" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy JSON
              </>
            )}
          </button>
          <button
            onClick={onClose}
            className="
              flex-1 flex items-center justify-center gap-2 px-4 py-2
              rounded-lg bg-primary text-primary-foreground
              text-sm font-mono font-medium
              hover:bg-primary/90 transition-all duration-200
            "
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModelDetailPanel;
