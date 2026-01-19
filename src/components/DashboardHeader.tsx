import { Radar, Activity, Database, History } from "lucide-react";

interface DashboardHeaderProps {
  onShowHistory?: () => void;
}

const DashboardHeader = ({ onShowHistory }: DashboardHeaderProps) => {
  return (
    <header className="w-full border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and title */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 rounded-lg blur-lg" />
              <div className="relative bg-card border border-primary/30 rounded-lg p-2">
                <Radar className="w-6 h-6 text-primary" />
              </div>
            </div>
            <div>
              <h1 className="font-mono text-xl font-bold text-foreground tracking-tight">
                BENCHMARK <span className="text-primary">RADAR</span>
              </h1>
              <p className="text-xs text-muted-foreground font-mono">
                AI Model Intelligence Dashboard
              </p>
            </div>
          </div>

          {/* Status indicators */}
          <div className="hidden md:flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-secondary" />
              <span className="text-xs font-mono text-muted-foreground">
                SYSTEM ONLINE
              </span>
              <div className="w-2 h-2 rounded-full bg-secondary animate-pulse-glow" />
            </div>
            
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-primary" />
              <span className="text-xs font-mono text-muted-foreground">
                CLOUD CONNECTED
              </span>
            </div>

            {onShowHistory && (
              <button
                onClick={onShowHistory}
                className="
                  flex items-center gap-2 px-3 py-1.5 rounded-lg
                  border border-border hover:border-primary/50
                  bg-muted/30 hover:bg-muted/50
                  transition-all duration-200
                "
              >
                <History className="w-4 h-4 text-muted-foreground" />
                <span className="text-xs font-mono text-muted-foreground">
                  HISTORY
                </span>
              </button>
            )}
          </div>

          {/* Mobile status dot */}
          <div className="flex md:hidden items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-secondary animate-pulse-glow" />
            <span className="text-xs font-mono text-muted-foreground">LIVE</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default DashboardHeader;
