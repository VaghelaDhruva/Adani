"""
Performance benchmarking for the clinker supply chain optimization system.
Generates synthetic workloads, benchmarks different model sizes, and tracks performance metrics.
"""

from typing import Dict, Any, List, Tuple, Optional
import time
import pandas as pd
import numpy as np
from datetime import datetime
import json
import uuid
from dataclasses import dataclass

from app.services.optimization.model_builder import build_clinker_model
from app.services.optimization.solvers import solve_model
from app.utils.exceptions import OptimizationError


@dataclass
class BenchmarkResult:
    """Data class for benchmark results."""
    test_id: str
    timestamp: str
    model_size: Dict[str, int]
    solver_name: str
    solve_time_seconds: float
    objective_value: Optional[float]
    gap: Optional[float]
    termination_status: str
    nodes_explored: Optional[int]
    iterations: Optional[int]
    memory_usage_mb: Optional[float]
    success: bool
    error_message: Optional[str] = None


class SyntheticDataGenerator:
    """
    Generates synthetic optimization problems of varying sizes for benchmarking.
    """
    
    def __init__(self, base_config: Optional[Dict[str, Any]] = None):
        """
        Initialize with base configuration.
        
        Args:
            base_config: Base configuration for synthetic data generation
        """
        self.base_config = base_config or {}
    
    def generate_model_data(
        self,
        num_plants: int = 5,
        num_customers: int = 20,
        num_periods: int = 12,
        num_modes: int = 3,
        route_density: float = 0.8
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate synthetic model data of specified size.
        
        Args:
            num_plants: Number of production plants
            num_customers: Number of customer demand nodes
            num_periods: Number of time periods
            num_modes: Number of transport modes
            route_density: Fraction of possible routes to create (0-1)
            
        Returns:
            Dict of DataFrames matching model input requirements
        """
        np.random.seed(42)  # For reproducible results
        
        # Generate plants
        plants_data = []
        for i in range(num_plants):
            plants_data.append({
                "plant_id": f"PLANT_{i:03d}",
                "plant_name": f"Plant {i}",
                "plant_type": "production"
            })
        plants_df = pd.DataFrame(plants_data)
        
        # Generate production capacity and costs
        prod_capacity_data = []
        for plant_id in plants_df["plant_id"]:
            for period in range(num_periods):
                base_capacity = np.random.uniform(1000, 5000)
                capacity_noise = np.random.uniform(0.8, 1.2)
                prod_capacity_data.append({
                    "plant_id": plant_id,
                    "period": f"P{period:02d}",
                    "max_capacity_tonnes": base_capacity * capacity_noise,
                    "variable_cost_per_tonne": np.random.uniform(50, 150),
                    "holding_cost_per_tonne": np.random.uniform(5, 15)
                })
        prod_capacity_df = pd.DataFrame(prod_capacity_data)
        
        # Generate demand forecast
        demand_data = []
        for customer_id in range(num_customers):
            for period in range(num_periods):
                base_demand = np.random.uniform(50, 300)
                demand_noise = np.random.uniform(0.7, 1.3)
                demand_data.append({
                    "customer_node_id": f"CUST_{customer_id:03d}",
                    "period": f"P{period:02d}",
                    "demand_tonnes": base_demand * demand_noise
                })
        demand_df = pd.DataFrame(demand_data)
        
        # Generate transport routes and modes
        transport_modes = ["TRUCK", "RAIL", "SHIP"][:num_modes]
        routes_data = []
        
        for plant_id in plants_df["plant_id"]:
            for customer_id in range(num_customers):
                # Create route with probability based on density
                if np.random.random() <= route_density:
                    for mode in transport_modes:
                        routes_data.append({
                            "origin_plant_id": plant_id,
                            "destination_node_id": f"CUST_{customer_id:03d}",
                            "transport_mode": mode,
                            "distance_km": np.random.uniform(50, 1000),
                            "cost_per_tonne": np.random.uniform(10, 100),
                            "cost_per_tonne_km": np.random.uniform(0.05, 0.5),
                            "fixed_cost_per_trip": np.random.uniform(100, 500),
                            "vehicle_capacity_tonnes": np.random.uniform(20, 100),
                            "min_batch_quantity_tonnes": np.random.uniform(10, 50)
                        })
        
        transport_df = pd.DataFrame(routes_data)
        
        # Generate safety stock policy
        safety_stock_data = []
        for plant_id in plants_df["plant_id"]:
            safety_stock_data.append({
                "node_id": plant_id,
                "safety_stock_tonnes": np.random.uniform(100, 500),
                "max_inventory_tonnes": np.random.uniform(2000, 10000)
            })
        safety_stock_df = pd.DataFrame(safety_stock_data)
        
        # Generate initial inventory
        inventory_data = []
        for plant_id in plants_df["plant_id"]:
            inventory_data.append({
                "node_id": plant_id,
                "period": "P00",  # Initial period
                "inventory_tonnes": np.random.uniform(200, 1000)
            })
        inventory_df = pd.DataFrame(inventory_data)
        
        return {
            "plants": plants_df,
            "production_capacity_cost": prod_capacity_df,
            "transport_routes_modes": transport_df,
            "demand_forecast": demand_df,
            "safety_stock_policy": safety_stock_df,
            "initial_inventory": inventory_df,
            "time_periods": [f"P{p:02d}" for p in range(num_periods)]
        }
    
    def generate_size_series(
        self,
        size_configs: List[Dict[str, int]]
    ) -> List[Dict[str, pd.DataFrame]]:
        """
        Generate a series of models with different sizes.
        
        Args:
            size_configs: List of size configuration dictionaries
            
        Returns:
            List of model data dictionaries
        """
        models = []
        for config in size_configs:
            model_data = self.generate_model_data(**config)
            models.append(model_data)
        return models


class PerformanceBenchmark:
    """
    Benchmarks optimization performance across different model sizes and solvers.
    """
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.data_generator = SyntheticDataGenerator()
    
    def run_benchmark_suite(
        self,
        size_configs: Optional[List[Dict[str, int]]] = None,
        solvers: Optional[List[str]] = None,
        time_limit_seconds: int = 300,
        mip_gap: float = 0.01
    ) -> Dict[str, Any]:
        """
        Run comprehensive benchmark suite.
        
        Args:
            size_configs: List of model size configurations
            solvers: List of solvers to test
            time_limit_seconds: Time limit per solve
            mip_gap: MIP gap tolerance
            
        Returns:
            Dict with benchmark results and summary statistics
        """
        # Default size configurations
        if size_configs is None:
            size_configs = [
                {"num_plants": 3, "num_customers": 10, "num_periods": 6, "num_modes": 2},
                {"num_plants": 5, "num_customers": 20, "num_periods": 12, "num_modes": 3},
                {"num_plants": 10, "num_customers": 50, "num_periods": 12, "num_modes": 3},
                {"num_plants": 15, "num_customers": 100, "num_periods": 24, "num_modes": 3},
            ]
        
        # Default solvers
        if solvers is None:
            solvers = ["highs", "cbc"]  # Exclude gurobi by default (may not be available
        
        # Generate test models
        test_models = self.data_generator.generate_size_series(size_configs)
        
        # Run benchmarks
        total_tests = len(test_models) * len(solvers)
        completed_tests = 0
        
        print(f"Starting benchmark suite: {total_tests} tests")
        
        for i, model_data in enumerate(test_models):
            size_config = size_configs[i]
            
            for solver in solvers:
                try:
                    result = self._benchmark_single_model(
                        model_data, solver, size_config, time_limit_seconds, mip_gap
                    )
                    self.results.append(result)
                    completed_tests += 1
                    
                    print(f"Completed {completed_tests}/{total_tests}: "
                          f"Size {size_config} with {solver} - "
                          f"Time: {result.solve_time_seconds:.2f}s")
                    
                except Exception as e:
                    # Log failed benchmark
                    failed_result = BenchmarkResult(
                        test_id=str(uuid.uuid4()),
                        timestamp=datetime.utcnow().isoformat(),
                        model_size=size_config,
                        solver_name=solver,
                        solve_time_seconds=0.0,
                        objective_value=None,
                        gap=None,
                        termination_status="failed",
                        nodes_explored=None,
                        iterations=None,
                        memory_usage_mb=None,
                        success=False,
                        error_message=str(e)
                    )
                    self.results.append(failed_result)
                    print(f"Failed {completed_tests + 1}/{total_tests}: "
                          f"Size {size_config} with {solver} - Error: {e}")
        
        # Generate summary
        summary = self._generate_summary()
        
        return {
            "benchmark_results": [self._result_to_dict(r) for r in self.results],
            "summary_statistics": summary,
            "total_tests": total_tests,
            "successful_tests": len([r for r in self.results if r.success]),
            "failed_tests": len([r for r in self.results if not r.success])
        }
    
    def _benchmark_single_model(
        self,
        model_data: Dict[str, pd.DataFrame],
        solver: str,
        size_config: Dict[str, int],
        time_limit_seconds: int,
        mip_gap: float
    ) -> BenchmarkResult:
        """
        Benchmark a single model with a specific solver.
        """
        test_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Build model
        try:
            model = build_clinker_model(model_data)
            model_build_time = time.time() - start_time
        except Exception as e:
            raise OptimizationError(f"Model building failed: {e}")
        
        # Solve model
        solve_start = time.time()
        try:
            solve_result = solve_model(
                model, solver, time_limit_seconds, mip_gap
            )
            solve_time = time.time() - solve_start
            
            # Extract additional metrics if available
            nodes_explored = getattr(solve_result, 'nodes', None)
            iterations = getattr(solve_result, 'iterations', None)
            
            return BenchmarkResult(
                test_id=test_id,
                timestamp=datetime.utcnow().isoformat(),
                model_size=size_config,
                solver_name=solver,
                solve_time_seconds=solve_time,
                objective_value=solve_result.get("objective"),
                gap=solve_result.get("gap"),
                termination_status=solve_result.get("termination", "unknown"),
                nodes_explored=nodes_explored,
                iterations=iterations,
                memory_usage_mb=None,  # Would need memory profiling
                success=True
            )
            
        except Exception as e:
            solve_time = time.time() - solve_start
            return BenchmarkResult(
                test_id=test_id,
                timestamp=datetime.utcnow().isoformat(),
                model_size=size_config,
                solver_name=solver,
                solve_time_seconds=solve_time,
                objective_value=None,
                gap=None,
                termination_status="failed",
                nodes_explored=None,
                iterations=None,
                memory_usage_mb=None,
                success=False,
                error_message=str(e)
            )
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics from benchmark results."""
        successful_results = [r for r in self.results if r.success]
        
        if not successful_results:
            return {"message": "No successful benchmarks"}
        
        # Calculate statistics by solver
        solver_stats = {}
        for solver in set(r.solver_name for r in successful_results):
            solver_results = [r for r in successful_results if r.solver_name == solver]
            
            solve_times = [r.solve_time_seconds for r in solver_results]
            objectives = [r.objective_value for r in solver_results if r.objective_value is not None]
            gaps = [r.gap for r in solver_results if r.gap is not None]
            
            solver_stats[solver] = {
                "count": len(solver_results),
                "avg_solve_time": np.mean(solve_times),
                "min_solve_time": np.min(solve_times),
                "max_solve_time": np.max(solve_times),
                "std_solve_time": np.std(solve_times),
                "avg_objective": np.mean(objectives) if objectives else None,
                "avg_gap": np.mean(gaps) if gaps else None,
                "success_rate": len(solver_results) / len([r for r in self.results if r.solver_name == solver])
            }
        
        # Calculate scalability metrics
        scalability_metrics = self._calculate_scalability_metrics(successful_results)
        
        # Performance recommendations
        recommendations = self._generate_recommendations(solver_stats, scalability_metrics)
        
        return {
            "solver_statistics": solver_stats,
            "scalability_metrics": scalability_metrics,
            "recommendations": recommendations,
            "overall_success_rate": len(successful_results) / len(self.results)
        }
    
    def _calculate_scalability_metrics(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Calculate scalability metrics across model sizes."""
        # Group by total problem size (approximate)
        size_metrics = {}
        
        for result in results:
            # Calculate approximate problem size
            total_size = (
                result.model_size.get("num_plants", 0) *
                result.model_size.get("num_customers", 0) *
                result.model_size.get("num_periods", 0) *
                result.model_size.get("num_modes", 0)
            )
            
            if total_size not in size_metrics:
                size_metrics[total_size] = []
            
            size_metrics[total_size].append(result.solve_time_seconds)
        
        # Calculate scaling factors
        sizes = sorted(size_metrics.keys())
        times = [np.mean(size_metrics[size]) for size in sizes]
        
        scaling_factor = None
        if len(sizes) >= 2:
            # Simple linear scaling estimate
            size_ratio = sizes[-1] / sizes[0]
            time_ratio = times[-1] / times[0]
            scaling_factor = time_ratio / size_ratio
        
        return {
            "size_time_pairs": list(zip(sizes, times)),
            "scaling_factor": scaling_factor,
            "largest_problem_solve_time": times[-1] if times else None,
            "smallest_problem_solve_time": times[0] if times else None
        }
    
    def _generate_recommendations(
        self,
        solver_stats: Dict[str, Any],
        scalability_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Solver recommendations
        best_solver = min(
            solver_stats.items(),
            key=lambda x: x[1]["avg_solve_time"]
        ) if solver_stats else None
        
        if best_solver:
            recommendations.append(
                f"Best performing solver: {best_solver[0]} "
                f"(avg time: {best_solver[1]['avg_solve_time']:.2f}s)"
            )
        
        # Scalability recommendations
        scaling_factor = scalability_metrics.get("scaling_factor")
        if scaling_factor and scaling_factor > 2.0:
            recommendations.append(
                f"Poor scalability detected (factor: {scaling_factor:.2f}). "
                "Consider model reduction or decomposition for large problems."
            )
        elif scaling_factor and scaling_factor < 1.5:
            recommendations.append(
                f"Good scalability (factor: {scaling_factor:.2f}). "
                "Current approach scales well with problem size."
            )
        
        # Performance recommendations
        max_solve_time = scalability_metrics.get("largest_problem_solve_time")
        if max_solve_time and max_solve_time > 300:  # 5 minutes
            recommendations.append(
                "Large problems taking >5 minutes. Consider increasing time limits or using heuristics."
            )
        
        return recommendations
    
    def _result_to_dict(self, result: BenchmarkResult) -> Dict[str, Any]:
        """Convert BenchmarkResult to dictionary for JSON serialization."""
        return {
            "test_id": result.test_id,
            "timestamp": result.timestamp,
            "model_size": result.model_size,
            "solver_name": result.solver_name,
            "solve_time_seconds": result.solve_time_seconds,
            "objective_value": result.objective_value,
            "gap": result.gap,
            "termination_status": result.termination_status,
            "nodes_explored": result.nodes_explored,
            "iterations": result.iterations,
            "memory_usage_mb": result.memory_usage_mb,
            "success": result.success,
            "error_message": result.error_message
        }
    
    def export_results(self, filename: str) -> None:
        """Export benchmark results to JSON file."""
        results_data = {
            "benchmark_results": [self._result_to_dict(r) for r in self.results],
            "summary_statistics": self._generate_summary(),
            "export_timestamp": datetime.utcnow().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"Benchmark results exported to {filename}")
    
    def get_performance_report(self) -> str:
        """Generate a formatted performance report."""
        if not self.results:
            return "No benchmark results available."
        
        successful_results = [r for r in self.results if r.success]
        
        report = []
        report.append("=== PERFORMANCE BENCHMARK REPORT ===")
        report.append(f"Total tests: {len(self.results)}")
        report.append(f"Successful: {len(successful_results)}")
        report.append(f"Success rate: {len(successful_results)/len(self.results):.1%}")
        report.append("")
        
        # Solver comparison
        solver_stats = {}
        for result in successful_results:
            if result.solver_name not in solver_stats:
                solver_stats[result.solver_name] = []
            solver_stats[result.solver_name].append(result.solve_time_seconds)
        
        report.append("SOLVER PERFORMANCE:")
        for solver, times in solver_stats.items():
            avg_time = np.mean(times)
            report.append(f"  {solver}: {avg_time:.2f}s average")
        
        report.append("")
        
        # Size performance
        size_performance = {}
        for result in successful_results:
            size_key = f"{result.model_size.get('num_plants', 0)}x{result.model_size.get('num_customers', 0)}"
            if size_key not in size_performance:
                size_performance[size_key] = []
            size_performance[size_key].append(result.solve_time_seconds)
        
        report.append("SIZE PERFORMANCE:")
        for size, times in sorted(size_performance.items()):
            avg_time = np.mean(times)
            report.append(f"  {size}: {avg_time:.2f}s average")
        
        return "\n".join(report)
