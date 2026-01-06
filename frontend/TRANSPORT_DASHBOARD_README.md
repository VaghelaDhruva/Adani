# Transport Mode Selection React Dashboard

## Overview

This is a comprehensive React-based dashboard for the Transport Mode Selection feature in the Clinker Supply Chain Optimization system. The dashboard provides an intuitive interface for configuring transportation preferences, validating constraints, and optimizing transport mode combinations.

## Features

### 🚛 Transport Mode Configuration
- **Multi-Mode Selection**: Choose from Road, Rail, Sea, and Air transport modes
- **Smart Validation**: Real-time constraint validation for volume, weight, and handling requirements
- **Multi-Modal Support**: Configure complex transport sequences (e.g., Sea + Rail + Road)
- **Visual Mode Cards**: Interactive cards displaying mode characteristics and constraints

### 📊 Route Management
- **Route Selection**: Choose from predefined routes with available transport modes
- **Distance Calculation**: Automatic distance and transit time calculations
- **Transfer Points**: Support for multi-modal transfer infrastructure
- **Route Restrictions**: Handle route-specific constraints and limitations

### 📦 Cargo Specifications
- **Volume & Weight**: Configure cargo dimensions and weight
- **Priority Settings**: Set delivery priority (Low, Medium, High)
- **Cost Constraints**: Define maximum acceptable transportation costs
- **Special Requirements**: Specify handling and delivery requirements

### ✅ Intelligent Validation
- **Constraint Checking**: Validate against mode-specific constraints
- **Feasibility Analysis**: Determine if selections are feasible
- **Violation Reporting**: Detailed violation messages with suggestions
- **Alternative Options**: Suggest viable alternatives for invalid selections

### 💰 Cost Analysis
- **Real-Time Cost Calculation**: Instant cost estimates for selected modes
- **Cost Breakdown**: Detailed breakdown by transport, transfer, handling, fuel, labor, infrastructure, and taxes
- **Cost Comparison**: Compare costs across different mode combinations
- **Budget Validation**: Check against maximum cost constraints

### 🌍 Environmental Impact
- **Carbon Footprint Calculation**: Calculate CO₂ emissions for transport selections
- **Environmental Scoring**: Compare environmental impact of different modes
- **Sustainability Metrics**: Track sustainability KPIs

### 🔄 Alternative Analysis
- **Smart Alternatives**: Generate alternative transport mode combinations
- **Advantages/Disadvantages**: Detailed analysis of each alternative
- **Cost-Time Trade-offs**: Balance between cost and delivery time
- **Feasibility Comparison**: Compare feasibility of different options

## Architecture

### Component Structure
```
src/
├── components/
│   └── Transport/
│       └── TransportModeCard.tsx    # Individual transport mode cards
├── pages/
│   └── TransportModeSelection.tsx   # Main dashboard page
├── services/
│   └── transportService.ts          # Business logic and API calls
├── types/
│   └── transport.ts                  # TypeScript type definitions
└── App.tsx                          # Main application routing
```

### Key Components

#### TransportModeCard
- Displays individual transport mode information
- Shows mode characteristics, constraints, and metrics
- Handles selection state and availability
- Displays constraint violations and warnings

#### TransportModeSelection (Main Dashboard)
- Route selection and configuration
- Cargo specification forms
- Transport mode selection grid
- Validation results display
- Cost breakdown analysis
- Alternative options comparison

#### TransportService
- Business logic for transport mode validation
- Cost calculation algorithms
- Constraint validation engine
- Alternative generation logic
- Mock data service (replace with real API)

### Data Models

#### TransportMode
```typescript
interface TransportMode {
  id: string;
  name: string;
  icon: string;
  description: string;
  minVolume: number;
  maxVolume: number;
  maxWeight: number;
  costPerTonKm: number;
  avgSpeed: number;
  reliability: number;
  carbonFootprint: number;
  specialHandling: boolean;
  weatherDependent: boolean;
  infrastructureRequired: string[];
  transferTime: number;
}
```

#### TransportSelection
```typescript
interface TransportSelection {
  modes: string[];
  sequence: ModeSequence[];
  totalCost: number;
  totalTime: number;
  feasibility: 'valid' | 'warning' | 'invalid';
  violations: ConstraintViolation[];
  alternatives: AlternativeOption[];
  carbonFootprint: number;
}
```

## User Interface

### Main Sections

#### 1. Route Selection
- Dropdown to select source-destination routes
- Display route distance and available modes
- Clear and validate buttons

#### 2. Cargo Specifications
- Volume and weight inputs
- Priority selection
- Maximum cost constraint
- Special requirements field

#### 3. Transport Mode Grid
- Interactive cards for each transport mode
- Visual indicators for availability and selection
- Real-time constraint violation display
- Mode characteristics and metrics

#### 4. Validation Results
- Feasibility status with color coding
- Total cost, time, and carbon footprint
- Detailed constraint violations with suggestions
- Progress indicators for key metrics

#### 5. Cost Breakdown
- Visual cost breakdown by category
- Percentage distribution
- Total cost summary
- Category-wise cost details

#### 6. Alternative Options
- Table of alternative transport combinations
- Cost, time, and feasibility comparison
- Advantages and disadvantages for each alternative
- Interactive selection capability

### Visual Design

