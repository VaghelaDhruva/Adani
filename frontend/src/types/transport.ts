export interface TransportMode {
  id: string;
  name: string;
  icon: string;
  description: string;
  minVolume: number; // tonnes
  maxVolume: number; // tonnes
  maxWeight: number; // tonnes
  costPerTonKm: number; // INR
  avgSpeed: number; // km/h
  reliability: number; // 0-1
  carbonFootprint: number; // kg CO2/tonne-km
  specialHandling: boolean;
  weatherDependent: boolean;
  infrastructureRequired: string[];
  transferTime: number; // hours for multi-modal transfers
  notes?: string; // Additional industry-specific notes
}

export interface Route {
  id: string;
  source: string;
  destination: string;
  distance: number; // km
  availableModes: string[];
  transferPoints: TransferPoint[];
  restrictions: RouteRestrictions;
}

export interface TransferPoint {
  id: string;
  name: string;
  location: string;
  availableModes: string[];
  transferTime: number; // hours
  transferCost: number; // INR per tonne
  equipment: string[];
  capacity: number; // tonnes
}

export interface RouteRestrictions {
  maxWeight: number;
  hazardousMaterials: boolean;
  timeRestrictions: string[];
  seasonalRestrictions: string[];
}

export interface CargoSpecification {
  volume: number; // tonnes
  weight: number; // tonnes
  handlingRequirements: string[];
  deliveryDeadline: string;
  maxCost: number; // INR
  priority: 'low' | 'medium' | 'high';
  specialInstructions: string;
}

export interface TransportSelection {
  modes: string[];
  sequence: ModeSequence[];
  totalCost: number;
  totalTime: number;
  feasibility: 'valid' | 'warning' | 'invalid';
  violations: ConstraintViolation[];
  alternatives: AlternativeOption[];
  carbonFootprint: number;
}

export interface ModeSequence {
  mode: string;
  from: string;
  to: string;
  distance: number;
  cost: number;
  time: number;
  capacity: number;
}

export interface ConstraintViolation {
  type: 'volume' | 'weight' | 'route' | 'time' | 'cost' | 'handling';
  severity: 'error' | 'warning' | 'info';
  message: string;
  suggestion: string;
  affectedMode: string;
}

export interface AlternativeOption {
  modes: string[];
  cost: number;
  time: number;
  feasibility: 'valid' | 'warning' | 'invalid';
  advantages: string[];
  disadvantages: string[];
}

export interface CostBreakdown {
  transportCost: number;
  transferCost: number;
  handlingCost: number;
  fuelCost: number;
  laborCost: number;
  infrastructureCost: number;
  taxes: number;
  total: number;
}

export interface OptimizationConstraints {
  modePreferences: Record<string, number>; // mode: preference score
  maxTransitTime: number; // hours
  maxCost: number; // INR
  minReliability: number; // 0-1
  maxCarbonFootprint: number; // kg CO2
  requiredModes: string[];
  excludedModes: string[];
}
