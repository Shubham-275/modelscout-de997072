import { useEffect, useRef } from "react";
import { Terminal, ChevronRight } from "lucide-react";

interface LogEntry {
  id: string;
  timestamp: Date;
  type: "info" | "success" | "warning" | "error" | "system";
  message: string;
}

interface TerminalFeedProps {
  logs: LogEntry[];
  isActive: boolean;
}

const TerminalFeed = ({ logs, isActive }: TerminalFeedProps) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  const getTypeColor = (type: LogEntry["type"]) => {
    switch (type) {
      case "success":
        return "text-secondary";
      case "warning":
        return "text-warning";
      case "error":
        return "text-destructive";
      case "system":
        return "text-primary";
      default:
        return "text-muted-foreground";
    }
  };

  const getTypePrefix = (type: LogEntry["type"]) => {
    switch (type) {
      case "success":
        return "[✓]";
      case "warning":
        return "[!]";
      case "error":
        return "[✗]";
      case "system":
        return "[SYS]";
      default:
        return "[→]";
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  return (
    <div className="bento-card h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-primary" />
          <h3 className="font-mono text-sm font-semibold text-foreground">
            LIVE FEED
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <div
            className={`status-dot ${
              isActive ? "status-dot-online" : "status-dot-offline"
            }`}
          />
          <span className="text-xs font-mono text-muted-foreground">
            {isActive ? "STREAMING" : "IDLE"}
          </span>
        </div>
      </div>

      {/* Terminal content */}
      <div
        ref={containerRef}
        className="
          flex-1 mt-4 p-4 rounded-lg overflow-y-auto
          terminal-container scanlines relative custom-scrollbar
        "
      >
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <Terminal className="w-8 h-8 mb-2 opacity-50" />
            <p className="font-mono text-sm">Awaiting search query...</p>
          </div>
        ) : (
          <div className="space-y-1.5 font-mono text-xs">
            {logs.map((log, index) => (
              <div
                key={log.id}
                className="flex items-start gap-2 slide-up"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <span className="text-muted-foreground/60 flex-shrink-0">
                  {formatTime(log.timestamp)}
                </span>
                <span className={`flex-shrink-0 ${getTypeColor(log.type)}`}>
                  {getTypePrefix(log.type)}
                </span>
                <span className={getTypeColor(log.type)}>{log.message}</span>
              </div>
            ))}
            {isActive && (
              <div className="flex items-center gap-2 text-primary">
                <ChevronRight className="w-3 h-3 animate-pulse" />
                <span className="typing-cursor">Processing</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TerminalFeed;
