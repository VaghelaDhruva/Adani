from typing import Any, Dict

from pyomo.environ import value

from app.utils.exceptions import OptimizationError


def extract_solution(model) -> Dict[str, Any]:
	"""Extract decision variables and cost breakdown from a solved model.

	Returns a structured dict with:
	- production plan
	- shipments
	- inventory profile
	- trips
	- objective value and cost components
	"""
	try:
		production = [
			{"plant": i, "period": t, "tonnes": float(value(model.prod[i, t]))}
			for i in model.I
			for t in model.T
		]

		shipments = []
		trips = []
		for (i, j, mode) in model.R:
			for t in model.T:
				ship_val = float(value(model.ship[i, j, mode, t]))
				trip_val = float(value(model.trips[i, j, mode, t]))
				if ship_val > 0 or trip_val > 0:
					shipments.append(
						{
							"origin": i,
							"destination": j,
							"mode": mode,
							"period": t,
							"tonnes": ship_val,
						}
					)
					trips.append(
						{
							"origin": i,
							"destination": j,
							"mode": mode,
							"period": t,
							"trips": int(round(trip_val)),
						}
					)

		inventory = [
			{"plant": i, "period": t, "tonnes": float(value(model.inv[i, t]))}
			for i in model.I
			for t in model.T
		]

		# Cost breakdown using model parameters
		prod_cost = sum(
			float(value(model.prod_cost[i, t])) * float(value(model.prod[i, t]))
			for i in model.I
			for t in model.T
		)
		trans_cost = sum(
			float(value(model.trans_cost[i, j, mode]))
			* float(value(model.ship[i, j, mode, t]))
			for (i, j, mode) in model.R
			for t in model.T
		)
		fixed_trip_cost = sum(
			float(value(model.fixed_trip_cost[i, j, mode]))
			* float(value(model.trips[i, j, mode, t]))
			for (i, j, mode) in model.R
			for t in model.T
		)
		holding_cost = sum(
			float(value(model.hold_cost[i])) * float(value(model.inv[i, t]))
			for i in model.I
			for t in model.T
		)

		objective_val = float(value(model.total_cost)) if hasattr(model, "total_cost") else None
		total_cost = prod_cost + trans_cost + fixed_trip_cost + holding_cost

		return {
			"production": production,
			"shipments": shipments,
			"inventory": inventory,
			"trips": trips,
			"objective": objective_val,
			"cost_breakdown": {
				"total_cost": total_cost,
				"production_cost": prod_cost,
				"transport_cost": trans_cost,
				"fixed_trip_cost": fixed_trip_cost,
				"holding_cost": holding_cost,
			},
		}
	except Exception as e:
		raise OptimizationError(f"Failed to extract solution: {e}")
