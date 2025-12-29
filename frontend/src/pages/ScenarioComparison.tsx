import React, { useState } from 'react';
import { Card, Select, Button, Typography, Space, Row, Col, Table, Alert } from 'antd';
import { useQuery, useMutation } from 'react-query';
import { SwapOutlined } from '@ant-design/icons';
import { fetchScenarios, compareScenarios } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

const ScenarioComparison = () => {
  const [selectedScenarios, setSelectedScenarios] = useState<string[]>([]);

  const { data: scenarios, isLoading: scenariosLoading } = useQuery(
    'scenarios-comparison',
    fetchScenarios
  );

  const compareMutation = useMutation(compareScenarios);

  const handleCompare = async () => {
    if (selectedScenarios.length >= 2) {
      await compareMutation.mutateAsync(selectedScenarios);
    }
  };

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

  const comparisonColumns = [
    {
      title: 'Metric',
      dataIndex: 'metric',
      key: 'metric',
      fixed: 'left' as const,
      width: 200,
    },
    ...selectedScenarios.map(scenario => ({
      title: scenario,
      dataIndex: scenario,
      key: scenario,
      align: 'center' as const,
    })),
  ];

  const getComparisonData = () => {
    if (!compareMutation.data) return [];

    const scenarios = compareMutation.data.scenarios;
    
    return [
      {
        key: 'total_cost',
        metric: 'Total Cost',
        ...scenarios.reduce((acc, scenario) => ({
          ...acc,
          [scenario.scenario_name]: formatCurrency(scenario.total_cost)
        }), {})
      },
      {
        key: 'production_cost',
        metric: 'Production Cost',
        ...scenarios.reduce((acc, scenario) => ({
          ...acc,
          [scenario.scenario_name]: formatCurrency(scenario.cost_breakdown.production_cost || 0)
        }), {})
      },
      {
        key: 'transport_cost',
        metric: 'Transport Cost',
        ...scenarios.reduce((acc, scenario) => ({
          ...acc,
          [scenario.scenario_name]: formatCurrency(scenario.cost_breakdown.transport_cost || 0)
        }), {})
      },
      {
        key: 'service_level',
        metric: 'Service Level',
        ...scenarios.reduce((acc, scenario) => ({
          ...acc,
          [scenario.scenario_name]: `${(scenario.service_level * 100).toFixed(1)}%`
        }), {})
      },
      {
        key: 'utilization',
        metric: 'Utilization',
        ...scenarios.reduce((acc, scenario) => ({
          ...acc,
          [scenario.scenario_name]: `${(scenario.utilization * 100).toFixed(1)}%`
        }), {})
      },
    ];
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Space direction="vertical" size="small">
          <Title level={2} style={{ margin: 0, color: '#1f4e79' }}>
            Scenario Comparison
          </Title>
          <Text type="secondary">
            Compare multiple optimization scenarios side-by-side to analyze trade-offs
          </Text>
        </Space>
      </div>

      {/* Scenario Selection */}
      <Card title="Select Scenarios to Compare" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>Choose 2-4 scenarios:</Text>
            <Select
              mode="multiple"
              value={selectedScenarios}
              onChange={setSelectedScenarios}
              style={{ width: '100%', marginTop: 8 }}
              loading={scenariosLoading}
              placeholder="Select scenarios to compare"
              maxTagCount={4}
            >
              {scenarios?.map(scenario => (
                <Option key={scenario.name} value={scenario.name}>
                  <div>
                    <Text strong>{scenario.name}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '0.8rem' }}>
                      {scenario.description}
                    </Text>
                  </div>
                </Option>
              ))}
            </Select>
          </div>
          
          <Button
            type="primary"
            icon={<SwapOutlined />}
            onClick={handleCompare}
            loading={compareMutation.isLoading}
            disabled={selectedScenarios.length < 2}
            className="btn-primary"
          >
            Compare Scenarios
          </Button>
        </Space>
      </Card>

      {/* Comparison Results */}
      {compareMutation.data && (
        <>
          {/* Recommendations */}
          {compareMutation.data.recommendations && compareMutation.data.recommendations.length > 0 && (
            <Alert
              message="Recommendations"
              description={
                <ul style={{ marginBottom: 0 }}>
                  {compareMutation.data.recommendations.map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              }
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />
          )}

          {/* Comparison Table */}
          <Card title="Scenario Comparison Results">
            <Table
              dataSource={getComparisonData()}
              columns={comparisonColumns}
              pagination={false}
              scroll={{ x: 800 }}
              size="middle"
              className="data-table"
            />
          </Card>

          {/* Cost Comparison Chart */}
          <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
            <Col xs={24} lg={12}>
              <Card title="Total Cost Comparison">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {compareMutation.data.scenarios.map((scenario, index) => (
                    <div key={scenario.scenario_name} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px',
                      background: index % 2 === 0 ? '#fafafa' : 'white',
                      borderRadius: '6px'
                    }}>
                      <div style={{ 
                        width: '12px', 
                        height: '12px', 
                        backgroundColor: ['#1f4e79', '#2e7d32', '#f57c00', '#9c27b0'][index % 4],
                        borderRadius: '2px'
                      }} />
                      <div style={{ flex: 1 }}>
                        <Text strong>{scenario.scenario_name}</Text>
                      </div>
                      <div>
                        <Text strong>{formatCurrency(scenario.total_cost)}</Text>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Service Level Comparison">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {compareMutation.data.scenarios.map((scenario, index) => (
                    <div key={scenario.scenario_name} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px',
                      background: index % 2 === 0 ? '#fafafa' : 'white',
                      borderRadius: '6px'
                    }}>
                      <div style={{ 
                        width: '12px', 
                        height: '12px', 
                        backgroundColor: ['#1f4e79', '#2e7d32', '#f57c00', '#9c27b0'][index % 4],
                        borderRadius: '2px'
                      }} />
                      <div style={{ flex: 1 }}>
                        <Text strong>{scenario.scenario_name}</Text>
                      </div>
                      <div>
                        <Text strong>{(scenario.service_level * 100).toFixed(1)}%</Text>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </Col>
          </Row>
        </>
      )}

      {compareMutation.error && (
        <Alert
          message="Comparison Failed"
          description={(compareMutation.error as any)?.response?.data?.detail || 'Failed to compare scenarios'}
          type="error"
          showIcon
          style={{ marginTop: 24 }}
        />
      )}

      {!compareMutation.data && !compareMutation.isLoading && selectedScenarios.length === 0 && (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            <SwapOutlined style={{ fontSize: '3rem', marginBottom: '16px' }} />
            <div>
              <Text>Select scenarios to compare their performance and costs</Text>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ScenarioComparison;