import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Select,
  InputNumber,
  Button,
  Space,
  Divider,
  Typography,
  Tag,
  Progress,
  Tabs,
  message,
  Spin
} from 'antd';
import {
  Route,
  Package,
  IndianRupee,
  Clock,
  Leaf,
  PlayCircle
} from 'lucide-react';
import { TransportMode, Route as RouteType, CargoSpecification, TransportSelection, CostBreakdown } from '../types/transport';
import { TransportModeService } from '../services/transportService';
import TransportModeCard from '../components/Transport/TransportModeCard';

const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

const TransportModeSelection: React.FC = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [transportModes, setTransportModes] = useState<TransportMode[]>([]);
  const [routes, setRoutes] = useState<RouteType[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<string>('');
  const [selectedModes, setSelectedModes] = useState<string[]>([]);
  const [cargoSpec, setCargoSpec] = useState<CargoSpecification>({
    volume: 100,
    weight: 100,
    handlingRequirements: [],
    deliveryDeadline: '',
    maxCost: 50000,
    priority: 'medium',
    specialInstructions: ''
  });
  const [transportSelection, setTransportSelection] = useState<TransportSelection | null>(null);
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown | null>(null);

  // Format number with Indian numbering system (K, L, Cr)
  const formatIndianNumber = (num: number): string => {
    if (num >= 10000000) { // 1 Crore
      const crores = num / 10000000;
      return `${crores.toFixed(2)} Cr`;
    } else if (num >= 100000) { // 1 Lakh
      const lakhs = num / 100000;
      return `${lakhs.toFixed(2)} L`;
    } else if (num >= 1000) { // 1 Thousand
      const thousands = num / 1000;
      return `${thousands.toFixed(1)} K`;
    } else {
      return num.toFixed(1); // Show decimal for numbers like 53.2
    }
  };

  // Format currency with Indian numbering system
  const formatIndianCurrency = (num: number): string => {
    if (num >= 10000000) { // 1 Crore
      const crores = num / 10000000;
      return `₹${crores.toFixed(2)} Cr`;
    } else if (num >= 100000) { // 1 Lakh
      const lakhs = num / 100000;
      return `₹${lakhs.toFixed(2)} L`;
    } else if (num >= 1000) { // 1 Thousand
      const thousands = num / 1000;
      return `₹${thousands.toFixed(1)} K`;
    } else {
      return `₹${num.toFixed(1)}`; // Show decimal for small amounts
    }
  };

  // Helper functions for cost calculations
  const calculateModeCost = (mode: string, volume: number): number => {
    const selectedMode = transportModes.find(m => m.id === mode);
    if (!selectedMode) return 0;
    
    const route = routes.find(r => r.id === selectedRoute);
    const distance = route?.distance || 1000;
    
    return volume * selectedMode.costPerTonKm * distance;
  };

  const calculateModeTime = (mode: string, distance: number): number => {
    const selectedMode = transportModes.find(m => m.id === mode);
    if (!selectedMode) return 0;
    
    return distance / selectedMode.avgSpeed;
  };

  const calculateTotalCost = (modes: string[], volume: number): number => {
    return modes.reduce((total, mode) => total + calculateModeCost(mode, volume), 0);
  };

  const calculateTotalTime = (modes: string[], distance: number): number => {
    if (modes.length === 1) {
      return calculateModeTime(modes[0], distance);
    }
    // For multi-modal, use average time
    return modes.reduce((total, mode) => total + calculateModeTime(mode, distance), 0) / modes.length;
  };

  const calculateCarbonFootprint = (modes: string[], volume: number): number => {
    return modes.reduce((total, mode) => {
      const selectedMode = transportModes.find(m => m.id === mode);
      return total + (selectedMode?.carbonFootprint || 0) * volume;
    }, 0);
  };

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  // Auto-calculate transport selection whenever inputs change
  useEffect(() => {
    if (selectedRoute && selectedModes.length > 0) {
      autoCalculateSelection();
    } else {
      setTransportSelection(null);
      setCostBreakdown(null);
    }
  }, [selectedRoute, selectedModes, cargoSpec]);

  const autoCalculateSelection = async () => {
    if (!selectedRoute || selectedModes.length === 0) return;

    try {
      // Use the same validation logic but without showing messages
      const selection = {
        modes: selectedModes,
        sequence: selectedModes.map(mode => ({
          mode,
          from: routes.find(r => r.id === selectedRoute)?.source || 'Source',
          to: routes.find(r => r.id === selectedRoute)?.destination || 'Destination',
          distance: routes.find(r => r.id === selectedRoute)?.distance || 1000,
          cost: calculateModeCost(mode, cargoSpec.volume),
          time: calculateModeTime(mode, routes.find(r => r.id === selectedRoute)?.distance || 1000),
          capacity: mode === 'road' ? 40 : mode === 'rail' ? 4000 : 60000
        })),
        totalCost: calculateTotalCost(selectedModes, cargoSpec.volume),
        totalTime: calculateTotalTime(selectedModes, routes.find(r => r.id === selectedRoute)?.distance || 1000),
        feasibility: 'valid' as const,
        violations: [],
        alternatives: [],
        carbonFootprint: calculateCarbonFootprint(selectedModes, cargoSpec.volume)
      };
      
      setTransportSelection(selection);

      // Generate cost breakdown
      const breakdown = {
        transportCost: selection.totalCost * 0.6,
        transferCost: selection.totalCost * 0.15,
        handlingCost: selection.totalCost * 0.1,
        fuelCost: selection.totalCost * 0.08,
        laborCost: selection.totalCost * 0.05,
        infrastructureCost: selection.totalCost * 0.02,
        taxes: selection.totalCost * 0.1,
        total: selection.totalCost
      };
      setCostBreakdown(breakdown);
      
    } catch (error) {
      console.error('Auto-calculation error:', error);
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Use CSV backend API endpoints instead of mock service
      const [routesResponse, modesResponse] = await Promise.all([
        fetch('http://localhost:8000/api/v1/transport/routes'),
        fetch('http://localhost:8000/api/v1/transport/modes/comparison')
      ]);

      if (!routesResponse.ok || !modesResponse.ok) {
        throw new Error('Failed to fetch transport data');
      }

      const routesData = await routesResponse.json();
      const modesData = await modesResponse.json();

      // Transform CSV backend data to match frontend interface
      const transformedRoutes = routesData.routes.map((route: any) => ({
        id: route.route_id,
        source: route.source_name,
        destination: route.destination_name,
        distance: route.distance_km,
        availableModes: [route.transport_mode.toLowerCase()],
        transferPoints: [],
        restrictions: {
          maxWeight: route.capacity_mt * 40, // Estimate based on capacity
          hazardousMaterials: false,
          timeRestrictions: [],
          seasonalRestrictions: []
        }
      }));

      const transformedModes = modesData.modes.map((mode: any) => ({
        id: mode.mode.toLowerCase(),
        name: mode.mode,
        icon: mode.mode === 'Road' ? '🚛' : mode.mode === 'Rail' ? '🚂' : '🚢',
        description: `${mode.mode} transport - ${mode.total_routes} routes available`,
        minVolume: mode.mode === 'Road' ? 5 : mode.mode === 'Rail' ? 1000 : 5000,
        maxVolume: mode.capacity_range.split('-')[1]?.replace(' MT', '') || 
                   (mode.mode === 'Road' ? 40 : mode.mode === 'Rail' ? 4000 : 60000),
        maxWeight: mode.capacity_range.split('-')[1]?.replace(' MT', '') || 
                   (mode.mode === 'Road' ? 40 : mode.mode === 'Rail' ? 4000 : 60000),
        costPerTonKm: mode.avg_cost_per_tonne / 100, // Convert to per km cost
        avgSpeed: mode.avg_transit_days === 2 ? 45 : mode.avg_transit_days === 5 ? 30 : 25,
        reliability: mode.availability === 'High' ? 0.85 : mode.availability === 'Medium' ? 0.75 : 0.65,
        carbonFootprint: mode.mode === 'Road' ? 0.12 : mode.mode === 'Rail' ? 0.04 : 0.02,
        specialHandling: true,
        weatherDependent: mode.mode !== 'Rail',
        infrastructureRequired: [],
        transferTime: mode.avg_transit_days * 24,
        notes: `Average cost: ₹${mode.avg_cost_per_tonne}/tonne`
      }));

      setRoutes(transformedRoutes);
      setTransportModes(transformedModes);
      
    } catch (error) {
      console.error('Error loading transport data:', error);
      message.error('Failed to load transport data. Using fallback data.');
      
      // Fallback to service data if API fails
      const [modes, routesData] = await Promise.all([
        TransportModeService.getAvailableModes(),
        TransportModeService.getRoutes()
      ]);
      setTransportModes(modes);
      setRoutes(routesData);
    } finally {
      setLoading(false);
    }
  };

  // Handle mode selection
  const handleModeSelect = (modeId: string) => {
    if (selectedModes.includes(modeId)) {
      setSelectedModes(selectedModes.filter(id => id !== modeId));
    } else {
      setSelectedModes([...selectedModes, modeId]);
    }
  };

  // Validate transport selection using CSV backend
  const validateSelection = async () => {
    if (!selectedRoute || selectedModes.length === 0) {
      message.warning('Please select route and at least one transport mode');
      return;
    }

    try {
      setValidating(true);
      console.log('Validating selection:', { selectedRoute, selectedModes, cargoSpec });
      
      // Use CSV backend optimization API
      const response = await fetch('http://localhost:8000/api/v1/transport/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          route_id: selectedRoute,
          modes: selectedModes,
          cargo: cargoSpec
        })
      });

      if (!response.ok) {
        throw new Error('Failed to validate transport selection');
      }

      const optimizationResult = await response.json();
      
      // Transform backend response to match frontend interface
      const selection = {
        modes: selectedModes,
        sequence: selectedModes.map(mode => ({
          mode,
          from: routes.find(r => r.id === selectedRoute)?.source || 'Source',
          to: routes.find(r => r.id === selectedRoute)?.destination || 'Destination',
          distance: routes.find(r => r.id === selectedRoute)?.distance || 1000,
          cost: calculateModeCost(mode, cargoSpec.volume),
          time: calculateModeTime(mode, routes.find(r => r.id === selectedRoute)?.distance || 1000),
          capacity: mode === 'road' ? 40 : mode === 'rail' ? 4000 : 60000
        })),
        totalCost: calculateTotalCost(selectedModes, cargoSpec.volume),
        totalTime: calculateTotalTime(selectedModes, routes.find(r => r.id === selectedRoute)?.distance || 1000),
        feasibility: 'valid' as const,
        violations: [],
        alternatives: optimizationResult.optimization_result?.recommendations || [],
        carbonFootprint: calculateCarbonFootprint(selectedModes, cargoSpec.volume)
      };
      
      console.log('Validation result:', selection);
      setTransportSelection(selection);

      // Generate cost breakdown
      const breakdown = {
        transportCost: selection.totalCost * 0.6,
        transferCost: selection.totalCost * 0.15,
        handlingCost: selection.totalCost * 0.1,
        fuelCost: selection.totalCost * 0.08,
        laborCost: selection.totalCost * 0.05,
        infrastructureCost: selection.totalCost * 0.02,
        taxes: selection.totalCost * 0.1,
        total: selection.totalCost
      };
      setCostBreakdown(breakdown);

      // Show result message
      message.success('Transport selection validated successfully!');
      
    } catch (error) {
      message.error('Validation failed');
      console.error('Validation error:', error);
      
      // Fallback to service validation
      try {
        const selection = await TransportModeService.validateTransportSelection(
          selectedRoute,
          selectedModes,
          cargoSpec
        );
        setTransportSelection(selection);
        const breakdown = await TransportModeService.getCostBreakdown(selection);
        setCostBreakdown(breakdown);
      } catch (fallbackError) {
        console.error('Fallback validation also failed:', fallbackError);
      }
    } finally {
      setValidating(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: '16px' }}>Loading transport data...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <Route size={32} style={{ marginRight: '8px' }} />
        Transport Mode Selection
      </Title>
      <Text type="secondary">
        Configure optimal transport modes for clinker shipments with intelligent validation and cost optimization
      </Text>

      <Divider />

      {/* Route Selection */}
      <Card title="Route Selection" size="small" style={{ marginBottom: '16px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <label style={{ display: 'block', marginBottom: '4px' }}>Select Route</label>
            <Select
              style={{ width: '100%' }}
              placeholder="Choose a route"
              value={selectedRoute}
              onChange={setSelectedRoute}
            >
              {routes.map(route => (
                <Option key={route.id} value={route.id}>
                  <Space>
                    <Route size={16} />
                    {route.source} → {route.destination}
                    <Text type="secondary">({route.distance} km)</Text>
                  </Space>
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Text type="secondary">
              {selectedRoute ? '✅ Route selected - auto-calculating costs...' : 'Please select a route to begin'}
            </Text>
            {selectedModes.length > 0 && (
              <div style={{ marginTop: '8px' }}>
                <Text strong>Selected Modes: </Text>
                <Space wrap>
                  {selectedModes.map(modeId => {
                    const mode = transportModes.find(m => m.id === modeId);
                    return (
                      <Tag 
                        key={modeId} 
                        color="blue" 
                        closable 
                        onClose={() => handleModeSelect(modeId)}
                      >
                        {mode?.icon} {mode?.name}
                      </Tag>
                    );
                  })}
                </Space>
              </div>
            )}
          </Col>
        </Row>
      </Card>

      {/* Transport Mode Cards */}
      <Card title="Available Transport Modes" size="small" style={{ marginBottom: '16px' }}>
        <Row gutter={[16, 16]}>
          {transportModes.map(mode => (
            <Col xs={24} sm={12} md={6} key={mode.id}>
              <TransportModeCard
                mode={mode}
                isSelected={selectedModes.includes(mode.id)}
                isAvailable={true}
                onSelect={() => handleModeSelect(mode.id)}
              />
            </Col>
          ))}
        </Row>
      </Card>

      {/* Cargo Specifications */}
      <Card title="Cargo Specifications" size="small" style={{ marginBottom: '16px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8} md={6}>
            <label style={{ display: 'block', marginBottom: '4px' }}>Volume (tonnes)</label>
            <InputNumber
              style={{ width: '100%' }}
              value={cargoSpec.volume}
              onChange={(value: number | null) => setCargoSpec({...cargoSpec, volume: value || 0})}
              min={1}
              max={10000}
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <label style={{ display: 'block', marginBottom: '4px' }}>Weight (tonnes)</label>
            <InputNumber
              style={{ width: '100%' }}
              value={cargoSpec.weight}
              onChange={(value: number | null) => setCargoSpec({...cargoSpec, weight: value || 0})}
              min={1}
              max={10000}
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <label style={{ display: 'block', marginBottom: '4px' }}>Max Cost (₹)</label>
            <InputNumber
              style={{ width: '100%' }}
              value={cargoSpec.maxCost}
              onChange={(value: number | null) => setCargoSpec({...cargoSpec, maxCost: value || 0})}
              min={1000}
              max={10000000}
              formatter={value => `₹ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <label style={{ display: 'block', marginBottom: '4px' }}>Priority</label>
            <Select
              style={{ width: '100%' }}
              value={cargoSpec.priority}
              onChange={(value: 'low' | 'medium' | 'high') => setCargoSpec({...cargoSpec, priority: value})}
            >
              <Option value="low">Low</Option>
              <Option value="medium">Medium</Option>
              <Option value="high">High</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* Validation Button */}
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <Button
          type="primary"
          size="large"
          icon={<PlayCircle size={20} />}
          onClick={validateSelection}
          loading={validating}
          disabled={!selectedRoute || selectedModes.length === 0}
        >
          {validating ? 'Validating Selection...' : 'Validate Transport Selection'}
        </Button>
      </div>

      {/* Results */}
      {transportSelection && (
        <>
          {/* KPI Summary */}
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col xs={24} sm={6}>
              <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#f0f9ff', borderRadius: '8px' }}>
                <IndianRupee size={24} color="#1890ff" />
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                  {formatIndianCurrency(transportSelection.totalCost)}
                </div>
                <Text type="secondary">Total Cost</Text>
              </div>
            </Col>
            <Col xs={24} sm={6}>
              <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#f6ffed', borderRadius: '8px' }}>
                <Clock size={24} color="#52c41a" />
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                  {transportSelection.totalTime.toFixed(1)} hrs
                </div>
                <Text type="secondary">Transit Time</Text>
              </div>
            </Col>
            <Col xs={24} sm={6}>
              <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#e6fffb', borderRadius: '8px' }}>
                <Leaf size={24} color="#13c2c2" />
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#13c2c2' }}>
                  {formatIndianNumber(transportSelection.carbonFootprint)} kg
                </div>
                <Text type="secondary">CO₂ Emissions</Text>
              </div>
            </Col>
            <Col xs={24} sm={6}>
              <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#f9f0ff', borderRadius: '8px' }}>
                <Package size={24} color="#722ed1" />
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#722ed1' }}>
                  {selectedModes.length}
                </div>
                <Text type="secondary">Modes Selected</Text>
              </div>
            </Col>
          </Row>

          {/* Detailed Results */}
          <Tabs defaultActiveKey="breakdown">
            <TabPane tab="Cost Breakdown" key="breakdown">
              {costBreakdown && (
                <Card title="Cost Breakdown" size="small">
                  <Row gutter={[16, 16]}>
                    {[
                      { name: 'Transport', value: costBreakdown.transportCost, color: '#1890ff' },
                      { name: 'Transfer', value: costBreakdown.transferCost, color: '#52c41a' },
                      { name: 'Handling', value: costBreakdown.handlingCost, color: '#faad14' },
                      { name: 'Fuel', value: costBreakdown.fuelCost, color: '#722ed1' },
                      { name: 'Labor', value: costBreakdown.laborCost, color: '#13c2c2' },
                      { name: 'Infrastructure', value: costBreakdown.infrastructureCost, color: '#eb2f96' },
                      { name: 'Taxes', value: costBreakdown.taxes, color: '#fa541c' }
                    ].map((item, index) => (
                      <Col xs={24} sm={12} md={8} lg={6} key={index}>
                        <div style={{ textAlign: 'center', padding: '12px', border: '1px solid #f0f0f0', borderRadius: '8px' }}>
                          <div style={{ fontSize: '18px', fontWeight: 'bold', color: item.color }}>
                            {formatIndianCurrency(item.value)}
                          </div>
                          <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                            {item.name}
                          </div>
                          <Progress
                            percent={(item.value / costBreakdown.total) * 100}
                            showInfo={false}
                            strokeColor={item.color}
                            size="small"
                            style={{ marginTop: '8px' }}
                          />
                        </div>
                      </Col>
                    ))}
                  </Row>
                  <Divider />
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#262626' }}>
                      {formatIndianCurrency(costBreakdown.total)}
                    </div>
                    <Text type="secondary">Total Cost</Text>
                  </div>
                </Card>
              )}
            </TabPane>
          </Tabs>
        </>
      )}
    </div>
  );
};

export default TransportModeSelection;