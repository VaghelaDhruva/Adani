from typing import Dict, Any, Optional
from pyomo.environ import SolverFactory, TerminationCondition
from pyomo.opt import SolverStatus

from app.core.config import get_settings
from app.utils.exceptions import OptimizationError

settings = get_settings()


def solve_model(model, solver_name: Optional[str] = None, time_limit_seconds: Optional[int] = None, mip_gap: Optional[float] = None) -> Dict[str, Any]:
    """
    Solve a Pyomo model using the specified solver.
    Returns a dict with status, objective, runtime, and gap.
    """
    solver_name = solver_name or settings.DEFAULT_SOLVER
    time_limit = time_limit_seconds or settings.SOLVER_TIME_LIMIT_SECONDS
    gap = mip_gap or settings.SOLVER_MIP_GAP

    # Select solver
    if solver_name == "gurobi":
        try:
            opt = SolverFactory("gurobi")
        except Exception:
            raise OptimizationError("Gurobi not available")
    elif solver_name == "cbc":
        opt = SolverFactory("cbc")
    elif solver_name == "highs":
        opt = SolverFactory("highs")
    else:
        raise OptimizationError(f"Unsupported solver: {solver_name}")

    # Set solver options
    if solver_name == "gurobi":
        opt.options["TimeLimit"] = time_limit
        opt.options["MIPGap"] = gap
    elif solver_name == "cbc":
        opt.options["seconds"] = time_limit
        opt.options["ratio"] = gap
    elif solver_name == "highs":
        opt.options["time_limit"] = time_limit
        opt.options["mip_rel_gap"] = gap

    # Solve
    results = opt.solve(model, tee=False)
    status = results.solver.status
    termination = results.solver.termination_condition

    if status != SolverStatus.ok or termination not in {
        TerminationCondition.optimal,
        TerminationCondition.maxTimeLimit,
        TerminationCondition.feasible,
    }:
        raise OptimizationError(f"Solver failed: status={status}, termination={termination}")

    objective_val = model.total_cost() if hasattr(model, "total_cost") else None

    # Some solvers (and Pyomo plugins) may not expose `time` or MIP gap attributes
    runtime = getattr(results.solver, "time", None)
    final_gap = None
    # Try common names on the solver results or options
    for attr in ("MIPGap", "mip_rel_gap", "gap"):
        if hasattr(results.solver, attr):
            final_gap = getattr(results.solver, attr)
            break

    return {
        "solver": solver_name,
        "status": str(status),
        "termination": str(termination),
        "objective": objective_val,
        "runtime_seconds": runtime,
        "mip_gap": final_gap,
    }
