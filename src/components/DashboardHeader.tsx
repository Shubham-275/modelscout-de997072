import { Radar, History, Search, GitCompare, BarChart3 } from "lucide-react";
import { NavLink } from "react-router-dom";

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
                MODEL <span className="text-primary">SCOUT</span>
              </h1>
              <p className="text-xs text-muted-foreground font-mono">
                AI Model Benchmark Radar
              </p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-1 bg-secondary/5 rounded-lg p-1 border border-border/50">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center gap-2 ${isActive
                  ? "bg-primary/20 text-primary shadow-[0_0_10px_rgba(6,182,212,0.2)]"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                }`
              }
            >
              <Search className="w-4 h-4" />
              Find a Model
            </NavLink>
            <NavLink
              to="/compare"
              className={({ isActive }) =>
                `px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center gap-2 ${isActive
                  ? "bg-primary/20 text-primary shadow-[0_0_10px_rgba(6,182,212,0.2)]"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                }`
              }
            >
              <GitCompare className="w-4 h-4" />
              Compare Two
            </NavLink>
            <NavLink
              to="/benchmarks"
              className={({ isActive }) =>
                `px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center gap-2 ${isActive
                  ? "bg-primary/20 text-primary shadow-[0_0_10px_rgba(6,182,212,0.2)]"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                }`
              }
            >
              <BarChart3 className="w-4 h-4" />
              Explore Data
            </NavLink>
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-4">
            {onShowHistory && (
              <button
                onClick={onShowHistory}
                className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border hover:border-primary/50 bg-muted/30 hover:bg-muted/50 transition-all duration-200"
              >
                <History className="w-4 h-4 text-muted-foreground" />
                <span className="text-xs font-mono text-muted-foreground">
                  HISTORY
                </span>
              </button>
            )}

            {/* Live Indicator */}
            <div className="flex items-center gap-2 px-2 py-1 bg-secondary/10 rounded-full border border-secondary/20">
              <div className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse-glow" />
              <span className="text-[10px] font-mono text-secondary tracking-wider">ONLINE</span>
            </div>
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
