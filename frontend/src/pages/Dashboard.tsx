import React, { useState } from 'react';
import { Row, Col, Card, Statistic, Select, Spin, Alert, Typography, Space } from 'antd';
import { useQuery } from 'react-query';
import { 
  DollarOutlined, 
  TruckOutlined, 
  BuildOutlined, 
  CheckCircleOutlined,
  WarningOutlined 
} from '@ant-design/icons';
import { fetchKPIDashboard, fetchScenarios } from '../services/api';
import CostBreakdownChart from '../components/Charts/CostBreakdownChart';
import ProductionUtilizationChart from '../components/Charts/ProductionUtilizationChart';
import ServiceMetricsChart from '../components/Charts/ServiceMetricsChart';
import TransportUtilizationTable from '../components/Tables/TransportUtilizationTable';
import { formatIndianCurrency, formatIndianNumber } from '../utils/numberFormat';

const { Title, Text } = Typography;

const Dashboard = () => {
  const [selectedScenario, setSelectedScenario] = useState('base');

  const { data: scenarios, isLoading: scenariosLoading } = useQuery(
    'scenarios',
    fetchScenarios
  );

  const { 
    data: kpiData, 
    isLoading: kpiLoading, 
    error: kpiError,
    refetch: refetchKPI 
  } = useQuery(
    ['kpi-dashboard', selectedScenario],
    () => fetchKPIDashboard(selectedScenario),
    {
      enabled: !!selectedScenario,
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  if (kpiError) {
    return (
      <Alert
        message="Error Loading Dashboard"
        description="Failed to load KPI data. Please check your connection and try again."
        type="error"
        showIcon
        action={
          <button onClick={() => refetchKPI()}>
            Retry
          </button>
        }
      />
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Space direction="vertical" size="small">
          <Title level={2} style={{ margin: 0, color: '#1f4e79' }}>
            KPI Dashboard
          </Title>
          <Text type="secondary">
            Real-time supply chain optimization metrics and performance indicators
          </Text>
        </Space>
        
        <div style={{ marginTop: 16 }}>
          <Space>
            <Text strong>Scenario:</Text>
            <Select
              value={selectedScenario}
              onChange={setSelectedScenario}
              style={{ width: 200 }}
              loading={scenariosLoading}
              options={scenarios?.map(scenario => ({
                key: scenario.name,
                value: scenario.name,
                label: `${scenario.name} - ${scenario.description || scenario.name}`
              })) || []}
            />
          </Space>
        </div>
      </div>

      {kpiLoading ? (
        <div style={{ textAlign: 'center', padding: '50px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text>Loading optimization results...</Text>
          </div>
        </div>
      ) : (
        <>
          {/* Key Metrics Row */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <Statistic
                  title="Total Cost"
                  value={kpiData?.total_cost || 0}
                  formatter={(value) => formatIndianCurrency(Number(value))}
                  prefix={<DollarOutlined style={{ color: '#1f4e79' }} />}
                  valueStyle={{ color: '#1f4e79' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <Statistic
                  title="Service Level"
                  value={kpiData?.service_performance?.service_level || 0}
                  formatter={(value) => formatPercentage(Number(value))}
                  prefix={<CheckCircleOutlined style={{ color: '#2e7d32' }} />}
                  valueStyle={{ color: '#2e7d32' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <Statistic
                  title="Demand Fulfillment"
                  value={kpiData?.service_performance?.demand_fulfillment_rate || 0}
                  formatter={(value) => formatPercentage(Number(value))}
                  prefix={<TruckOutlined style={{ color: '#2e7d32' }} />}
                  valueStyle={{ color: '#2e7d32' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <Statistic
                  title="Inventory Turns"
                  value={kpiData?.inventory_metrics?.inventory_turns || 0}
                  precision={1}
                  prefix={<BuildOutlined style={{ color: '#f57c00' }} />}
                  valueStyle={{ color: '#f57c00' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Charts Row */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} lg={12}>
              <Card title="Cost Breakdown" className="chart-container">
                <CostBreakdownChart data={kpiData?.cost_breakdown} />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Production Utilization" className="chart-container">
                <ProductionUtilizationChart data={kpiData?.production_utilization} />
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} lg={12}>
              <Card title="Service Performance" className="chart-container">
                <ServiceMetricsChart data={kpiData?.service_performance} />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Transport Utilization" className="chart-container">
                <TransportUtilizationTable data={kpiData?.transport_utilization} />
              </Card>
            </Col>
          </Row>

          {/* Status Indicators */}
          <Row gutter={[16, 16]}>
            <Col xs={24}>
              <Card>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Title level={4}>System Status</Title>
                  <Row gutter={[16, 16]}>
                    <Col xs={24} sm={8}>
                      <Space>
                        <CheckCircleOutlined style={{ color: '#2e7d32', fontSize: '1.2rem' }} />
                        <div>
                          <Text strong>Data Validation</Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: '0.9rem' }}>
                            All validation stages passed
                          </Text>
                        </div>
                      </Space>
                    </Col>
                    <Col xs={24} sm={8}>
                      <Space>
                        <CheckCircleOutlined style={{ color: '#2e7d32', fontSize: '1.2rem' }} />
                        <div>
                          <Text strong>Optimization Engine</Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: '0.9rem' }}>
                            Ready for execution
                          </Text>
                        </div>
                      </Space>
                    </Col>
                    <Col xs={24} sm={8}>
                      <Space>
                        {kpiData?.service_performance?.stockout_triggered ? (
                          <WarningOutlined style={{ color: '#f57c00', fontSize: '1.2rem' }} />
                        ) : (
                          <CheckCircleOutlined style={{ color: '#2e7d32', fontSize: '1.2rem' }} />
                        )}
                        <div>
                          <Text strong>Service Level</Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: '0.9rem' }}>
                            {kpiData?.service_performance?.stockout_triggered 
                              ? 'Stockout detected' 
                              : 'All demand satisfied'
                            }
                          </Text>
                        </div>
                      </Space>
                    </Col>
                  </Row>
                </Space>
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
};

export default Dashboard;