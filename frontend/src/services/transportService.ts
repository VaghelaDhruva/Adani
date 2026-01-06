import { TransportMode, Route, CargoSpecification, TransportSelection, ModeSequence, ConstraintViolation, AlternativeOption, CostBreakdown } from '../types/transport';

// Industry-accurate transportation data for clinker logistics
export const transportModes: TransportMode[] = [
  {
    id: 'road',
    name: 'Road',
    icon: '🚛',
    description: 'Flexible door-to-door transport for medium distances (25-40 tonne trucks)',
    minVolume: 5,
    maxVolume: 40,
    maxWeight: 40,
    costPerTonKm: 4.0,
    avgSpeed: 45,
    reliability: 0.78,
    carbonFootprint: 0.12,
    specialHandling: true,
    weatherDependent: true,
    infrastructureRequired: ['highways', 'loading_docks', 'cement_silos'],
    transferTime: 2,
    notes: 'Requires covered trucks for dust protection'
  },
  {
    id: 'rail',
    name: 'Rail',
    icon: '🚂',
    description: 'Cost-effective bulk transport for long distances (full rake: 1500-4000 tonnes)',
    minVolume: 1500,
    maxVolume: 4000,
    maxWeight: 4000,
    costPerTonKm: 1.0,
    avgSpeed: 30,
    reliability: 0.87,
    carbonFootprint: 0.04,
    specialHandling: true,
    weatherDependent: false,
    infrastructureRequired: ['railway_lines', 'loading_facilities', 'cement_terminals'],
    transferTime: 6,
    notes: 'Requires BOXN covered wagons, full rake loading'
  },
  {
    id: 'sea',
    name: 'Sea',
    icon: '🚢',
    description: 'Economical for very large volumes and coastal routes (5000-60000 tonnes)',
    minVolume: 5000,
    maxVolume: 60000,
    maxWeight: 60000,
    costPerTonKm: 0.4,
    avgSpeed: 30,
    reliability: 0.87,
    carbonFootprint: 0.02,
    specialHandling: true,
    weatherDependent: true,
    infrastructureRequired: ['ports', 'container_facilities', 'cement_terminals'],
    transferTime: 24,
    notes: 'Requires specialized cement terminals and covered vessels'
  },
  {
    id: 'air',
    name: 'Air',
    icon: '✈️',
    description: 'Emergency transport only - samples and urgent small shipments (<500 kg)',
    minVolume: 0.1,
    maxVolume: 0.5,
    maxWeight: 0.5,
    costPerTonKm: 75.0,
    avgSpeed: 700,
    reliability: 0.92,
    carbonFootprint: 0.6,
    specialHandling: true,
    weatherDependent: true,
    infrastructureRequired: ['airports', 'cargo_terminals', 'special_handling'],
    transferTime: 8,
    notes: 'Not recommended for bulk clinker - emergency samples only'
  }
];

