/**
 * Multimodal Recommendation Component
 * Handles image, video, voice, and 3D model recommendations
 */

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ChevronDown, Image, Video, Mic, Box, Info, CheckCircle2, XCircle } from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface MultimodalRequirements {
    use_case: string;
    modality: 'image' | 'video' | 'voice' | '3d';
    priorities: {
        quality: string;
        cost: string;
        speed: string;
    };
    monthly_budget_usd?: number;
    expected_usage_per_month?: number;
    image_requirements?: {
        min_resolution?: number;
        needs_safety_filter?: boolean;
        needs_style_diversity?: boolean;
    };
    video_requirements?: {
        min_duration_sec?: number;
        min_resolution?: string;
    };
    voice_requirements?: {
        needs_voice_cloning?: boolean;
        languages?: string[];
        needs_emotions?: boolean;
    };
    three_d_requirements?: {
        needs_rigging?: boolean;
        min_polygons?: number;
        needs_optimization?: boolean;
    };
}

interface MultimodalRecommendation {
    recommended_model: string;
    provider: string;
    modality: string;
    reasoning: string;
    score: number;
    alternatives: Array<{
        model: string;
        score: number;
        reasons: string[];
    }>;
    benchmarks: any;
    pricing: any;
    confidence: string;
}

const MODALITY_CONFIG = {
    image: {
        icon: Image,
        label: "Image Generation",
        color: "text-blue-400",
        bgColor: "bg-blue-500/10",
        borderColor: "border-blue-500/30",
        usageUnit: "images",
        usageOptions: [
            { value: 100, label: "100 images/month (hobby)" },
            { value: 1000, label: "1,000 images/month (small business)" },
            { value: 10000, label: "10,000 images/month (production)" }
        ]
    },
    video: {
        icon: Video,
        label: "Video Generation",
        color: "text-purple-400",
        bgColor: "bg-purple-500/10",
        borderColor: "border-purple-500/30",
        usageUnit: "seconds",
        usageOptions: [
            { value: 60, label: "60 seconds/month (testing)" },
            { value: 300, label: "300 seconds/month (regular)" },
            { value: 1800, label: "1,800 seconds/month (heavy)" }
        ]
    },
    voice: {
        icon: Mic,
        label: "Voice/Audio",
        color: "text-green-400",
        bgColor: "bg-green-500/10",
        borderColor: "border-green-500/30",
        usageUnit: "characters",
        usageOptions: [
            { value: 10000, label: "10K characters/month (light)" },
            { value: 100000, label: "100K characters/month (moderate)" },
            { value: 1000000, label: "1M characters/month (heavy)" }
        ]
    },
    "3d": {
        icon: Box,
        label: "3D Generation",
        color: "text-orange-400",
        bgColor: "bg-orange-500/10",
        borderColor: "border-orange-500/30",
        usageUnit: "models",
        usageOptions: [
            { value: 10, label: "10 models/month (testing)" },
            { value: 100, label: "100 models/month (regular)" },
            { value: 500, label: "500 models/month (production)" }
        ]
    }
};

