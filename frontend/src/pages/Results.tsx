import React, { useState } from 'react';
import { Card, Select, Typography, Space, Row, Col, Table, Tag, Button } from 'antd';
import { useQuery } from 'react-query';
import { DownloadOutlined, EyeOutlined } from '@ant-design/icons';
import { fetchOptimizationRuns, fetchOptimizationResults } from '../services/api';
import CostBreakdownChart from '../components/Charts/CostBreakdownChart';

const { Title, Text } = Typography;
const { Option } = Select;

const Results = () => {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  const { data: runs, isLoading: runsLoading } = useQuery(
    'optimization-runs-results',
    fetchOptimizationRuns
  );

  const { data: results, isLoading: resultsLoading } = useQuery(
    ['optimization-results', selectedRunId],
    () => fetchOptimizationResults(selectedRunId!),
    {
      enabled: !!selectedRunId,
    }
  );

  const completedRuns = runs?.filter(run => run.status === 'completed') || [];

  const formatCurrency = (value: number) => {
    if (value >= 10000000) {
      return `₹${(value / 10000000).toFixed(2)} Cr`;
    } else if (value >= 100000) {
      return `₹${(value / 100000).toFixed(2)} L`;
    } else if (value >= 1000) {
      return `₹${(value / 1000).toFixed(2)} K`;
    }
    return `₹${value.toFixed(2)}`;
  };

  const productionColumns = [
    {
      title: 'Plant',
      dataIndex: 'plant_id',
      key: 'plant_id',
    },
    {
      title: 'Period',
      dataIndex: 'period',
      key: 'period',
    },
    {
      title: 'Production (tonnes)',
      dataIndex: 'production_tonnes',
      key: 'production_tonnes',
      align: 'right' as const,
      render: (value: number) => value.toLocaleString(),
    },
  ];

  const shipmentColumns = [
    {
      title: 'Origin',
      dataIndex: 'origin_plant_id',
      key: 'origin_plant_id',
    },
    {
      title: 'Destination',
      dataIndex: 'destination_node_id',
      key: 'destination_node_id',
    },
    {
      title: 'Mode',
      dataIndex: 'transport_mode',
      key: 'transport_mode',
      render: (mode: string) => (
        <Tag color={mode === 'road' ? 'blue' : mode === 'rail' ? 'green' : 'orange'}>
          {mode.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Period',
      dataIndex: 'period',
      key: 'period',
    },
    {
      title: 'Shipment (tonnes)',
      dataIndex: 'shipment_tonnes',
      key: 'shipment_tonnes',
      align: 'right' as const,
      render: (value: number) => value.toLocaleString(),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Space direction="vertical" size="small">
          <Title level={2} style={{ margin: 0, color: '#1f4e79' }}>
            Optimization Results
          </Title>
          <Text type="secondary">
            Detailed analysis of optimization results with cost breakdown and solution plans
          </Text>
        </Space>
        
        <div style={{ marginTop: 16 }}>
          <Space>
            <Text strong>Select Run:</Text>
            <Select
              value={selectedRunId}
              onChange={setSelectedRunId}
              style={{ width: 300 }}
              loading={runsLoading}
              placeholder="Select an optimization run"
            >
              {completedRuns.map(run => (
                <Option key={run.run_id} value={run.run_id}>
                  <div>
                    <Text strong>{run.scenario_name}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '0.8rem' }}>
                      {new Date(run.start_time).toLocaleString()} - 
                      {formatCurrency(run.objective_value || 0)}
                    </Text>
                  </div>
                </Option>
              ))}
            </Select>
          </Space>
        </div>
      </div>

      {!selectedRunId ? (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            <EyeOutlined style={{ fontSize: '3rem', marginBottom: '16px' }} />
            <div>
              <Text>Select an optimization run to view detailed results</Text>
            </div>
          </div>
        </Card>
      ) : resultsLoading ? (
        <Card loading />
      ) : results ? (
        <>
          {/* Summary Cards */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <div className="metric-value">
                  {formatCurrency(results.objective_value)}
                </div>
                <div className="metric-label">Total Cost</div>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <div className="metric-value">
                  {results.solve_time.toFixed(1)}s
                </div>
                <div className="metric-label">Solve Time</div>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <div className="metric-value">
                  {(results.service_metrics.demand_fulfillment_rate * 100).toFixed(1)}%
                </div>
                <div className="metric-label">Demand Fulfillment</div>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="metric-card">
                <div className="metric-value">
                  {results.solver_status}
                </div>
                <div className="metric-label">Solver Status</div>
              </Card>
            </Col>
          </Row>

          {/* Cost Breakdown */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} lg={12}>
              <Card title="Cost Breakdown">
                <CostBreakdownChart data={results.cost_breakdown} />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Cost Details">
                <Space direction="vertical" style={{ width: '100%' }}>
                  {Object.entries(results.cost_breakdown).map(([key, value]) => (
                    <div key={key} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      padding: '8px 0',
                      borderBottom: '1px solid #f0f0f0'
                    }}>
                      <Text>{key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</Text>
                      <Text strong>{formatCurrency(value)}</Text>
                    </div>
                  ))}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    padding: '12px 0',
                    borderTop: '2px solid #1f4e79',
                    marginTop: '8px'
                  }}>
                    <Text strong style={{ color: '#1f4e79' }}>Total Cost</Text>
                    <Text strong style={{ color: '#1f4e79', fontSize: '1.1rem' }}>
                      {formatCurrency(results.objective_value)}
                    </Text>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>

          {/* Solution Tables */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} lg={12}>
              <Card 
                title="Production Plan" 
                extra={
                  <Button icon={<DownloadOutlined />} size="small">
                    Export
                  </Button>
                }
              >
                <Table
                  dataSource={results.production_plan}
                  columns={productionColumns}
                  pagination={{ pageSize: 10 }}
                  size="small"
                  rowKey={(record) => `${record.plant_id}-${record.period}`}
                />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card 
                title="Shipment Plan"
                extra={
                  <Button icon={<DownloadOutlined />} size="small">
                    Export
                  </Button>
                }
              >
                <Table
                  dataSource={results.shipment_plan}
                  columns={shipmentColumns}
                  pagination={{ pageSize: 10 }}
                  size="small"
                  rowKey={(record) => `${record.origin_plant_id}-${record.destination_node_id}-${record.period}-${record.transport_mode}`}
                />
              </Card>
            </Col>
          </Row>

          {/* Performance Metrics */}
          <Card title="Performance Metrics">
            <Row gutter={[16, 16]}>
              <Col xs={24} md={8}>
                <div style={{ textAlign: 'center', padding: '16px' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#2e7d32' }}>
                    {(results.utilization_metrics.production_utilization * 100).toFixed(1)}%
                  </div>
                  <Text type="secondary">Production Utilization</Text>
                </div>
              </Col>
              <Col xs={24} md={8}>
                <div style={{ textAlign: 'center', padding: '16px' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1f4e79' }}>
                    {(results.utilization_metrics.transport_utilization * 100).toFixed(1)}%
                  </div>
                  <Text type="secondary">Transport Utilization</Text>
                </div>
              </Col>
              <Col xs={24} md={8}>
                <div style={{ textAlign: 'center', padding: '16px' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f57c00' }}>
                    {results.utilization_metrics.inventory_turns.toFixed(1)}
                  </div>
                  <Text type="secondary">Inventory Turns</Text>
                </div>
              </Col>
            </Row>
          </Card>
        </>
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            <Text>No results found for the selected run</Text>
          </div>
        </Card>
      )}
    </div>
  );
};

export default Results;