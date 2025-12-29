import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE || '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Types
export interface SystemHealth {
  status: string;
  optimization_ready: boolean;
  data_validation_status: string;
  alerts: Array<{
    level: string;
    message: string;
    timestamp: string;
  }>;
  services: {
    database: string;
    optimization_engine: string;
    data_validation: string;
  };
}

export interface DataHealthStatus {
  overall_status: string;
  optimization_ready: boolean;
  tables: Array<{
    table_name: string;
    status: string;
    record_count: number;
    last_updated: string;
    issues: string[];
  }>;
  validation_summary: {
    total_errors: number;
    total_warnings: number;
    blocking_errors: number;
  };
}

export interface ValidationReport {
  stages: Array<{
    stage: string;
    status: string;
    errors: Array<{
      table?: string;
      column?: string;
      error: string;
      severity: string;
    }>;
    warnings: Array<{
      table?: string;
      warning: string;
      impact: string;
    }>;
    row_level_errors: Array<{
      table: string;
      row: number;
      error: string;
      [key: string]: any;
    }>;
  }>;
  optimization_blocked: boolean;
  blocking_errors: string[];
}

export interface OptimizationRun {
  run_id: string;
  scenario_name: string;
  status: string;
  progress: number;
  start_time: string;
  estimated_completion?: string;
  error_message?: string;
  solver_name?: string;
  objective_value?: number;
  solve_time?: number;
}

export interface OptimizationResults {
  run_id: string;
  scenario_name: string;
  status: string;
  objective_value: number;
  solve_time: number;
  solver_status: string;
  cost_breakdown: {
    production_cost: number;
    transport_cost: number;
    fixed_trip_cost: number;
    holding_cost: number;
    penalty_cost: number;
  };
  production_plan: Array<{
    plant_id: string;
    period: string;
    production_tonnes: number;
  }>;
  shipment_plan: Array<{
    origin_plant_id: string;
    destination_node_id: string;
    period: string;
    transport_mode: string;
    shipment_tonnes: number;
  }>;
  utilization_metrics: {
    production_utilization: number;
    transport_utilization: number;
    inventory_turns: number;
  };
  service_metrics: {
    demand_fulfillment_rate: number;
    stockout_events: number;
    service_level: number;
  };
}

export interface KPIDashboard {
  scenario_name: string;
  run_id: string;
  timestamp: string;
  total_cost: number;
  cost_breakdown: {
    production_cost: number;
    transport_cost: number;
    fixed_trip_cost: number;
    holding_cost: number;
    penalty_cost: number;
  };
  production_utilization: Array<{
    plant_name: string;
    plant_id: string;
    production_used: number;
    production_capacity: number;
    utilization_pct: number;
  }>;
  transport_utilization: Array<{
    from: string;
    to: string;
    mode: string;
    trips: number;
    capacity_used_pct: number;
    sbq_compliance: string;
    violations: number;
  }>;
  service_performance: {
    demand_fulfillment_rate: number;
    on_time_delivery: number;
    average_lead_time_days: number;
    service_level: number;
    stockout_triggered: boolean;
  };
  inventory_metrics: {
    safety_stock_compliance: number;
    average_inventory_days: number;
    stockout_events: number;
    inventory_turns: number;
  };
}

// API Functions
export const fetchSystemHealth = async (): Promise<SystemHealth> => {
  const response = await api.get('/health');
  return response.data;
};

export const fetchDataHealth = async (): Promise<DataHealthStatus> => {
  const response = await api.get('/dashboard/health-status');
  return response.data;
};

export const fetchValidationReport = async (): Promise<ValidationReport> => {
  const response = await api.get('/data/validation-report');
  return response.data;
};

export const runOptimization = async (params: {
  scenario_name: string;
  solver: string;
  time_limit: number;
  mip_gap: number;
}): Promise<{ run_id: string; status: string; message: string }> => {
  const response = await api.post('/optimize/optimize', params);
  return response.data;
};

export const fetchOptimizationStatus = async (runId: string): Promise<OptimizationRun> => {
  const response = await api.get(`/optimize/optimize/${runId}/status`);
  return response.data;
};

export const fetchOptimizationResults = async (runId: string): Promise<OptimizationResults> => {
  const response = await api.get(`/optimize/optimize/${runId}/results`);
  return response.data;
};

export const fetchKPIDashboard = async (scenarioName: string): Promise<KPIDashboard> => {
  const response = await api.get(`/kpi/dashboard/${scenarioName}`);
  return response.data;
};

export const fetchScenarios = async (): Promise<Array<{
  name: string;
  description: string;
  status?: string;
  last_run?: string;
}>> => {
  const response = await api.get('/optimize/scenarios');
  return response.data.scenarios || [];
};

export const fetchOptimizationRuns = async (): Promise<OptimizationRun[]> => {
  const response = await api.get('/optimize/runs');
  return response.data.runs || [];
};

export const compareScenarios = async (scenarios: string[]): Promise<{
  scenarios: Array<{
    scenario_name: string;
    total_cost: number;
    cost_breakdown: any;
    service_level: number;
    utilization: number;
  }>;
  recommendations: string[];
}> => {
  const response = await api.post('/kpi/compare', { scenarios });
  return response.data;
};

export default api;