#### Color Scheme
- **Primary**: Blue (#1890ff) for primary actions and selections
- **Success**: Green (#52c41a) for valid selections and positive indicators
- **Warning**: Orange (#faad14) for warnings and cautions
- **Error**: Red (#ff4d4f) for errors and invalid selections
- **Info**: Cyan (#13c2c2) for information and neutral indicators

#### Icons
- Lucide React icons for consistent iconography
- Mode-specific icons (🚛 Road, 🚂 Rail, 🚢 Sea, ✈️ Air)
- Status indicators (✅ Valid, ⚠️ Warning, ❌ Invalid)
- Metric icons (💰 Cost, ⏱️ Time, 🌿 Carbon, 📦 Package)

#### Layout
- Responsive grid layout for transport mode cards
- Tabbed interface for results sections
- Card-based design for organized information display
- Consistent spacing and typography

## Business Logic

### Validation Engine

#### Constraint Validation
1. **Volume Constraints**: Check against mode minimum/maximum volumes
2. **Weight Constraints**: Validate weight limits per mode
3. **Route Constraints**: Ensure mode availability on selected route
4. **Cost Constraints**: Check against maximum cost limits
5. **Time Constraints**: Validate delivery deadlines
6. **Handling Constraints**: Check special handling requirements

#### Feasibility Analysis
- **Valid**: No violations or only informational warnings
- **Warning**: Minor violations that don't prevent execution
- **Invalid**: Critical violations that prevent execution

#### Alternative Generation
- Single-mode alternatives for all available modes
- Multi-modal combinations for complex routes
- Cost-optimized alternatives
- Time-optimized alternatives

### Cost Calculation

#### Cost Components
1. **Transport Cost**: Base transportation cost (60% of total)
2. **Transfer Cost**: Mode transfer costs (15% of total)
3. **Handling Cost**: Cargo handling costs (10% of total)
4. **Fuel Cost**: Fuel consumption costs (8% of total)
5. **Labor Cost**: Labor costs (5% of total)
6. **Infrastructure Cost**: Infrastructure usage costs (2% of total)
7. **Taxes**: Applicable taxes and fees (10% of total)

#### Calculation Formula
```
Total Cost = Σ(Mode Cost) + Σ(Transfer Costs) + Σ(Handling Costs)
Mode Cost = Volume × Cost per Ton-Km × Distance
```

### Environmental Impact

#### Carbon Footprint Calculation
```
Total CO₂ = Σ(Mode Carbon Footprint × Volume × Distance)
```

#### Environmental Scoring
- **Low Impact**: ≤ 0.05 kg CO₂/tonne-km (Rail, Sea)
- **Medium Impact**: 0.05 - 0.2 kg CO₂/tonne-km (Road)
- **High Impact**: > 0.2 kg CO₂/tonne-km (Air)

## Integration Points

### API Integration
- **Transport Modes API**: GET /api/transport/modes
- **Routes API**: GET /api/transport/routes
- **Validation API**: POST /api/transport/validate
- **Cost Calculation API**: POST /api/transport/cost-breakdown

### Backend Integration
- **Optimization Model**: Pass transport constraints to Pyomo model
- **Database**: Store transport configurations and preferences
- **External APIs**: Real-time transport cost and availability data

### Frontend Integration
- **Navigation**: Added to main sidebar navigation
- **Routing**: New route `/transport` for the dashboard
- **State Management**: React state for local component state
- **Data Fetching**: React Query for server state (to be implemented)

## Development Setup

### Prerequisites
- Node.js 16+
- React 18+
- Ant Design 5+
- TypeScript 4+

### Installation
```bash
cd frontend
npm install
```

### Development
```bash
npm start
```

### Build
```bash
npm build
```

## Testing

### Unit Tests
- Component rendering tests
- Validation logic tests
- Cost calculation tests
- Constraint checking tests

### Integration Tests
- API integration tests
- End-to-end workflow tests
- Multi-modal selection tests

### User Testing
- Usability testing
- Performance testing
- Accessibility testing

## Future Enhancements

### Advanced Features
- **AI-Powered Recommendations**: Machine learning for optimal mode suggestions
- **Real-Time Tracking**: Integration with transport tracking systems
- **Dynamic Pricing**: Real-time transport cost updates
- **Route Optimization**: Advanced route planning algorithms
- **Weather Integration**: Weather-based mode availability and cost adjustments

### Performance Optimizations
- **Caching**: Implement intelligent caching for transport data
- **Lazy Loading**: Load complex components on demand
- **Virtualization**: Handle large datasets efficiently
- **Optimization**: Reduce bundle size and improve load times

### User Experience Improvements
- **Drag-and-Drop**: Visual mode sequence builder
- **Map Integration**: Interactive route visualization
- **Mobile Support**: Responsive design for mobile devices
- **Accessibility**: WCAG 2.1 compliance

## Troubleshooting

### Common Issues

#### Mode Selection Not Working
- Check if route is selected
- Verify mode availability for selected route
- Check constraint violations

#### Cost Calculation Errors
- Verify cargo specifications
- Check route distance data
- Validate mode cost parameters

#### Validation Failures
- Review constraint violation messages
- Check cargo compatibility with selected modes
- Verify route restrictions

### Debug Mode
- Enable debug mode in browser console
- Check network requests in browser dev tools
- Review component state in React DevTools

## Support

For technical support and questions:
- Check the troubleshooting section
- Review the API documentation
- Contact the development team

---

**Note**: This dashboard is part of the Clinker Supply Chain Optimization system and integrates with the broader logistics platform.