export const routes: Route[] = [
  {
    id: 'route_1',
    source: 'Mumbai Plant',
    destination: 'Delhi Distribution Center',
    distance: 1420,
    availableModes: ['road', 'rail'],
    transferPoints: [
      {
        id: 'tp_1',
        name: 'Vadodara Junction',
        location: 'Vadodara',
        availableModes: ['road', 'rail'],
        transferTime: 4,
        transferCost: 1500,
        equipment: ['cement_silos', 'bulk_loaders', 'conveyors'],
        capacity: 2000
      }
    ],
    restrictions: {
      maxWeight: 4000,
      hazardousMaterials: false,
      timeRestrictions: ['monsoon_road_delays'],
      seasonalRestrictions: ['monsoon', 'winter_fog']
    }
  },
  {
    id: 'route_2',
    source: 'Mumbai Plant',
    destination: 'Chennai Port',
    distance: 1330,
    availableModes: ['road', 'rail', 'sea'],
    transferPoints: [
      {
        id: 'tp_2',
        name: 'Bangalore Logistics Hub',
        location: 'Bangalore',
        availableModes: ['road', 'rail'],
        transferTime: 5,
        transferCost: 2000,
        equipment: ['cement_terminals', 'covered_storage', 'bagging_facilities'],
        capacity: 3000
      }
    ],
    restrictions: {
      maxWeight: 60000,
      hazardousMaterials: false,
      timeRestrictions: [],
      seasonalRestrictions: ['cyclone_season']
    }
  },
  {
    id: 'route_3',
    source: 'Kolkata Plant',
    destination: 'Delhi Distribution Center',
    distance: 1540,
    availableModes: ['road', 'rail'],
    transferPoints: [
      {
        id: 'tp_3',
        name: 'Varanasi Transfer Point',
        location: 'Varanasi',
        availableModes: ['road', 'rail'],
        transferTime: 4,
        transferCost: 1800,
        equipment: ['cement_silos', 'bulk_loaders'],
        capacity: 2500
      }
    ],
    restrictions: {
      maxWeight: 4000,
      hazardousMaterials: false,
      timeRestrictions: [],
      seasonalRestrictions: ['monsoon', 'winter_fog']
    }
  },
  {
    id: 'route_4',
    source: 'Mumbai Plant',
    destination: 'Kolkata Distribution Center',
    distance: 2100,
    availableModes: ['road', 'rail', 'sea'],
    transferPoints: [
      {
        id: 'tp_4',
        name: 'Nagpur Hub',
        location: 'Nagpur',
        availableModes: ['road', 'rail'],
        transferTime: 4,
        transferCost: 1600,
        equipment: ['cement_silos', 'bulk_loaders'],
        capacity: 2000
      }
    ],
    restrictions: {
      maxWeight: 60000,
      hazardousMaterials: false,
      timeRestrictions: [],
      seasonalRestrictions: ['monsoon']
    }
  }
];

export class TransportModeService {
  static async getAvailableModes(): Promise<TransportMode[]> {
    // Simulate API call
    return new Promise(resolve => {
      setTimeout(() => resolve(transportModes), 500);
    });
  }

  static async getRoutes(): Promise<Route[]> {
    // Simulate API call
    return new Promise(resolve => {
      setTimeout(() => resolve(routes), 500);
    });
  }

  static async validateTransportSelection(
    routeId: string,
    selectedModes: string[],
    cargo: CargoSpecification
  ): Promise<TransportSelection> {
    // Simulate validation logic
    const route = routes.find(r => r.id === routeId);
    if (!route) {
      throw new Error('Route not found');
    }

    const violations: ConstraintViolation[] = [];
    let totalCost = 0;
    let totalTime = 0;
    const sequence: ModeSequence[] = [];

    // Validate each selected mode
    for (const modeId of selectedModes) {
      const mode = transportModes.find(m => m.id === modeId);
      if (!mode) continue;

      // Volume validation - changed to warning instead of error
      if (cargo.volume < mode.minVolume) {
        violations.push({
          type: 'volume',
          severity: 'warning',
          message: `Volume below minimum for ${mode.name} (min: ${mode.minVolume} tonnes, current: ${cargo.volume} tonnes)`,
          suggestion: `Consider increasing volume or this mode may not be cost-effective`,
          affectedMode: modeId
        });
      }

      // Weight validation - only error if significantly over capacity
      if (cargo.weight > mode.maxWeight * 1.1) {
        violations.push({
          type: 'weight',
          severity: 'error',
          message: `Weight exceeds maximum for ${mode.name}`,
          suggestion: `Reduce weight to ${mode.maxWeight} tonnes or split shipment`,
          affectedMode: modeId
        });
      } else if (cargo.weight > mode.maxWeight) {
        violations.push({
          type: 'weight',
          severity: 'warning',
          message: `Weight approaches maximum for ${mode.name}`,
          suggestion: `Monitor weight closely or consider splitting shipment`,
          affectedMode: modeId
        });
      }

      // Cost calculation
      const modeCost = cargo.volume * mode.costPerTonKm * (route.distance / 1000);
      const modeTime = route.distance / mode.avgSpeed;

      totalCost += modeCost;
      totalTime += modeTime;

      sequence.push({
        mode: modeId,
        from: route.source,
        to: route.destination,
        distance: route.distance,
        cost: modeCost,
        time: modeTime,
        capacity: mode.maxVolume
      });
    }

    // Multi-modal transfer costs
    if (selectedModes.length > 1) {
      const transferCost = route.transferPoints.reduce((sum, tp) => sum + tp.transferCost, 0);
      const transferTime = route.transferPoints.reduce((sum, tp) => sum + tp.transferTime, 0);
      
      totalCost += transferCost;
      totalTime += transferTime;
    }

    // Check cost constraint
    if (totalCost > cargo.maxCost) {
      violations.push({
        type: 'cost',
        severity: 'warning',
        message: `Total cost (₹${totalCost.toLocaleString()}) exceeds budget (₹${cargo.maxCost.toLocaleString()})`,
        suggestion: 'Consider alternative modes or increase budget',
        affectedMode: 'all'
      });
    }

    // Generate alternatives
    const alternatives = this.generateAlternatives(route, cargo, selectedModes);

    // Determine feasibility - only invalid if there are actual errors
    let feasibility: 'valid' | 'warning' | 'invalid' = 'valid';
    const hasErrors = violations.some(v => v.severity === 'error');
    const hasWarnings = violations.some(v => v.severity === 'warning');

    if (hasErrors) feasibility = 'invalid';
    else if (hasWarnings) feasibility = 'warning';

    // Calculate carbon footprint
    const carbonFootprint = sequence.reduce((total, seq) => {
      const mode = transportModes.find(m => m.id === seq.mode);
      return total + (mode?.carbonFootprint || 0) * cargo.volume * seq.distance;
    }, 0);

    return {
      modes: selectedModes,
      sequence,
      totalCost,
      totalTime,
      feasibility,
      violations,
      alternatives,
      carbonFootprint
    };
  }

