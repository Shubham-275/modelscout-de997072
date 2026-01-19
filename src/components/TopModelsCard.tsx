import { Trophy, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface ModelRanking {
  rank: number;
  name: string;
  score: number;
  change: "up" | "down" | "same";
  source: string;
}

interface TopModelsCardProps {
  models: ModelRanking[];
  isLoading: boolean;
}

const TopModelsCard = ({ models, isLoading }: TopModelsCardProps) => {
  const getTrendIcon = (change: ModelRanking["change"]) => {
    switch (change) {
      case "up":
        return <TrendingUp className="w-3 h-3 text-secondary" />;
      case "down":
        return <TrendingDown className="w-3 h-3 text-destructive" />;
      default:
        return <Minus className="w-3 h-3 text-muted-foreground" />;
    }
  };

  const getRankColor = (rank: number) => {
    switch (rank) {
      case 1:
        return "text-warning";
      case 2:
        return "text-muted-foreground";
      case 3:
        return "text-amber-muted";
      default:
        return "text-muted-foreground";
    }
  };

  return (
    <div className="bento-card h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Trophy className="w-4 h-4 text-warning" />
          <h3 className="font-mono text-sm font-semibold text-foreground">
            TOP MODELS
          </h3>
        </div>
        <span className="text-xs font-mono text-muted-foreground">
          GLOBAL RANKING
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 mt-4 overflow-y-auto custom-scrollbar">
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="flex items-center gap-3 p-3 rounded-lg bg-muted/30 animate-pulse"
              >
                <div className="w-8 h-8 rounded-full bg-muted" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-muted rounded w-3/4" />
                  <div className="h-3 bg-muted rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : models.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground py-8">
            <Trophy className="w-8 h-8 mb-2 opacity-50" />
            <p className="font-mono text-sm text-center">
              Search for a model to see rankings
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {models.map((model, index) => (
              <div
                key={`${model.name}-${index}`}
                className="
                  flex items-center gap-3 p-3 rounded-lg
                  bg-muted/20 hover:bg-muted/40 
                  border border-transparent hover:border-primary/20
                  transition-all duration-200 cursor-pointer
                "
              >
                {/* Rank badge */}
                <div
                  className={`
                    flex items-center justify-center w-8 h-8 rounded-full
                    font-mono font-bold text-sm
                    ${
                      model.rank === 1
                        ? "bg-warning/20 text-warning"
                        : model.rank <= 3
                        ? "bg-muted text-muted-foreground"
                        : "bg-muted/50 text-muted-foreground"
                    }
                  `}
                >
                  {model.rank}
                </div>

                {/* Model info */}
                <div className="flex-1 min-w-0">
                  <p className="font-mono text-sm font-medium text-foreground truncate">
                    {model.name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {model.source}
                  </p>
                </div>

                {/* Score and trend */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="font-mono text-sm font-semibold text-primary">
                    {model.score.toFixed(1)}
                  </span>
                  {getTrendIcon(model.change)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TopModelsCard;