export const MultimodalRecommendationForm = () => {
    const [modality, setModality] = useState<'image' | 'video' | 'voice' | '3d'>('image');
    const [useCase, setUseCase] = useState("");
    const [qualityPriority, setQualityPriority] = useState("high");
    const [costPriority, setCostPriority] = useState("medium");
    const [speedPriority, setSpeedPriority] = useState("medium");
    const [monthlyBudget, setMonthlyBudget] = useState(100);
    const [expectedUsage, setExpectedUsage] = useState(1000);

    // Image-specific
    const [minResolution, setMinResolution] = useState(1024);
    const [needsSafetyFilter, setNeedsSafetyFilter] = useState(true);
    const [needsStyleDiversity, setNeedsStyleDiversity] = useState(false);

    // Video-specific
    const [minDuration, setMinDuration] = useState(10);
    const [videoResolution, setVideoResolution] = useState("1080p");

    // Voice-specific
    const [needsVoiceCloning, setNeedsVoiceCloning] = useState(false);
    const [needsEmotions, setNeedsEmotions] = useState(true);
    const [languages, setLanguages] = useState<string[]>(["en"]);

    // 3D-specific
    const [needsRigging, setNeedsRigging] = useState(false);
    const [minPolygons, setMinPolygons] = useState(50000);
    const [needsOptimization, setNeedsOptimization] = useState(true);

    const [isLoading, setIsLoading] = useState(false);
    const [recommendation, setRecommendation] = useState<MultimodalRecommendation | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showAlternatives, setShowAlternatives] = useState(false);

    const config = MODALITY_CONFIG[modality];
    const ModalityIcon = config.icon;

    const handleGetRecommendation = async () => {
        if (!useCase.trim()) {
            setError("Please describe your use case");
            return;
        }

        setIsLoading(true);
        setError(null);

        const requirements: MultimodalRequirements = {
            use_case: useCase,
            modality,
            priorities: {
                quality: qualityPriority,
                cost: costPriority,
                speed: speedPriority
            },
            monthly_budget_usd: monthlyBudget,
            expected_usage_per_month: expectedUsage
        };

        // Add modality-specific requirements
        if (modality === 'image') {
            requirements.image_requirements = {
                min_resolution: minResolution,
                needs_safety_filter: needsSafetyFilter,
                needs_style_diversity: needsStyleDiversity
            };
        } else if (modality === 'video') {
            requirements.video_requirements = {
                min_duration_sec: minDuration,
                min_resolution: videoResolution
            };
        } else if (modality === 'voice') {
            requirements.voice_requirements = {
                needs_voice_cloning: needsVoiceCloning,
                languages,
                needs_emotions: needsEmotions
            };
        } else if (modality === '3d') {
            requirements.three_d_requirements = {
                needs_rigging: needsRigging,
                min_polygons: minPolygons,
                needs_optimization: needsOptimization
            };
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/v2/analyst/recommend/multimodal`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requirements),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            setRecommendation(data.recommendation);
        } catch (err) {
            setError("Failed to get recommendation. Please try again.");
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Modality Selector */}
            <Card className="p-6 border border-primary/20 bg-card/50 backdrop-blur-sm">
                <h3 className="text-sm font-semibold mb-4 text-muted-foreground uppercase tracking-wider">
                    Select Model Type
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {(Object.keys(MODALITY_CONFIG) as Array<keyof typeof MODALITY_CONFIG>).map((key) => {
                        const cfg = MODALITY_CONFIG[key];
                        const Icon = cfg.icon;
                        const isSelected = modality === key;

                        return (
                            <button
                                key={key}
                                onClick={() => setModality(key)}
                                className={`p-4 rounded-lg border-2 transition-all ${isSelected
                                        ? `${cfg.borderColor} ${cfg.bgColor}`
                                        : 'border-border/50 bg-background/50 hover:bg-background/80'
                                    }`}
                            >
                                <Icon className={`w-6 h-6 mx-auto mb-2 ${isSelected ? cfg.color : 'text-muted-foreground'}`} />
                                <p className={`text-xs font-medium ${isSelected ? cfg.color : 'text-muted-foreground'}`}>
                                    {cfg.label}
                                </p>
                            </button>
                        );
                    })}
                </div>
            </Card>

            {/* Main Form */}
            <Card className="p-8 border border-primary/20 bg-card/50 backdrop-blur-sm">
                <div className="space-y-6">
                    {/* Use Case */}
                    <div>
                        <label className="text-sm font-medium mb-2 block text-muted-foreground">
                            What do you want to create? (1-2 lines)
                        </label>
                        <textarea
                            placeholder={`e.g., ${modality === 'image' ? 'Product images for e-commerce' :
                                    modality === 'video' ? 'Short marketing videos for social media' :
                                        modality === 'voice' ? 'Podcast narration with emotions' :
                                            'Game-ready 3D assets for Unity'
                                }`}
                            value={useCase}
                            onChange={(e) => setUseCase(e.target.value)}
                            rows={2}
                            className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground placeholder-muted-foreground/50 resize-none focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all font-mono text-sm"
                        />
                    </div>

                    {/* Priorities */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="text-sm font-medium mb-2 block text-muted-foreground">Quality</label>
                            <div className="relative">
                                <select
                                    value={qualityPriority}
                                    onChange={(e) => setQualityPriority(e.target.value)}
                                    className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-mono text-sm cursor-pointer"
                                >
                                    <option value="low">Low (basic)</option>
                                    <option value="medium">Medium (good)</option>
                                    <option value="high">High (best)</option>
                                </select>
                                <ChevronDown className="absolute right-3 top-3.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                            </div>
                        </div>

                        <div>
                            <label className="text-sm font-medium mb-2 block text-muted-foreground">Cost</label>
                            <div className="relative">
                                <select
                                    value={costPriority}
                                    onChange={(e) => setCostPriority(e.target.value)}
                                    className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-mono text-sm cursor-pointer"
                                >
                                    <option value="low">Low (minimize)</option>
                                    <option value="medium">Medium (balanced)</option>
                                    <option value="high">High (quality over cost)</option>
                                </select>
                                <ChevronDown className="absolute right-3 top-3.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                            </div>
                        </div>

                        <div>
                            <label className="text-sm font-medium mb-2 block text-muted-foreground">Speed</label>
                            <div className="relative">
                                <select
                                    value={speedPriority}
                                    onChange={(e) => setSpeedPriority(e.target.value)}
                                    className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-mono text-sm cursor-pointer"
                                >
                                    <option value="low">Low (can wait)</option>
                                    <option value="medium">Medium (normal)</option>
                                    <option value="high">High (fast needed)</option>
                                </select>
                                <ChevronDown className="absolute right-3 top-3.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                            </div>
                        </div>
                    </div>

                    {/* Modality-Specific Fields */}
                    {modality === 'image' && (
                        <div className={`p-4 rounded-lg border ${config.borderColor} ${config.bgColor} space-y-4`}>
                            <h4 className={`text-sm font-semibold ${config.color} flex items-center gap-2`}>
                                <Image className="w-4 h-4" />
                                Image-Specific Settings
                            </h4>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm font-medium mb-2 block text-muted-foreground">Min Resolution</label>
                                    <div className="relative">
                                        <select
                                            value={minResolution}
                                            onChange={(e) => setMinResolution(parseInt(e.target.value))}
                                            className="w-full px-4 py-2 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm cursor-pointer"
                                        >
                                            <option value={512}>512px (low)</option>
                                            <option value={1024}>1024px (standard)</option>
                                            <option value={2048}>2048px (high)</option>
                                        </select>
                                        <ChevronDown className="absolute right-3 top-2.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={needsSafetyFilter}
                                            onChange={(e) => setNeedsSafetyFilter(e.target.checked)}
                                            className="w-4 h-4 rounded border-border/50 bg-background/50 text-primary focus:ring-primary/50"
                                        />
                                        <span className="text-sm text-muted-foreground">Safety filter required</span>
                                    </label>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={needsStyleDiversity}
                                            onChange={(e) => setNeedsStyleDiversity(e.target.checked)}
                                            className="w-4 h-4 rounded border-border/50 bg-background/50 text-primary focus:ring-primary/50"
                                        />
                                        <span className="text-sm text-muted-foreground">Style diversity needed</span>
                                    </label>
                                </div>
                            </div>
                        </div>
                    )}

                    {modality === 'video' && (
                        <div className={`p-4 rounded-lg border ${config.borderColor} ${config.bgColor} space-y-4`}>
                            <h4 className={`text-sm font-semibold ${config.color} flex items-center gap-2`}>
                                <Video className="w-4 h-4" />
                                Video-Specific Settings
                            </h4>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm font-medium mb-2 block text-muted-foreground">Min Duration</label>
                                    <div className="relative">
                                        <select
                                            value={minDuration}
                                            onChange={(e) => setMinDuration(parseInt(e.target.value))}
                                            className="w-full px-4 py-2 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm cursor-pointer"
                                        >
                                            <option value={5}>5 seconds</option>
                                            <option value={10}>10 seconds</option>
                                            <option value={30}>30 seconds</option>
                                            <option value={60}>60 seconds</option>
                                        </select>
                                        <ChevronDown className="absolute right-3 top-2.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                                    </div>
                                </div>

                                <div>
                                    <label className="text-sm font-medium mb-2 block text-muted-foreground">Min Resolution</label>
                                    <div className="relative">
                                        <select
                                            value={videoResolution}
                                            onChange={(e) => setVideoResolution(e.target.value)}
                                            className="w-full px-4 py-2 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm cursor-pointer"
                                        >
                                            <option value="720p">720p (HD)</option>
                                            <option value="1080p">1080p (Full HD)</option>
                                            <option value="4k">4K (Ultra HD)</option>
                                        </select>
                                        <ChevronDown className="absolute right-3 top-2.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {modality === 'voice' && (
                        <div className={`p-4 rounded-lg border ${config.borderColor} ${config.bgColor} space-y-4`}>
                            <h4 className={`text-sm font-semibold ${config.color} flex items-center gap-2`}>
                                <Mic className="w-4 h-4" />
                                Voice-Specific Settings
                            </h4>

                            <div className="space-y-2">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={needsVoiceCloning}
                                        onChange={(e) => setNeedsVoiceCloning(e.target.checked)}
                                        className="w-4 h-4 rounded border-border/50 bg-background/50 text-primary focus:ring-primary/50"
                                    />
                                    <span className="text-sm text-muted-foreground">Voice cloning required</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={needsEmotions}
                                        onChange={(e) => setNeedsEmotions(e.target.checked)}
                                        className="w-4 h-4 rounded border-border/50 bg-background/50 text-primary focus:ring-primary/50"
                                    />
                                    <span className="text-sm text-muted-foreground">Emotional expression needed</span>
                                </label>
                            </div>
                        </div>
                    )}

                    {modality === '3d' && (
                        <div className={`p-4 rounded-lg border ${config.borderColor} ${config.bgColor} space-y-4`}>
                            <h4 className={`text-sm font-semibold ${config.color} flex items-center gap-2`}>
                                <Box className="w-4 h-4" />
                                3D-Specific Settings
                            </h4>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm font-medium mb-2 block text-muted-foreground">Min Polygons</label>
                                    <div className="relative">
                                        <select
                                            value={minPolygons}
                                            onChange={(e) => setMinPolygons(parseInt(e.target.value))}
                                            className="w-full px-4 py-2 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm cursor-pointer"
                                        >
                                            <option value={10000}>10K (low poly)</option>
                                            <option value={50000}>50K (medium)</option>
                                            <option value={100000}>100K (high detail)</option>
                                        </select>
                                        <ChevronDown className="absolute right-3 top-2.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={needsRigging}
                                            onChange={(e) => setNeedsRigging(e.target.checked)}
                                            className="w-4 h-4 rounded border-border/50 bg-background/50 text-primary focus:ring-primary/50"
                                        />
                                        <span className="text-sm text-muted-foreground">Rigging support</span>
                                    </label>
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={needsOptimization}
                                            onChange={(e) => setNeedsOptimization(e.target.checked)}
                                            className="w-4 h-4 rounded border-border/50 bg-background/50 text-primary focus:ring-primary/50"
                                        />
                                        <span className="text-sm text-muted-foreground">Game optimization</span>
                                    </label>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Budget */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <label className="text-sm font-medium text-muted-foreground">
                                Monthly Budget
                            </label>
                            <span className="font-mono text-xl text-primary font-bold">
                                ${monthlyBudget}
                            </span>
                        </div>
                        <input
                            type="range"
                            min="10"
                            max="1000"
                            step="10"
                            value={monthlyBudget}
                            onChange={(e) => setMonthlyBudget(parseInt(e.target.value))}
                            className="w-full h-2 bg-secondary/30 rounded-lg appearance-none cursor-pointer accent-primary"
                        />
                    </div>

                    {/* Expected Usage */}
                    <div>
                        <label className="text-sm font-medium mb-2 block text-muted-foreground">
                            Expected Usage ({config.usageUnit}/month)
                        </label>
                        <div className="relative">
                            <select
                                value={expectedUsage}
                                onChange={(e) => setExpectedUsage(parseInt(e.target.value))}
                                className="w-full px-4 py-3 border border-border/50 rounded-lg bg-background/50 text-foreground appearance-none focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-mono text-sm cursor-pointer"
                            >
                                {config.usageOptions.map(opt => (
                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                ))}
                            </select>
                            <ChevronDown className="absolute right-3 top-3.5 w-4 h-4 text-muted-foreground pointer-events-none" />
                        </div>
                    </div>

                    {/* Submit Button */}
                    <Button
                        onClick={handleGetRecommendation}
                        disabled={isLoading}
                        size="lg"
                        className="w-full font-bold text-lg h-14 bg-primary hover:bg-primary/90 shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] transition-all uppercase tracking-wider"
                    >
                        {isLoading ? (
                            <span className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-background rounded-full animate-bounce" />
                                Analyzing...
                            </span>
                        ) : `Get ${config.label} Recommendation`}
                    </Button>

                    {error && (
                        <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive text-sm flex items-center gap-2">
                            <span className="font-bold">Error:</span> {error}
                        </div>
                    )}
                </div>
            </Card>

            {/* Results */}
            {recommendation && (
                <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
                    <Card className={`p-8 border-2 ${config.borderColor} ${config.bgColor} backdrop-blur-md shadow-[0_0_30px_rgba(6,182,212,0.15)]`}>
                        <div className="flex flex-col md:flex-row md:items-start justify-between mb-6 gap-4">
                            <div>
                                <p className={`text-sm font-mono mb-2 flex items-center gap-2 ${config.color}`}>
                                    <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                                    RECOMMENDED {modality.toUpperCase()} MODEL
                                </p>
                                <h2 className="text-4xl md:text-5xl font-bold text-foreground tracking-tight">
                                    {recommendation.recommended_model}
                                </h2>
                                <div className="flex items-center gap-3 mt-3">
                                    <span className="text-sm text-muted-foreground">
                                        by {recommendation.provider}
                                    </span>
                                    <span className={`px-2 py-0.5 rounded text-xs font-mono uppercase ${recommendation.confidence === 'high'
                                            ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                                            : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                                        }`}>
                                        {recommendation.confidence} confidence
                                    </span>
                                    <span className={`px-2 py-0.5 rounded text-xs font-mono ${config.bgColor} ${config.color} border ${config.borderColor}`}>
                                        Score: {recommendation.score}/100
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Reasoning */}
                        <div className="mb-6 bg-secondary/5 rounded-lg p-5 border border-secondary/20">
                            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2 text-foreground">
                                <Info className="w-4 h-4 text-primary" />
                                Why this model fits your needs
                            </h3>
                            <p className="text-muted-foreground leading-relaxed text-sm md:text-base">
                                {recommendation.reasoning}
                            </p>
                        </div>

                        {/* Benchmarks */}
                        {recommendation.benchmarks && (
                            <div className="mb-6 grid grid-cols-2 md:grid-cols-4 gap-3">
                                {Object.entries(recommendation.benchmarks)
                                    .filter(([key]) => !['modality', 'strengths', 'weaknesses'].includes(key))
                                    .slice(0, 4)
                                    .map(([key, value]) => (
                                        <div key={key} className="bg-background/40 rounded-lg p-3 border border-border/50">
                                            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                                                {key.replace(/_/g, ' ')}
                                            </p>
                                            <p className="font-mono text-lg font-bold text-foreground">
                                                {typeof value === 'number' ? value : String(value)}
                                            </p>
                                        </div>
                                    ))}
                            </div>
                        )}

                        {/* Strengths & Weaknesses */}
                        {recommendation.benchmarks?.strengths && (
                            <div className="grid md:grid-cols-2 gap-4">
                                <div className="bg-green-500/5 rounded-lg p-4 border border-green-500/20">
                                    <h3 className="text-sm font-semibold text-green-400 mb-3 flex items-center gap-2">
                                        <CheckCircle2 className="w-4 h-4" /> Strengths
                                    </h3>
                                    <ul className="space-y-2">
                                        {recommendation.benchmarks.strengths.map((strength: string, idx: number) => (
                                            <li key={idx} className="text-sm text-foreground/90 flex items-start gap-2">
                                                <span className="text-green-400 mt-0.5">✓</span>
                                                <span>{strength}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                {recommendation.benchmarks?.weaknesses && (
                                    <div className="bg-orange-500/5 rounded-lg p-4 border border-orange-500/20">
                                        <h3 className="text-sm font-semibold text-orange-400 mb-3 flex items-center gap-2">
                                            <XCircle className="w-4 h-4" /> Limitations
                                        </h3>
                                        <ul className="space-y-2">
                                            {recommendation.benchmarks.weaknesses.map((weakness: string, idx: number) => (
                                                <li key={idx} className="text-sm text-foreground/90 flex items-start gap-2">
                                                    <span className="text-orange-400 mt-0.5">•</span>
                                                    <span>{weakness}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}
                    </Card>

                    {/* Alternatives */}
                    {recommendation.alternatives && recommendation.alternatives.length > 0 && (
                        <Card className="border border-border/50 bg-card/30">
                            <button
                                onClick={() => setShowAlternatives(!showAlternatives)}
                                className="w-full flex items-center justify-between p-4 text-sm font-semibold hover:bg-white/5 transition-colors"
                            >
                                <span className="flex items-center gap-2 text-muted-foreground">
                                    Alternative {config.label} Models
                                </span>
                                <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${showAlternatives ? 'rotate-180' : ''}`} />
                            </button>

                            {showAlternatives && (
                                <div className="p-4 pt-0 space-y-3">
                                    {recommendation.alternatives.map((alt, idx) => (
                                        <div key={idx} className="border-l-2 border-muted pl-4 py-1">
                                            <div className="flex items-center justify-between">
                                                <p className="font-bold text-sm text-foreground">{alt.model}</p>
                                                <span className="text-xs text-muted-foreground">Score: {alt.score}/100</span>
                                            </div>
                                            <ul className="mt-1 space-y-1">
                                                {alt.reasons.map((reason, ridx) => (
                                                    <li key={ridx} className="text-xs text-muted-foreground">
                                                        • {reason}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </Card>
                    )}
                </div>
            )}
        </div>
    );
};