  private static generateAlternatives(
    route: Route,
    cargo: CargoSpecification,
    currentSelection: string[]
  ): AlternativeOption[] {
    const alternatives: AlternativeOption[] = [];

    // Generate single-mode alternatives
    route.availableModes.forEach(modeId => {
      if (!currentSelection.includes(modeId)) {
        const mode = transportModes.find(m => m.id === modeId);
        if (mode && cargo.volume >= mode.minVolume && cargo.weight <= mode.maxWeight) {
          const cost = cargo.volume * mode.costPerTonKm * (route.distance / 1000);
          const time = route.distance / mode.avgSpeed;

          alternatives.push({
            modes: [modeId],
            cost,
            time,
            feasibility: 'valid',
            advantages: [`Lower cost: ₹${cost.toFixed(0)}`, `Direct transport`],
            disadvantages: [`Longer transit time: ${time.toFixed(1)} hours`]
          });
        }
      }
    });

    // Generate multi-modal alternatives
    if (route.availableModes.length >= 2) {
      const modeCombo = route.availableModes.slice(0, 2);
      const combinedCost = modeCombo.reduce((sum, modeId) => {
        const mode = transportModes.find(m => m.id === modeId);
        return sum + (mode ? cargo.volume * mode.costPerTonKm * (route.distance / 1000) : 0);
      }, 0);

      const combinedTime = modeCombo.reduce((sum, modeId) => {
        const mode = transportModes.find(m => m.id === modeId);
        return sum + (mode ? route.distance / mode.avgSpeed : 0);
      }, 0);

      alternatives.push({
        modes: modeCombo,
        cost: combinedCost,
        time: combinedTime,
        feasibility: 'valid',
        advantages: ['Balanced cost and time', 'Flexible routing'],
        disadvantages: ['Complex coordination', 'Transfer risks']
      });
    }

    return alternatives.sort((a, b) => a.cost - b.cost).slice(0, 3);
  }

  static async getCostBreakdown(selection: TransportSelection): Promise<CostBreakdown> {
    const transportCost = selection.totalCost * 0.6;
    const transferCost = selection.totalCost * 0.15;
    const handlingCost = selection.totalCost * 0.1;
    const fuelCost = selection.totalCost * 0.08;
    const laborCost = selection.totalCost * 0.05;
    const infrastructureCost = selection.totalCost * 0.02;
    const taxes = selection.totalCost * 0.1;

    return {
      transportCost,
      transferCost,
      handlingCost,
      fuelCost,
      laborCost,
      infrastructureCost,
      taxes,
      total: selection.totalCost
    };
  }
}
