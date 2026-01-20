"""
Model Scout - Phase 2: Cost-Performance Frontier

FRONTIER DEFINITION:
Frontier charts visualize tradeoffs, NOT optimality.

AXES:
- X-axis: Cost (normalized)
- Y-axis: Capability (normalized)

NORMALIZATION SCOPE (MANDATORY):
Normalization is computed ONLY over the currently filtered model set.
This must be stated in UI tooltips.

CLARIFICATION:
- Frontier ≠ recommendation
- Frontier ≠ universal optimality
- Frontier ≠ ranking
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import math


@dataclass
class FrontierPoint:
    """
    A single point on the cost-performance frontier.
    """
    model_id: str
    
    # Raw values
    raw_cost: float       # e.g., $/1M tokens
    raw_capability: float  # e.g., average benchmark score
    
    # Normalized values (within current filter set)
    normalized_cost: float      # 0-1, higher = more expensive
    normalized_capability: float # 0-1, higher = more capable
    
    # Pareto optimality within the filtered set
    is_pareto_optimal: bool = False
    
    # Metadata
    cost_metric: str = "input_price"
    capability_metric: str = "average_score"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "raw": {
                "cost": self.raw_cost,
                "capability": self.raw_capability
            },
            "normalized": {
                "cost": round(self.normalized_cost, 4),
                "capability": round(self.normalized_capability, 4)
            },
            "is_pareto_optimal": self.is_pareto_optimal,
            "metrics": {
                "cost_metric": self.cost_metric,
                "capability_metric": self.capability_metric
            }
        }


@dataclass
class FrontierChart:
    """
    Complete frontier visualization data.
    
    MANDATORY DISCLOSURES:
    - Normalization scope is the filtered model set
    - Frontier does not imply recommendation
    """
    points: List[FrontierPoint]
    
    # Normalization parameters (for transparency)
    cost_min: float
    cost_max: float
    capability_min: float
    capability_max: float
    
    # Pareto frontier line
    pareto_frontier: List[str]  # model_ids on the frontier
    
    # Filter information
    models_in_set: int
    filter_description: str
    
    # Mandatory tooltips
    tooltips: Dict[str, str] = field(default_factory=lambda: {
        "x_axis": "Cost (normalized within current filter). 0 = cheapest in set, 1 = most expensive.",
        "y_axis": "Capability (normalized within current filter). 0 = lowest in set, 1 = highest.",
        "pareto": "Models where no other model in the set is both cheaper AND more capable.",
        "scope_warning": "Normalization is computed ONLY over the currently filtered model set. Adding or removing models will change normalized positions.",
        "disclaimer": "This frontier visualizes tradeoffs only. It does NOT recommend models or imply universal optimality."
    })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "points": [p.to_dict() for p in self.points],
            "normalization": {
                "cost_range": {"min": self.cost_min, "max": self.cost_max},
                "capability_range": {"min": self.capability_min, "max": self.capability_max},
                "scope": "filtered_model_set_only"
            },
            "pareto_frontier": self.pareto_frontier,
            "filter": {
                "models_in_set": self.models_in_set,
                "description": self.filter_description
            },
            "tooltips": self.tooltips,
            "warnings": [
                "Normalization scope: Current filter only",
                "Frontier ≠ recommendation",
                "Adding/removing models changes positions"
            ]
        }


def compute_frontier(
    model_data: Dict[str, Dict[str, float]],
    cost_metric: str = "input_price",
    capability_metric: str = "average_score",
    filter_description: str = "All models"
) -> FrontierChart:
    """
    Compute cost-performance frontier for a set of models.
    
    NORMALIZATION SCOPE: Only the models in model_data are used for normalization.
    
    Args:
        model_data: Dict of model_id -> {metric_name -> value}
        cost_metric: Metric to use for cost (x-axis)
        capability_metric: Metric to use for capability (y-axis)
        filter_description: Human-readable description of the filter applied
        
    Returns:
        FrontierChart with all points and Pareto frontier
    """
    # Extract raw values
    raw_points: List[Tuple[str, float, float]] = []
    
    for model_id, metrics in model_data.items():
        cost = metrics.get(cost_metric)
        capability = metrics.get(capability_metric)
        
        if cost is not None and capability is not None:
            raw_points.append((model_id, cost, capability))
    
    if not raw_points:
        return FrontierChart(
            points=[],
            cost_min=0, cost_max=0,
            capability_min=0, capability_max=0,
            pareto_frontier=[],
            models_in_set=0,
            filter_description=filter_description
        )
    
    # Compute normalization ranges (ONLY from this set)
    costs = [p[1] for p in raw_points]
    capabilities = [p[2] for p in raw_points]
    
    cost_min, cost_max = min(costs), max(costs)
    capability_min, capability_max = min(capabilities), max(capabilities)
    
    # Avoid division by zero
    cost_range = cost_max - cost_min if cost_max != cost_min else 1
    capability_range = capability_max - capability_min if capability_max != capability_min else 1
    
    # Create frontier points with normalization
    frontier_points: List[FrontierPoint] = []
    
    for model_id, raw_cost, raw_capability in raw_points:
        normalized_cost = (raw_cost - cost_min) / cost_range
        normalized_capability = (raw_capability - capability_min) / capability_range
        
        frontier_points.append(FrontierPoint(
            model_id=model_id,
            raw_cost=raw_cost,
            raw_capability=raw_capability,
            normalized_cost=normalized_cost,
            normalized_capability=normalized_capability,
            cost_metric=cost_metric,
            capability_metric=capability_metric
        ))
    
    # Compute Pareto frontier
    # A point is Pareto optimal if no other point dominates it
    # Dominates = lower cost AND higher capability
    pareto_frontier: List[str] = []
    
    for point in frontier_points:
        is_dominated = False
        
        for other in frontier_points:
            if other.model_id == point.model_id:
                continue
            
            # other dominates point if:
            # other has lower or equal cost AND higher or equal capability
            # with at least one strict inequality
            if (other.raw_cost <= point.raw_cost and 
                other.raw_capability >= point.raw_capability and
                (other.raw_cost < point.raw_cost or other.raw_capability > point.raw_capability)):
                is_dominated = True
                break
        
        if not is_dominated:
            point.is_pareto_optimal = True
            pareto_frontier.append(point.model_id)
    
    # Sort pareto frontier by cost for visualization
    pareto_frontier.sort(key=lambda m: next(
        p.raw_cost for p in frontier_points if p.model_id == m
    ))
    
    return FrontierChart(
        points=frontier_points,
        cost_min=cost_min,
        cost_max=cost_max,
        capability_min=capability_min,
        capability_max=capability_max,
        pareto_frontier=pareto_frontier,
        models_in_set=len(frontier_points),
        filter_description=filter_description
    )


def compute_multi_frontier(
    model_data: Dict[str, Dict[str, float]],
    cost_metrics: List[str] = None,
    capability_metrics: List[str] = None,
    filter_description: str = "All models"
) -> Dict[str, FrontierChart]:
    """
    Compute multiple frontiers for different metric combinations.
    
    Args:
        model_data: Dict of model_id -> {metric_name -> value}
        cost_metrics: List of cost metrics to use
        capability_metrics: List of capability metrics to use
        filter_description: Filter description
        
    Returns:
        Dict of "cost_metric:capability_metric" -> FrontierChart
    """
    if cost_metrics is None:
        cost_metrics = ["input_price", "output_price", "latency_ms"]
    
    if capability_metrics is None:
        capability_metrics = ["average_score", "mmlu", "humaneval"]
    
    frontiers = {}
    
    for cost_metric in cost_metrics:
        for capability_metric in capability_metrics:
            key = f"{cost_metric}:{capability_metric}"
            frontiers[key] = compute_frontier(
                model_data,
                cost_metric=cost_metric,
                capability_metric=capability_metric,
                filter_description=filter_description
            )
    
    return frontiers
