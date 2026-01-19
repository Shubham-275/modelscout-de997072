import { useState, useRef, useEffect } from "react";
import { Search, Radar, Zap } from "lucide-react";

interface SearchCommandProps {
  onSearch: (query: string) => void;
  isSearching: boolean;
}

const SearchCommand = ({ onSearch, isSearching }: SearchCommandProps) => {
  const [query, setQuery] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isSearching) {
      onSearch(query.trim());
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "/" && !isFocused) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFocused]);

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit}>
        <div
          className={`
            relative flex items-center gap-3 px-5 py-4 
            bg-card border rounded-xl transition-all duration-300
            ${isFocused 
              ? "border-primary glow-cyber" 
              : "border-border hover:border-primary/50"
            }
          `}
        >
          {/* Radar icon with animation */}
          <div className="flex-shrink-0">
            <div className={`relative ${isSearching ? "animate-spin" : ""}`}>
              <Radar className="w-5 h-5 text-primary" style={{ animationDuration: "2s" }} />
            </div>
          </div>

          {/* Input field */}
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Enter model name (e.g., Llama-3.1-70b)"
            disabled={isSearching}
            className="
              flex-1 bg-transparent text-foreground placeholder:text-muted-foreground
              font-mono text-sm outline-none disabled:opacity-50
            "
          />

          {/* Keyboard hint */}
          {!isFocused && !query && (
            <kbd className="hidden sm:flex items-center gap-1 px-2 py-1 text-xs font-mono text-muted-foreground bg-muted rounded">
              <span>/</span>
            </kbd>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={!query.trim() || isSearching}
            className="
              flex items-center gap-2 px-4 py-2 rounded-lg
              bg-primary text-primary-foreground font-medium text-sm
              hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed
              transition-all duration-200
            "
          >
            {isSearching ? (
              <>
                <Zap className="w-4 h-4 animate-pulse" />
                <span className="hidden sm:inline">Sniping...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span className="hidden sm:inline">Search</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Hint text */}
      <p className="mt-3 text-center text-xs text-muted-foreground">
        Search across HuggingFace, LMSYS Arena, and PapersWithCode leaderboards
      </p>
    </div>
  );
};

export default SearchCommand;
