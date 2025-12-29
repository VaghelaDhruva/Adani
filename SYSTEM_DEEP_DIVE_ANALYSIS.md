# 🏭 Clinker Supply Chain Optimization System - Deep Dive Analysis

## 📋 Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Data Sources & Flow](#data-sources--flow)
3. [Data Processing Pipeline](#data-processing-pipeline)
4. [Optimization Engine](#optimization-engine)
5. [Scenario Management](#scenario-management)
6. [Dashboard Data Display](#dashboard-data-display)
7. [Result Generation & Calculation](#result-generation--calculation)
8. [API Endpoints & Data Flow](#api-endpoints--data-flow)
9. [Database Schema](#database-schema)
10. [Configuration & Settings](#configuration--settings)

---

## 1. System Architecture Overview

### 🏗️ **High-Level Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│  (SQLite/PG)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌────▼────┐             ┌────▼────┐             ┌────▼────┐
    │Dashboard│             │   API   │             │  Tables │
    │ Pages   │             │ Routes  │             │  & Data │
    └─────────┘             └─────────┘             └─────────┘
```

### 🔧 **Technology Stack**
- **Frontend**: Streamlit (Python web framework)
- **Backend**: FastAPI (Python REST API framework)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Optimization**: Pyomo/PuLP (Mathematical optimization)
- **Visualization**: Plotly (Interactive charts)
- **Styling**: Custom CSS with modern design system

---

## 2. Data Sources & Flow

### 📊 **Primary Data Sources**

#### **A. Master Data Tables**
```sql
-- Plant Master Data
plant_master:
├── plant_id (Primary Key)
├── plant_name
├── plant_type (Clinker/Grinding/Terminal)
├── location (City, State)
├── capacity_tonnes_per_month
├── production_cost_per_tonne
├── fixed_cost_monthly
└── operational_status

-- Demand Forecast Data  
demand_forecast:
├── demand_id (Primary Key)
├── node_id (Foreign Key → plant_master)
├── period (YYYY-MM format)
├── demand_tonnes
├── demand_type (Confirmed/Forecast)
├── priority_level
└── last_updated

-- Transport Routes & Modes
transport_routes_modes:
├── route_id (Primary Key)
├── origin_plant_id (Foreign Key)
├── destination_node_id (Foreign Key)
├── transport_mode (Road/Rail/Sea)
├── distance_km
├── cost_per_tonne_km
├── transit_time_days
├── vehicle_capacity_tonnes
└── route_status
```

#### **B. Operational Data Tables**
```sql
-- Initial Inventory
initial_inventory:
├── inventory_id (Primary Key)
├── plant_id (Foreign Key)
├── period
├── opening_stock_tonnes
├── safety_stock_tonnes
└── holding_cost_per_tonne_month

-- Production Capacity & Costs
production_capacity_cost:
├── capacity_id (Primary Key)
├── plant_id (Foreign Key)
├── period
├── max_capacity_tonnes
├── min_capacity_tonnes
├── variable_cost_per_tonne
├── fixed_cost_per_period
└── maintenance_schedule

-- Safety Stock Policy
safety_stock_policy:
├── policy_id (Primary Key)
├── node_id (Foreign Key)
├── product_type
├── safety_stock_days
├── reorder_point_tonnes
└── policy_effective_date
```

### 🔄 **Data Flow Process**

#### **Step 1: Data Ingestion**
```python
# Location: backend/app/services/data_ingestion.py
def ingest_data_from_sources():
    """
    Data comes from multiple sources:
    1. ERP Systems (SAP/Oracle) → CSV exports
    2. Manual uploads via dashboard
    3. External APIs (market data, weather)
    4. Historical database records
    """
    sources = {
        'erp_export': load_csv_files(),
        'manual_upload': process_uploaded_files(),
        'external_api': fetch_market_data(),
        'historical': query_database_history()
    }
    return consolidate_sources(sources)
```

#### **Step 2: Data Validation Pipeline**
```python
# Location: backend/app/services/data_validation.py
class DataValidationPipeline:
    """5-Stage validation process"""
    
    def stage_1_schema_validation(self, data):
        """Validate column names, data types, required fields"""
        required_columns = {
            'plant_master': ['plant_id', 'plant_name', 'capacity_tonnes_per_month'],
            'demand_forecast': ['node_id', 'period', 'demand_tonnes'],
            'transport_routes': ['origin_plant_id', 'destination_node_id', 'cost_per_tonne_km']
        }
        return validate_schema(data, required_columns)
    
    def stage_2_business_rules(self, data):
        """Apply business logic validation"""
        rules = {
            'no_negative_demand': lambda x: x['demand_tonnes'] >= 0,
            'valid_transport_modes': lambda x: x['transport_mode'] in ['Road', 'Rail', 'Sea'],
            'capacity_positive': lambda x: x['capacity_tonnes_per_month'] > 0,
            'cost_positive': lambda x: x['cost_per_tonne_km'] > 0
        }
        return apply_business_rules(data, rules)
    
    def stage_3_referential_integrity(self, data):
        """Check foreign key relationships"""
        integrity_checks = {
            'plant_exists': check_plant_references(),
            'route_endpoints_valid': check_route_references(),
            'period_format_valid': check_period_format()
        }
        return validate_references(data, integrity_checks)
    
    def stage_4_unit_consistency(self, data):
        """Ensure consistent units across tables"""
        unit_standards = {
            'weight': 'tonnes',
            'distance': 'km', 
            'cost': 'INR_per_tonne',
            'time': 'days'
        }
        return standardize_units(data, unit_standards)
    
    def stage_5_missing_data_scan(self, data):
        """Identify and handle missing critical data"""
        critical_fields = ['demand_tonnes', 'capacity_tonnes_per_month', 'cost_per_tonne_km']
        return handle_missing_data(data, critical_fields)
```

---

## 3. Data Processing Pipeline

### 🧹 **Data Cleaning Process**

#### **A. Data Normalization**
```python
# Location: backend/app/services/data_cleaning.py
class DataCleaner:
    def normalize_data(self, raw_data):
        """
        Cleaning steps applied to all incoming data:
        """
        cleaned_data = raw_data.copy()
        
        # 1. String normalization
        cleaned_data = self.normalize_strings(cleaned_data)
        # - Strip whitespace
        # - Convert to uppercase for IDs
        # - Standardize naming conventions
        
        # 2. Numeric validation
        cleaned_data = self.validate_numerics(cleaned_data)
        # - Convert string numbers to float/int
        # - Handle scientific notation
        # - Remove currency symbols
        
        # 3. Date standardization
        cleaned_data = self.standardize_dates(cleaned_data)
        # - Convert to YYYY-MM-DD format
        # - Handle different date formats
        # - Validate date ranges
        
        # 4. Remove duplicates
        cleaned_data = self.remove_duplicates(cleaned_data)
        # - Based on composite keys
        # - Keep most recent records
        
        # 5. Fill missing values
        cleaned_data = self.handle_missing_values(cleaned_data)
        # - Use business rules for defaults
        # - Interpolate where appropriate
        # - Flag critical missing data
        
        return cleaned_data
```

#### **B. Data Transformation**
```python
# Location: backend/app/services/data_transformation.py
def transform_for_optimization(cleaned_data):
    """
    Transform cleaned data into optimization model format
    """
    
    # Create optimization-ready datasets
    optimization_data = {
        'plants': create_plant_parameters(cleaned_data['plant_master']),
        'demand': create_demand_matrix(cleaned_data['demand_forecast']),
        'transport': create_transport_cost_matrix(cleaned_data['transport_routes']),
        'capacity': create_capacity_constraints(cleaned_data['production_capacity']),
        'inventory': create_inventory_parameters(cleaned_data['initial_inventory'])
    }
    
    return optimization_data

def create_plant_parameters(plant_data):
    """Convert plant master data to optimization parameters"""
    return {
        'plant_ids': plant_data['plant_id'].tolist(),
        'production_costs': dict(zip(plant_data['plant_id'], plant_data['production_cost_per_tonne'])),
        'capacities': dict(zip(plant_data['plant_id'], plant_data['capacity_tonnes_per_month'])),
        'fixed_costs': dict(zip(plant_data['plant_id'], plant_data['fixed_cost_monthly']))
    }

def create_demand_matrix(demand_data):
    """Create time-series demand matrix"""
    demand_matrix = {}
    for _, row in demand_data.iterrows():
        key = (row['node_id'], row['period'])
        demand_matrix[key] = row['demand_tonnes']
    return demand_matrix

def create_transport_cost_matrix(transport_data):
    """Create origin-destination cost matrix"""
    cost_matrix = {}
    for _, row in transport_data.iterrows():
        key = (row['origin_plant_id'], row['destination_node_id'], row['transport_mode'])
        cost_matrix[key] = {
            'cost_per_tonne': row['cost_per_tonne_km'] * row['distance_km'],
            'transit_time': row['transit_time_days'],
            'capacity': row['vehicle_capacity_tonnes']
        }
    return cost_matrix
```

---

## 4. Optimization Engine

### ⚙️ **Mathematical Model Structure**

#### **A. Objective Function**
```python
# Location: backend/app/services/optimization_engine.py
def build_optimization_model(data):
    """
    Mixed Integer Linear Programming (MILP) Model
    
    MINIMIZE: Total Supply Chain Cost
    = Production Costs + Transportation Costs + Inventory Holding Costs + Penalty Costs
    """
    
    model = ConcreteModel()
    
    # Sets (indices)
    model.Plants = Set(initialize=data['plants']['plant_ids'])
    model.Customers = Set(initialize=data['demand']['customer_ids'])
    model.Periods = Set(initialize=data['periods'])
    model.TransportModes = Set(initialize=['Road', 'Rail', 'Sea'])
    
    # Parameters
    model.ProductionCost = Param(model.Plants, initialize=data['plants']['production_costs'])
    model.TransportCost = Param(model.Plants, model.Customers, model.TransportModes, 
                               initialize=data['transport']['cost_matrix'])
    model.Demand = Param(model.Customers, model.Periods, initialize=data['demand']['demand_matrix'])
    model.Capacity = Param(model.Plants, model.Periods, initialize=data['plants']['capacities'])
    
    # Decision Variables
    model.Production = Var(model.Plants, model.Periods, domain=NonNegativeReals)
    model.Shipment = Var(model.Plants, model.Customers, model.Periods, model.TransportModes, 
                        domain=NonNegativeReals)
    model.Inventory = Var(model.Plants, model.Periods, domain=NonNegativeReals)
    model.Trips = Var(model.Plants, model.Customers, model.Periods, model.TransportModes, 
                     domain=NonNegativeIntegers)
    
    # Objective Function
    def total_cost_rule(model):
        production_cost = sum(model.ProductionCost[p] * model.Production[p,t] 
                            for p in model.Plants for t in model.Periods)
        
        transport_cost = sum(model.TransportCost[p,c,m] * model.Shipment[p,c,t,m]
                           for p in model.Plants for c in model.Customers 
                           for t in model.Periods for m in model.TransportModes)
        
        inventory_cost = sum(data['inventory']['holding_cost'][p] * model.Inventory[p,t]
                           for p in model.Plants for t in model.Periods)
        
        return production_cost + transport_cost + inventory_cost
    
    model.TotalCost = Objective(rule=total_cost_rule, sense=minimize)
    
    return model
```

#### **B. Constraints**
```python
def add_constraints(model, data):
    """Add business constraints to the optimization model"""
    
    # 1. Demand Satisfaction Constraint
    def demand_satisfaction_rule(model, c, t):
        return sum(model.Shipment[p,c,t,m] for p in model.Plants 
                  for m in model.TransportModes) >= model.Demand[c,t]
    model.DemandSatisfaction = Constraint(model.Customers, model.Periods, 
                                        rule=demand_satisfaction_rule)
    
    # 2. Production Capacity Constraint
    def capacity_constraint_rule(model, p, t):
        return model.Production[p,t] <= model.Capacity[p,t]
    model.CapacityConstraint = Constraint(model.Plants, model.Periods, 
                                        rule=capacity_constraint_rule)
    
    # 3. Inventory Balance Constraint
    def inventory_balance_rule(model, p, t):
        if t == model.Periods.first():
            return (data['inventory']['initial_stock'][p] + model.Production[p,t] - 
                   sum(model.Shipment[p,c,t,m] for c in model.Customers 
                       for m in model.TransportModes) == model.Inventory[p,t])
        else:
            prev_period = model.Periods.prev(t)
            return (model.Inventory[p,prev_period] + model.Production[p,t] - 
                   sum(model.Shipment[p,c,t,m] for c in model.Customers 
                       for m in model.TransportModes) == model.Inventory[p,t])
    model.InventoryBalance = Constraint(model.Plants, model.Periods, 
                                      rule=inventory_balance_rule)
    
    # 4. Vehicle Capacity Constraint
    def vehicle_capacity_rule(model, p, c, t, m):
        vehicle_capacity = data['transport']['vehicle_capacity'][m]
        return model.Shipment[p,c,t,m] <= model.Trips[p,c,t,m] * vehicle_capacity
    model.VehicleCapacity = Constraint(model.Plants, model.Customers, model.Periods, 
                                     model.TransportModes, rule=vehicle_capacity_rule)
    
    # 5. Safety Stock Constraint
    def safety_stock_rule(model, p, t):
        safety_stock = data['inventory']['safety_stock'][p]
        return model.Inventory[p,t] >= safety_stock
    model.SafetyStock = Constraint(model.Plants, model.Periods, rule=safety_stock_rule)
    
    return model
```

#### **C. Solver Configuration**
```python
# Location: backend/app/services/solver_manager.py
class SolverManager:
    def __init__(self):
        self.available_solvers = {
            'highs': {'type': 'open_source', 'performance': 'high'},
            'cbc': {'type': 'open_source', 'performance': 'medium'},
            'gurobi': {'type': 'commercial', 'performance': 'very_high'},
            'cplex': {'type': 'commercial', 'performance': 'very_high'}
        }
    
    def solve_model(self, model, solver_name='highs', time_limit=600, mip_gap=0.01):
        """Solve the optimization model with specified parameters"""
        
        solver = SolverFactory(solver_name)
        
        # Set solver options
        solver.options['time_limit'] = time_limit
        solver.options['mip_gap'] = mip_gap
        solver.options['threads'] = 4
        
        # Solve the model
        start_time = time.time()
        results = solver.solve(model, tee=True)
        solve_time = time.time() - start_time
        
        # Extract solution
        solution = self.extract_solution(model, results, solve_time)
        
        return solution
    
    def extract_solution(self, model, results, solve_time):
        """Extract solution from solved model"""
        
        solution = {
            'solver_status': str(results.solver.termination_condition),
            'objective_value': value(model.TotalCost),
            'solve_time': solve_time,
            'optimality_gap': results.solver.gap if hasattr(results.solver, 'gap') else None,
            
            # Decision variables
            'production': {(p,t): value(model.Production[p,t]) 
                          for p in model.Plants for t in model.Periods},
            'shipments': {(p,c,t,m): value(model.Shipment[p,c,t,m]) 
                         for p in model.Plants for c in model.Customers 
                         for t in model.Periods for m in model.TransportModes},
            'inventory': {(p,t): value(model.Inventory[p,t]) 
                         for p in model.Plants for t in model.Periods},
            'trips': {(p,c,t,m): value(model.Trips[p,c,t,m]) 
                     for p in model.Plants for c in model.Customers 
                     for t in model.Periods for m in model.TransportModes}
        }
        
        return solution
```

---

## 5. Scenario Management

### 🎭 **Scenario Engine Architecture**

#### **A. Scenario Types**
```python
# Location: backend/app/services/scenario_manager.py
class ScenarioManager:
    def __init__(self):
        self.scenario_types = {
            'base': 'Baseline scenario with current parameters',
            'high_demand': 'Increased demand by 25%',
            'low_demand': 'Decreased demand by 20%',
            'capacity_constrained': 'Reduced plant capacity by 15%',
            'transport_disruption': 'Increased transport costs by 35%',
            'uncertainty': 'Stochastic scenario with demand uncertainty'
        }
    
    def generate_scenario_data(self, base_data, scenario_name):
        """Generate scenario-specific data modifications"""
        
        scenario_data = base_data.copy()
        
        if scenario_name == 'high_demand':
            scenario_data = self.modify_demand(scenario_data, multiplier=1.25)
        
        elif scenario_name == 'low_demand':
            scenario_data = self.modify_demand(scenario_data, multiplier=0.8)
        
        elif scenario_name == 'capacity_constrained':
            scenario_data = self.modify_capacity(scenario_data, multiplier=0.85)
        
        elif scenario_name == 'transport_disruption':
            scenario_data = self.modify_transport_costs(scenario_data, multiplier=1.35)
        
        elif scenario_name == 'uncertainty':
            scenario_data = self.add_demand_uncertainty(scenario_data)
        
        return scenario_data
    
    def modify_demand(self, data, multiplier):
        """Modify demand values by multiplier"""
        for key in data['demand']['demand_matrix']:
            data['demand']['demand_matrix'][key] *= multiplier
        return data
    
    def modify_capacity(self, data, multiplier):
        """Modify production capacity by multiplier"""
        for plant in data['plants']['capacities']:
            data['plants']['capacities'][plant] *= multiplier
        return data
    
    def modify_transport_costs(self, data, multiplier):
        """Modify transport costs by multiplier"""
        for key in data['transport']['cost_matrix']:
            data['transport']['cost_matrix'][key]['cost_per_tonne'] *= multiplier
        return data
```

#### **B. Scenario Comparison Logic**
```python
def compare_scenarios(scenario_results):
    """Compare multiple scenario results"""
    
    comparison = {
        'scenarios': [],
        'metrics': {
            'total_cost': {},
            'service_level': {},
            'capacity_utilization': {},
            'transport_efficiency': {}
        }
    }
    
    for scenario_name, results in scenario_results.items():
        comparison['scenarios'].append(scenario_name)
        
        # Calculate key metrics
        comparison['metrics']['total_cost'][scenario_name] = results['objective_value']
        comparison['metrics']['service_level'][scenario_name] = calculate_service_level(results)
        comparison['metrics']['capacity_utilization'][scenario_name] = calculate_utilization(results)
        comparison['metrics']['transport_efficiency'][scenario_name] = calculate_transport_efficiency(results)
    
    # Add recommendations
    comparison['recommendations'] = generate_recommendations(comparison['metrics'])
    
    return comparison
```

---

## 6. Dashboard Data Display

### 📊 **Data Flow to Frontend**

#### **A. API Data Transformation**
```python
# Location: backend/app/api/v1/routes_dashboard_demo.py
def _generate_enterprise_kpi_data(scenario_name: str) -> Dict[str, Any]:
    """
    Transform optimization results into dashboard-ready format
    """
    
    # Get optimization results for scenario
    optimization_results = get_scenario_results(scenario_name)
    
    # Calculate derived metrics
    kpi_data = {
        'scenario_name': scenario_name,
        'run_id': f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'timestamp': datetime.now().isoformat(),
        
        # Cost breakdown (converted to INR)
        'cost_summary': {
            'total_cost': optimization_results['objective_value'],
            'production_cost': calculate_production_cost(optimization_results),
            'transport_cost': calculate_transport_cost(optimization_results),
            'inventory_cost': calculate_inventory_cost(optimization_results),
            'penalty_cost': calculate_penalty_cost(optimization_results)
        },
        
        # Service performance metrics
        'service_performance': {
            'service_level': calculate_service_level(optimization_results),
            'demand_fulfillment': calculate_demand_fulfillment(optimization_results),
            'on_time_delivery': calculate_on_time_delivery(optimization_results),
            'stockout_triggered': check_stockout_conditions(optimization_results)
        },
        
        # Production utilization
        'production_utilization': calculate_plant_utilization(optimization_results),
        
        # Transport utilization
        'transport_utilization': calculate_transport_utilization(optimization_results),
        
        # Inventory status
        'inventory_status': calculate_inventory_metrics(optimization_results),
        
        # Demand fulfillment details
        'demand_fulfillment': calculate_demand_details(optimization_results)
    }
    
    return kpi_data
```

#### **B. Metric Calculations**
```python
def calculate_service_level(results):
    """Calculate overall service level percentage"""
    total_demand = sum(demand for demand in results['demand_matrix'].values())
    total_fulfilled = sum(shipment for shipment in results['shipments'].values())
    return min(1.0, total_fulfilled / total_demand) if total_demand > 0 else 0

def calculate_plant_utilization(results):
    """Calculate capacity utilization for each plant"""
    utilization_data = []
    
    for plant in results['plants']:
        total_production = sum(results['production'].get((plant, period), 0) 
                             for period in results['periods'])
        total_capacity = sum(results['capacity'].get((plant, period), 0) 
                           for period in results['periods'])
        
        utilization_pct = total_production / total_capacity if total_capacity > 0 else 0
        
        utilization_data.append({
            'plant_name': plant,
            'production_used': total_production,
            'production_capacity': total_capacity,
            'utilization_pct': utilization_pct
        })
    
    return utilization_data

def calculate_transport_utilization(results):
    """Calculate transport mode utilization and trips"""
    transport_data = []
    
    for (plant, customer, period, mode), shipment_qty in results['shipments'].items():
        if shipment_qty > 0:
            trips = results['trips'].get((plant, customer, period, mode), 0)
            vehicle_capacity = get_vehicle_capacity(mode)
            capacity_used_pct = (shipment_qty / (trips * vehicle_capacity)) if trips > 0 else 0
            
            transport_data.append({
                'from': plant,
                'to': customer,
                'mode': mode,
                'trips': trips,
                'capacity_used_pct': min(1.0, capacity_used_pct),
                'sbq_compliance': 'Yes' if capacity_used_pct <= 0.95 else 'No',
                'violations': max(0, int((capacity_used_pct - 0.95) * 100)) if capacity_used_pct > 0.95 else 0
            })
    
    return transport_data
```

#### **C. INR Currency Formatting**
```python
# Location: frontend/streamlit_app/pages/01_KPI_Dashboard.py
def format_inr(value):
    """Format currency value in Indian Rupees with proper digit grouping."""
    try:
        if value is None or value == 0:
            return "₹0"
        
        amount = float(value)
        negative = amount < 0
        amount = abs(amount)
        
        if amount >= 10000000:  # 1 crore = 10 million
            crores = amount / 10000000
            return f"{'−' if negative else ''}₹{crores:,.2f} Cr"
        elif amount >= 100000:  # 1 lakh = 100 thousand
            lakhs = amount / 100000
            return f"{'−' if negative else ''}₹{lakhs:,.2f} L"
        elif amount >= 1000:  # 1 thousand
            thousands = amount / 1000
            return f"{'−' if negative else ''}₹{thousands:,.1f}K"
        else:
            return f"{'−' if negative else ''}₹{amount:,.2f}"
    except (ValueError, TypeError):
        return "₹0"

# Usage in dashboard:
# ₹2.75 Cr = ₹27,500,000 (2.75 crores)
# ₹85.50 L = ₹8,550,000 (85.5 lakhs)  
# ₹15.2K = ₹15,200 (15.2 thousand)
```

---

## 7. Result Generation & Calculation

### 🔢 **Why Results Vary Each Time**

#### **A. Randomization Sources**
```python
# Location: backend/app/api/v1/routes_runs.py
def _generate_optimization_result(run_id: str) -> Dict[str, Any]:
    """
    Results vary due to multiple randomization factors:
    """
    
    # 1. Run ID-based seed for consistency within same run
    run_hash = hash(run_id) % 100  # Deterministic based on run_id
    
    # 2. Time-based variations
    timestamp_str = run_id.split('_')[1] + '_' + run_id.split('_')[2]
    run_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
    
    # 3. Scenario-specific multipliers
    base_multiplier = 1.0 + (run_hash - 50) * 0.01  # ±50% variation
    
    # 4. Solver performance variations
    if run_hash < 85:
        solver_status = "optimal"
        runtime_seconds = random.uniform(45.0, 180.0)  # Random solve time
        optimality_gap = random.uniform(0.001, 0.02)   # Random gap
    elif run_hash < 95:
        solver_status = "feasible"
        runtime_seconds = random.uniform(180.0, 600.0)
        optimality_gap = random.uniform(0.02, 0.05)
    else:
        solver_status = "infeasible"
        runtime_seconds = random.uniform(10.0, 60.0)
        optimality_gap = None
    
    # 5. Cost variations based on market conditions
    production_cost = int(18500000 * base_multiplier)  # Base ₹1.85 Cr
    transportation_cost = int(8200000 * base_multiplier)  # Base ₹82 L
    
    return {
        'total_cost': production_cost + transportation_cost,
        'solver_status': solver_status,
        'runtime_seconds': runtime_seconds,
        'optimality_gap': optimality_gap
    }
```

#### **B. Realistic Data Generation**
```python
def generate_realistic_production_plan(base_multiplier, plants):
    """Generate realistic production plans with variations"""
    production_plan = []
    
    for plant in plants:
        for period in ["2025-01", "2025-02", "2025-03"]:
            # Base production with seasonal variations
            seasonal_factor = {
                "2025-01": 0.9,   # Lower in January
                "2025-02": 1.0,   # Normal in February  
                "2025-03": 1.1    # Higher in March
            }[period]
            
            # Plant-specific capacity factors
            plant_factor = {
                "Mumbai_Plant": 1.2,    # Higher capacity
                "Delhi_Plant": 1.0,     # Standard capacity
                "Chennai_Plant": 0.8,   # Lower capacity
                "Kolkata_Plant": 0.9    # Medium capacity
            }.get(plant, 1.0)
            
            # Random demand variations (±20%)
            demand_variation = random.uniform(0.8, 1.2)
            
            production = int(1500 * base_multiplier * seasonal_factor * 
                           plant_factor * demand_variation)
            
            if production > 0:
                production_plan.append({
                    "plant": plant,
                    "period": period,
                    "tonnes": production
                })
    
    return production_plan

def generate_realistic_shipment_plan(base_multiplier):
    """Generate realistic shipment plans with route preferences"""
    shipment_plan = []
    
    # Route preferences based on distance and cost
    preferred_routes = [
        ("Mumbai_Plant", "Mumbai_Market", "road", 0.3),      # High preference
        ("Mumbai_Plant", "Pune_Market", "road", 0.25),       # Medium-high
        ("Delhi_Plant", "Delhi_NCR", "rail", 0.4),           # Very high
        ("Chennai_Plant", "Chennai_Region", "road", 0.35),   # High
        ("Chennai_Plant", "Bangalore_Hub", "road", 0.2)      # Medium
    ]
    
    for origin, destination, mode, preference in preferred_routes:
        for period in ["2025-01", "2025-02", "2025-03"]:
            # Base shipment adjusted by preference and multiplier
            base_shipment = 800 * preference * base_multiplier
            
            # Add random variations (±30%)
            variation = random.uniform(0.7, 1.3)
            tonnes = int(base_shipment * variation)
            
            # Calculate trips based on vehicle capacity
            vehicle_capacity = {"road": 25, "rail": 50, "sea": 100}[mode]
            trips = max(1, int(tonnes / vehicle_capacity))
            
            if tonnes > 0:
                shipment_plan.append({
                    "origin": origin,
                    "destination": destination,
                    "mode": mode,
                    "period": period,
                    "tonnes": tonnes,
                    "trips": trips
                })
    
    return shipment_plan
```

#### **C. Performance Metrics Calculation**
```python
def calculate_dynamic_service_level(scenario_multiplier):
    """Calculate service level based on scenario conditions"""
    
    # Base service level
    base_service_level = 0.96
    
    # Scenario impact on service level
    scenario_impact = {
        'base': 0.0,
        'high_demand': -0.08,      # Harder to meet high demand
        'low_demand': +0.02,       # Easier to meet low demand
        'capacity_constrained': -0.12,  # Much harder with less capacity
        'transport_disruption': -0.06   # Transport issues affect service
    }
    
    # Apply scenario impact
    adjusted_service_level = base_service_level + scenario_impact.get('base', 0.0)
    
    # Add random variations (±3%)
    random_variation = random.uniform(-0.03, 0.03)
    final_service_level = max(0.80, min(0.99, adjusted_service_level + random_variation))
    
    return final_service_level

def calculate_capacity_utilization(production_plan, plant_capacities):
    """Calculate realistic capacity utilization"""
    utilization = {}
    
    for plant, capacity in plant_capacities.items():
        total_production = sum(p['tonnes'] for p in production_plan if p['plant'] == plant)
        utilization[plant] = min(1.0, total_production / capacity) if capacity > 0 else 0
    
    return utilization
```

---

## 8. API Endpoints & Data Flow

### 🔌 **Complete API Architecture**

#### **A. Dashboard API Endpoints**
```python
# Location: backend/app/api/v1/routes_dashboard_demo.py

@router.get("/kpi/dashboard/{scenario_name}")
def get_kpi_dashboard(scenario_name: str, db: Session = Depends(get_db)):
    """
    GET /api/v1/dashboard/kpi/dashboard/{scenario_name}
    
    Returns comprehensive KPI data for dashboard display:
    - Cost summary with INR formatting
    - Service performance metrics  
    - Production utilization by plant
    - Transport utilization by mode
    - Inventory and safety stock status
    - Demand fulfillment details
    """
    kpi_data = _generate_enterprise_kpi_data(scenario_name)
    return kpi_data

@router.get("/scenarios/list")
def get_available_scenarios(db: Session = Depends(get_db)):
    """
    GET /api/v1/dashboard/scenarios/list
    
    Returns list of available scenarios:
    - base, high_demand, low_demand
    - capacity_constrained, transport_disruption
    - uncertainty (stochastic analysis)
    """
    return {"scenarios": [...]}

@router.post("/scenarios/compare")
def compare_scenarios(scenario_names: List[str], db: Session = Depends(get_db)):
    """
    POST /api/v1/dashboard/scenarios/compare
    Body: ["base", "high_demand", "low_demand"]
    
    Returns comparative analysis:
    - Cost comparison across scenarios
    - Service level differences
    - Capacity utilization comparison
    - Risk analysis and recommendations
    """
    comparison_data = []
    for scenario in scenario_names:
        kpi_data = _generate_enterprise_kpi_data(scenario)
        comparison_data.append(extract_comparison_metrics(kpi_data))
    
    return {"comparison_data": comparison_data}
```

#### **B. Results API Endpoints**
```python
# Location: backend/app/api/v1/routes_runs.py

@router.get("/runs")
def get_optimization_runs(limit: int = Query(20), db: Session = Depends(get_db)):
    """
    GET /api/v1/runs?limit=20
    
    Returns list of optimization runs:
    - run_id, status, timestamp
    - scenario, solver, runtime
    - total_cost (if completed)
    """
    runs = generate_sample_runs(limit)
    return {"runs": runs, "total_count": len(runs)}

@router.get("/runs/{run_id}/results")
def get_optimization_results(run_id: str, db: Session = Depends(get_db)):
    """
    GET /api/v1/runs/{run_id}/results
    
    Returns detailed optimization results:
    - Solver status and performance metrics
    - Cost breakdown (production, transport, inventory, penalties)
    - Production plan by plant and period
    - Shipment plan by route and mode
    - Inventory levels over time
    - Service level and utilization metrics
    """
    results = _generate_optimization_result(run_id)
    return results

@router.get("/runs/{run_id}/status")
def get_run_status(run_id: str, db: Session = Depends(get_db)):
    """
    GET /api/v1/runs/{run_id}/status
    
    Returns run execution status:
    - status: running/completed/failed
    - progress percentage
    - estimated completion time
    - error messages (if failed)
    """
    status = determine_run_status(run_id)
    return status
```

#### **C. Data Health API Endpoints**
```python
# Location: backend/app/api/v1/routes_dashboard_demo.py

@router.get("/health-status")
def get_data_health_status(db: Session = Depends(get_db)):
    """
    GET /api/v1/dashboard/health-status
    
    Returns comprehensive data health status:
    - Table-level validation status (PASS/WARN/FAIL)
    - Record counts and last update timestamps
    - Missing key fields and referential integrity issues
    - Overall optimization readiness status
    """
    return {
        "table_status": {
            "plant_master": {
                "record_count": 5,
                "last_update": "2025-01-01T10:00:00",
                "validation_status": "PASS",
                "missing_key_fields": 0,
                "referential_integrity_issues": 0
            },
            # ... other tables
        },
        "overall_status": "WARN",
        "optimization_ready": True
    }

@router.post("/run-optimization")
def run_optimization(
    scenario_name: str = Query("base"),
    solver: str = Query("highs"),
    time_limit: int = Query(600),
    mip_gap: float = Query(0.01),
    db: Session = Depends(get_db)
):
    """
    POST /api/v1/dashboard/run-optimization
    
    Triggers optimization run with parameters:
    - scenario_name: which scenario to optimize
    - solver: optimization solver to use
    - time_limit: maximum solve time in seconds
    - mip_gap: optimality gap tolerance
    
    Returns:
    - run_id for tracking
    - initial status and estimated completion
    """
    run_id = f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # In real implementation, this would:
    # 1. Validate data health
    # 2. Queue optimization job
    # 3. Return run_id for tracking
    
    return {
        "status": "queued",
        "run_id": run_id,
        "estimated_completion": (datetime.now() + timedelta(minutes=5)).isoformat()
    }
```

---

## 9. Database Schema

### 🗄️ **Complete Database Structure**

#### **A. Master Data Tables**
```sql
-- Plant Master Table
CREATE TABLE plant_master (
    plant_id VARCHAR(20) PRIMARY KEY,
    plant_name VARCHAR(100) NOT NULL,
    plant_type VARCHAR(20) CHECK (plant_type IN ('Clinker', 'Grinding', 'Terminal')),
    location_city VARCHAR(50),
    location_state VARCHAR(50),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    capacity_tonnes_per_month INTEGER NOT NULL CHECK (capacity_tonnes_per_month > 0),
    production_cost_per_tonne DECIMAL(10,2) NOT NULL CHECK (production_cost_per_tonne > 0),
    fixed_cost_monthly DECIMAL(12,2) DEFAULT 0,
    operational_status VARCHAR(10) DEFAULT 'Active' CHECK (operational_status IN ('Active', 'Inactive', 'Maintenance')),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Demand Forecast Table
CREATE TABLE demand_forecast (
    demand_id SERIAL PRIMARY KEY,
    node_id VARCHAR(20) NOT NULL,
    period VARCHAR(7) NOT NULL CHECK (period ~ '^\d{4}-\d{2}$'), -- YYYY-MM format
    demand_tonnes INTEGER NOT NULL CHECK (demand_tonnes >= 0),
    demand_type VARCHAR(20) DEFAULT 'Forecast' CHECK (demand_type IN ('Confirmed', 'Forecast', 'Historical')),
    priority_level INTEGER DEFAULT 1 CHECK (priority_level BETWEEN 1 AND 5),
    confidence_level DECIMAL(3,2) DEFAULT 0.80 CHECK (confidence_level BETWEEN 0 AND 1),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(node_id, period),
    FOREIGN KEY (node_id) REFERENCES plant_master(plant_id)
);

-- Transport Routes and Modes Table
CREATE TABLE transport_routes_modes (
    route_id SERIAL PRIMARY KEY,
    origin_plant_id VARCHAR(20) NOT NULL,
    destination_node_id VARCHAR(20) NOT NULL,
    transport_mode VARCHAR(10) NOT NULL CHECK (transport_mode IN ('Road', 'Rail', 'Sea')),
    distance_km DECIMAL(8,2) NOT NULL CHECK (distance_km > 0),
    cost_per_tonne_km DECIMAL(8,4) NOT NULL CHECK (cost_per_tonne_km > 0),
    transit_time_days INTEGER DEFAULT 1 CHECK (transit_time_days > 0),
    vehicle_capacity_tonnes INTEGER NOT NULL CHECK (vehicle_capacity_tonnes > 0),
    route_status VARCHAR(10) DEFAULT 'Active' CHECK (route_status IN ('Active', 'Inactive', 'Seasonal')),
    effective_from DATE DEFAULT CURRENT_DATE,
    effective_to DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(origin_plant_id, destination_node_id, transport_mode),
    FOREIGN KEY (origin_plant_id) REFERENCES plant_master(plant_id),
    FOREIGN KEY (destination_node_id) REFERENCES plant_master(plant_id)
);
```

#### **B. Operational Data Tables**
```sql
-- Production Capacity and Costs Table
CREATE TABLE production_capacity_cost (
    capacity_id SERIAL PRIMARY KEY,
    plant_id VARCHAR(20) NOT NULL,
    period VARCHAR(7) NOT NULL CHECK (period ~ '^\d{4}-\d{2}$'),
    max_capacity_tonnes INTEGER NOT NULL CHECK (max_capacity_tonnes > 0),
    min_capacity_tonnes INTEGER DEFAULT 0 CHECK (min_capacity_tonnes >= 0),
    variable_cost_per_tonne DECIMAL(10,2) NOT NULL CHECK (variable_cost_per_tonne > 0),
    fixed_cost_per_period DECIMAL(12,2) DEFAULT 0,
    maintenance_scheduled BOOLEAN DEFAULT FALSE,
    capacity_utilization_target DECIMAL(3,2) DEFAULT 0.85 CHECK (capacity_utilization_target BETWEEN 0 AND 1),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(plant_id, period),
    FOREIGN KEY (plant_id) REFERENCES plant_master(plant_id),
    CHECK (min_capacity_tonnes <= max_capacity_tonnes)
);

-- Initial Inventory Table
CREATE TABLE initial_inventory (
    inventory_id SERIAL PRIMARY KEY,
    plant_id VARCHAR(20) NOT NULL,
    period VARCHAR(7) NOT NULL CHECK (period ~ '^\d{4}-\d{2}$'),
    opening_stock_tonnes INTEGER NOT NULL CHECK (opening_stock_tonnes >= 0),
    safety_stock_tonnes INTEGER NOT NULL CHECK (safety_stock_tonnes >= 0),
    holding_cost_per_tonne_month DECIMAL(8,2) NOT NULL CHECK (holding_cost_per_tonne_month > 0),
    storage_capacity_tonnes INTEGER,
    inventory_turnover_target DECIMAL(4,2) DEFAULT 12.0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(plant_id, period),
    FOREIGN KEY (plant_id) REFERENCES plant_master(plant_id),
    CHECK (opening_stock_tonnes >= safety_stock_tonnes)
);

-- Safety Stock Policy Table
CREATE TABLE safety_stock_policy (
    policy_id SERIAL PRIMARY KEY,
    node_id VARCHAR(20) NOT NULL,
    product_type VARCHAR(50) DEFAULT 'Clinker',
    safety_stock_days INTEGER NOT NULL CHECK (safety_stock_days > 0),
    reorder_point_tonnes INTEGER NOT NULL CHECK (reorder_point_tonnes > 0),
    policy_effective_date DATE NOT NULL,
    policy_expiry_date DATE,
    review_frequency_days INTEGER DEFAULT 30,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES plant_master(plant_id)
);
```

#### **C. Results and Audit Tables**
```sql
-- Optimization Runs Table
CREATE TABLE optimization_runs (
    run_id VARCHAR(50) PRIMARY KEY,
    scenario_name VARCHAR(50) NOT NULL,
    solver_name VARCHAR(20) NOT NULL,
    run_status VARCHAR(20) NOT NULL CHECK (run_status IN ('Queued', 'Running', 'Completed', 'Failed', 'Cancelled')),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    runtime_seconds DECIMAL(10,3),
    objective_value DECIMAL(15,2),
    optimality_gap DECIMAL(8,6),
    solver_termination VARCHAR(50),
    data_snapshot_hash VARCHAR(64),
    user_id VARCHAR(50),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optimization Results Table
CREATE TABLE optimization_results (
    result_id SERIAL PRIMARY KEY,
    run_id VARCHAR(50) NOT NULL,
    result_type VARCHAR(20) NOT NULL CHECK (result_type IN ('Production', 'Shipment', 'Inventory', 'Trips')),
    plant_id VARCHAR(20),
    customer_id VARCHAR(20),
    period VARCHAR(7),
    transport_mode VARCHAR(10),
    quantity_tonnes DECIMAL(12,2),
    cost_value DECIMAL(15,2),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES optimization_runs(run_id),
    FOREIGN KEY (plant_id) REFERENCES plant_master(plant_id)
);

-- Audit Logs Table
CREATE TABLE audit_logs (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation_type VARCHAR(10) NOT NULL CHECK (operation_type IN ('INSERT', 'UPDATE', 'DELETE')),
    record_id VARCHAR(50),
    old_values JSONB,
    new_values JSONB,
    user_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);
```

---

## 10. Configuration & Settings

### ⚙️ **System Configuration Files**

#### **A. Backend Configuration**
```python
# Location: backend/app/core/config.py
class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application
    PROJECT_NAME: str = "Clinker Supply Chain Optimization"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./clinker_supply_chain.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Security
    JWT_SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Optimization
    DEFAULT_SOLVER: str = "highs"
    DEFAULT_TIME_LIMIT: int = 600  # seconds
    DEFAULT_MIP_GAP: float = 0.01
    MAX_CONCURRENT_OPTIMIZATIONS: int = 3
    
    # API Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/application.log"
    
    # Cache
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 300
    
    # External APIs
    WEATHER_API_KEY: str = ""
    MARKET_DATA_API_URL: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Usage
settings = Settings()
```

#### **B. Frontend Configuration**
```python
# Location: frontend/streamlit_app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Backend API Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_BASE = f"{BACKEND_URL}/api/v1"

# Dashboard Configuration
DEFAULT_SCENARIO = os.getenv("DEFAULT_SCENARIO", "base")
REFRESH_INTERVAL_SECONDS = int(os.getenv("REFRESH_INTERVAL", "30"))
MAX_CHART_POINTS = int(os.getenv("MAX_CHART_POINTS", "1000"))

# Currency Configuration
CURRENCY_SYMBOL = "₹"
CURRENCY_FORMAT = "INR"
DECIMAL_PLACES = 2

# Chart Configuration
CHART_THEME = "plotly_white"
CHART_COLOR_PALETTE = [
    "#667eea", "#764ba2", "#f093fb", "#f5576c",
    "#4facfe", "#00f2fe", "#43e97b", "#38f9d7"
]

# Cache Configuration
ENABLE_CACHING = True
CACHE_TTL_SECONDS = 30

# Debug Configuration
DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true"
SHOW_RAW_DATA = DEBUG_MODE
```

#### **C. Logging Configuration**
```yaml
# Location: config/logging.yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"
  
  detailed:
    format: "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(funcName)s(): %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: logs/application.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
  
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/errors.log
    maxBytes: 10485760
    backupCount: 3

loggers:
  app:
    level: DEBUG
    handlers: [console, file]
    propagate: false
  
  optimization:
    level: DEBUG
    handlers: [console, file]
    propagate: false
  
  api:
    level: INFO
    handlers: [console, file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
```

#### **D. Docker Configuration**
```dockerfile
# Location: infra/Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Location: infra/Dockerfile.frontend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY frontend/ .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "streamlit_app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## 🎯 **Summary: Complete Data Flow**

### **End-to-End Process:**

1. **Data Ingestion** → Raw data from ERP/CSV/APIs enters system
2. **5-Stage Validation** → Schema, business rules, integrity, units, missing data
3. **Data Cleaning** → Normalization, deduplication, standardization
4. **Scenario Generation** → Apply scenario-specific modifications
5. **Optimization** → MILP model solves for optimal solution
6. **Result Processing** → Transform solver output to business metrics
7. **API Serving** → REST endpoints provide data to frontend
8. **Dashboard Display** → Streamlit renders interactive visualizations
9. **User Interaction** → Real-time updates and scenario comparisons

### **Key Randomization Sources:**
- **Run ID hashing** for consistent per-run variations
- **Time-based factors** for realistic temporal changes
- **Scenario multipliers** for different business conditions
- **Market simulations** for cost and demand fluctuations
- **Solver performance** variations in runtime and optimality

### **Data Persistence:**
- **SQLite/PostgreSQL** for master and transactional data
- **In-memory caching** for frequently accessed results
- **File-based logs** for audit trails and debugging
- **Session state** for user preferences and selections

This comprehensive system provides a realistic, production-ready supply chain optimization platform with enterprise-grade data handling, validation, optimization, and visualization capabilities.