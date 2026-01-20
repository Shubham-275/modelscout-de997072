import { Globe, CheckCircle2, Loader2, XCircle, Clock } from "lucide-react";

interface SourceStatus {
  name: string;
  url: string;
  status: "idle" | "connecting" | "fetching" | "success" | "error" | "not_found" | "partial";
  lastUpdate?: Date;
}

interface SourceStatusCardProps {
  sources: SourceStatus[];
}

const SourceStatusCard = ({ sources }: SourceStatusCardProps) => {
  const getStatusIcon = (status: SourceStatus["status"]) => {
    switch (status) {
      case "connecting":
      case "fetching":
        return <Loader2 className="w-4 h-4 text-primary animate-spin" />;
      case "success":
        return <CheckCircle2 className="w-4 h-4 text-secondary" />;
      case "not_found":
        return <XCircle className="w-4 h-4 text-muted-foreground" />;
      case "partial":
        return <Loader2 className="w-4 h-4 text-warning" />;
      case "error":
        return <XCircle className="w-4 h-4 text-destructive" />;
      default:
        return <Clock className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const getStatusText = (status: SourceStatus["status"]) => {
    switch (status) {
      case "connecting":
        return "Connecting...";
      case "fetching":
        return "Extracting...";
      case "success":
        return "Complete";
      case "not_found":
        return "No Data Found";
      case "partial":
        return "Insufficient Coverage";
      case "error":
        return "Failed";
      default:
        return "Idle";
    }
  };

  const getStatusColor = (status: SourceStatus["status"]) => {
    switch (status) {
      case "connecting":
      case "fetching":
        return "border-primary/50 bg-primary/5";
      case "success":
        return "border-secondary/50 bg-secondary/5";
      case "not_found":
        return "border-muted/50 bg-muted/5";
      case "partial":
        return "border-warning/50 bg-warning/5";
      case "error":
        return "border-destructive/50 bg-destructive/5";
      default:
        return "border-border bg-muted/20";
    }
  };

  const formatTime = (date?: Date) => {
    if (!date) return "--:--:--";
    return date.toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  return (
    <div className="bento-card h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-secondary" />
          <h3 className="font-mono text-sm font-semibold text-foreground">
            SOURCE STATUS
          </h3>
        </div>
        <span className="text-xs font-mono text-muted-foreground">
          LIVE CONNECTIONS
        </span>
      </div>

      {/* Sources list */}
      <div className="flex-1 mt-4 space-y-3">
        {sources.map((source) => (
          <div
            key={source.name}
            className={`
              flex items-center gap-4 p-4 rounded-lg border
              transition-all duration-300
              ${getStatusColor(source.status)}
            `}
          >
            {/* Status icon */}
            <div className="flex-shrink-0">{getStatusIcon(source.status)}</div>

            {/* Source info */}
            <div className="flex-1 min-w-0">
              <p className="font-mono text-sm font-medium text-foreground">
                {source.name}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {source.url}
              </p>
            </div>

            {/* Status badge */}
            <div className="flex flex-col items-end flex-shrink-0">
              <span
                className={`
                  text-xs font-mono font-medium
                  ${source.status === "success"
                    ? "text-secondary"
                    : source.status === "error"
                      ? "text-destructive"
                      : source.status === "connecting" ||
                        source.status === "fetching"
                        ? "text-primary"
                        : "text-muted-foreground"
                  }
                `}
              >
                {getStatusText(source.status)}
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">
                {formatTime(source.lastUpdate)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Summary footer */}
      <div className="mt-4 pt-4 border-t border-border">
        <div className="flex items-center justify-between text-xs font-mono text-muted-foreground">
          <span>
            {sources.filter((s) => s.status === "success").length}/{sources.length} sources active
          </span>
          <span>
            {sources.some(
              (s) => s.status === "connecting" || s.status === "fetching"
            )
              ? "Syncing..."
              : "All systems nominal"}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SourceStatusCard;
