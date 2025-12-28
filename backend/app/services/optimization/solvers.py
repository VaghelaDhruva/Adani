from typing import Dict, Any, Optional
from pyomo.environ import SolverFactory, TerminationCondition, value
from pyomo.opt import SolverStatus

from app.core.config import get_settings
from app.utils.exceptions import OptimizationError

settings = get_settings()


def solve_model(model, solver_name: Optional[str] = None, time_limit_seconds: Optional[int] = None, mip_gap: Optional[float] = None) -> Dict[str, Any]:
    """
    Solve a Pyomo model using a robust solver fallback chain.
    Returns a dict with status, objective, runtime, gap, and solver used.
    """
    solver_name = solver_name or settings.DEFAULT_SOLVER
    time_limit = time_limit_seconds or settings.SOLVER_TIME_LIMIT_SECONDS
    gap = mip_gap or settings.SOLVER_MIP_GAP

    # Define solver fallback chain: Gurobi (commercial) -> HiGHS (modern open source) -> CBC (fallback)
    solver_chain = [solver_name] if solver_name != "auto" else ["gurobi", "highs", "cbc"]
    
    for attempt_solver in solver_chain:
        try:
            # Select solver
            if attempt_solver == "gurobi":
                opt = SolverFactory("gurobi")
                if not opt.available():
                    raise OptimizationError("Gurobi not available")
                opt.options["TimeLimit"] = time_limit
                opt.options["MIPGap"] = gap
            elif attempt_solver == "highs":
                opt = SolverFactory("highs")
                if not opt.available():
                    raise OptimizationError("HiGHS not available")
                opt.options["time_limit"] = time_limit
                opt.options["mip_rel_gap"] = gap
            elif attempt_solver == "cbc":
                opt = SolverFactory("cbc")
                if not opt.available():
                    raise OptimizationError("CBC not available")
                opt.options["seconds"] = time_limit
                opt.options["ratio"] = gap
            else:
                raise OptimizationError(f"Unsupported solver: {attempt_solver}")

            # Solve
            results = opt.solve(model, tee=False)
            status = results.solver.status
            termination = results.solver.termination_condition

            if status != SolverStatus.ok or termination not in {
                TerminationCondition.optimal,
                TerminationCondition.feasible,
                TerminationCondition.maxIterations,
                TerminationCondition.timeLimit,
            }:
                raise OptimizationError(f"Solver {attempt_solver} failed: status={status}, termination={termination}")

            # Extract results
            objective_value = getattr(model, "total_cost", None)
            obj_val = float(value(objective_value)) if objective_value is not None else None
            solver_time = results.solver.time if hasattr(results.solver, "time") else None
            solver_gap = results.solver.gap if hasattr(results.solver, "gap") else None

            return {
                "status": "optimal" if termination == TerminationCondition.optimal else "feasible",
                "solver": attempt_solver,
                "objective": obj_val,
                "runtime_seconds": solver_time,
                "gap": solver_gap,
                "termination": str(termination),
            }

        except Exception as e:
            # Log the attempt and continue to next solver
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Solver {attempt_solver} failed: {e}")
            continue

    # All solvers failed
    raise OptimizationError("All solvers in fallback chain failed")
