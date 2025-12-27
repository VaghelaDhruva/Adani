# Optimization Model Documentation

## Overview
Mixed-Integer Linear Program (MILP) to minimize total supply chain cost for clinker logistics across plants, transport modes, and time periods.

## Sets
- I: Plants
- J: Customer nodes
- M: Transport modes (road, rail, sea, barge)
- T: Time periods (e.g., weeks)

## Parameters
- cap[i]: Max production capacity per period at plant i
- demand[j,t]: Demand at customer j in period t
- inv0[i]: Initial inventory at plant i
- ss[i]: Safety stock at plant i
- trans_cost[i,j,m]: Transport cost per tonne from i to j via mode m
- prod_cost[i]: Variable production cost per tonne at plant i
- hold_cost[i]: Holding cost per tonne at plant i
- vehicle_cap[i,j,m]: Vehicle capacity (tonnes) per trip
- sbq[i,j,m]: Minimum shipment batch quantity (0 if none)
- fixed_trip_cost[i,j,m]: Fixed cost per trip

## Decision Variables
- prod[i,t] >= 0: Production at plant i in period t
- ship[i,j,m,t] >= 0: Shipment quantity from i to j via mode m in period t
- trips[i,j,m,t] >= 0, integer: Number of trips
- use_mode[i,j,m,t] in {0,1}: Binary activation for SBQ
- inv[i,t] >= 0: Inventory at plant i at end of period t

## Constraints

1. Production capacity
   prod[i,t] <= cap[i]

2. Inventory balance
   inv[i,t-1] + prod[i,t] = sum_j,m ship[i,j,m,t] + inv[i,t]

3. Safety stock
   inv[i,t] >= ss[i]

4. Demand satisfaction
   sum_i,m ship[i,j,m,t] = demand[j,t]

5. Trip capacity
   ship[i,j,m,t] <= vehicle_cap[i,j,m] * trips[i,j,m,t]

6. Minimum batch quantity (SBQ)
   ship[i,j,m,t] >= sbq[i,j,m] * use_mode[i,j,m,t]
   ship[i,j,m,t] <= bigM * use_mode[i,j,m,t]  (optional, if bigM used)

## Objective
Minimize total cost:
- Production: sum_i,t prod_cost[i] * prod[i,t]
- Transport: sum_i,j,m,t trans_cost[i,j,m] * ship[i,j,m,t]
- Fixed trips: sum_i,j,m,t fixed_trip_cost[i,j,m] * trips[i,j,m,t]
- Holding: sum_i,t hold_cost[i] * inv[i,t]

## Extensions (future)
- Multi-product (clinker, cement, additives)
- Production changeover/ramp constraints
- Carbon cost or emissions caps
- Lead time constraints (multi-period shipments)
- Stochastic demand via scenario-based recourse

## Solver Options
- CBC (default, open source)
- HiGHS (fast open source)
- Gurobi (commercial, if available)
- Time limit and MIP gap configurable per scenario

## Output Artifacts
- Production plan per plant/period
- Shipments per route/mode/period
- Number of trips per route/mode/period
- Inventory profile per plant/period
- Total cost and component breakdown
- Solver metadata (runtime, gap, status)
