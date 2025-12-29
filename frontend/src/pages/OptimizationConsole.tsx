import React, { useState } from 'react';
import { 
  Card, 
  Button, 
  Select, 
  InputNumber, 
  Form, 
  Alert, 
  Progress, 
  Typography, 
  Space, 
  Row, 
  Col,
  Divider,
  Tag
} from 'antd';
import { useQuery, useMutation } from 'react-query';
import { 
  PlayCircleOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { 
  fetchDataHealth, 
  fetchScenarios, 
  runOptimization, 
  fetchOptimizationStatus,
  fetchOptimizationRuns
} from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

const OptimizationConsole = () => {
  const [form] = Form.useForm();
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [optimizationStatus, setOptimizationStatus] = useState<any>(null);

  // Fetch data health to check if optimization can run
  const { data: dataHealth, refetch: refetchHealth } = useQuery(
    'data-health-console',
    fetchDataHealth,
    {
      refetchInterval: 10000, // Check every 10 seconds
    }
  );

  // Fetch available scenarios
  const { data: scenarios, isLoading: scenariosLoading } = useQuery(
    'scenarios-console',
    fetchScenarios
  );

  // Fetch recent optimization runs
  const { data: recentRuns, refetch: refetchRuns } = useQuery(
    'optimization-runs',
    fetchOptimizationRuns
  );

  // Poll optimization status if there's a current run
  const { data: statusData } = useQuery(
    ['optimization-status', currentRunId],
    () => fetchOptimizationStatus(currentRunId!),
    {
      enabled: !!currentRunId,
      refetchInterval: 2000, // Poll every 2 seconds
      onSuccess: (data) => {
        setOptimizationStatus(data);
        if (data.status === 'completed' || data.status === 'failed') {
          setCurrentRunId(null);
          refetchRuns();
        }
      }
    }
  );

  // Run optimization mutation
  const runOptimizationMutation = useMutation(runOptimization, {
    onSuccess: (data) => {
      setCurrentRunId(data.run_id);
      setOptimizationStatus({
        run_id: data.run_id,
        status: 'queued',
        progress: 0,
        start_time: new Date().toISOString()
      });
    },
    onError: (error: any) => {
      console.error('Optimization failed:', error);
    }
  });

  const handleRunOptimization = async (values: any) => {
    try {
      await runOptimizationMutation.mutateAsync({
        scenario_name: values.scenario,
        solver: values.solver,
        time_limit: values.timeLimit,
        mip_gap: values.mipGap / 100, // Convert percentage to decimal
      });
    } catch (error) {
      console.error('Failed to start optimization:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#2e7d32' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#d32f2f' }} />;
      case 'running':
      case 'solving':
      case 'building_model':
      case 'processing_results':
        return <LoadingOutlined style={{ color: '#1f4e79' }} />;
      case 'queued':
        return <LoadingOutlined style={{ color: '#f57c00' }} />;
      default:
        return null;
    }
  };

  const getProgressColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return '#2e7d32';
      case 'failed':
        return '#d32f2f';
      case 'running':
      case 'solving':
        return '#1f4e79';
      default:
        return '#f57c00';
    }
  };

  const isOptimizationReady = dataHealth?.optimization_ready;
  const isRunning = !!currentRunId;

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Space direction="vertical" size="small">
          <Title level={2} style={{ margin: 0, color: '#1f4e79' }}>
            Optimization Console
          </Title>
          <Text type="secondary">
            Central control panel for running supply chain optimization
          </Text>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        {/* Optimization Control Panel */}
        <Col xs={24} lg={12}>
          <Card title="Run Optimization" style={{ height: '100%' }}>
            {/* Data Readiness Check */}
            <Alert
              message={
                isOptimizationReady ? 
                "System Ready" : 
                "Optimization Blocked"
              }
              description={
                isOptimizationReady ? 
                "All data validation checks passed. Ready to run optimization." :
                `${dataHealth?.validation_summary?.blocking_errors || 0} critical errors must be resolved before optimization can run.`
              }
              type={isOptimizationReady ? "success" : "error"}
              showIcon
              style={{ marginBottom: 16 }}
              action={
                !isOptimizationReady && (
                  <Button size="small" onClick={() => refetchHealth()}>
                    Recheck
                  </Button>
                )
              }
            />

            <Form
              form={form}
              layout="vertical"
              onFinish={handleRunOptimization}
              initialValues={{
                scenario: 'base',
                solver: 'PULP_CBC_CMD',
                timeLimit: 600,
                mipGap: 1.0
              }}
            >
              <Form.Item
                label="Scenario"
                name="scenario"
                rules={[{ required: true, message: 'Please select a scenario' }]}
              >
                <Select loading={scenariosLoading} placeholder="Select scenario">
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
              </Form.Item>

              <Form.Item
                label="Solver"
                name="solver"
                rules={[{ required: true, message: 'Please select a solver' }]}
              >
                <Select>
                  <Option value="PULP_CBC_CMD">
                    <div>
                      <Text strong>CBC (Default)</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '0.8rem' }}>
                        Open source, reliable
                      </Text>
                    </div>
                  </Option>
                  <Option value="HIGHS">
                    <div>
                      <Text strong>HiGHS</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '0.8rem' }}>
                        High performance, faster
                      </Text>
                    </div>
                  </Option>
                  <Option value="GUROBI">
                    <div>
                      <Text strong>Gurobi</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '0.8rem' }}>
                        Commercial, premium
                      </Text>
                    </div>
                  </Option>
                </Select>
              </Form.Item>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="Time Limit (seconds)"
                    name="timeLimit"
                    rules={[{ required: true, message: 'Please set time limit' }]}
                  >
                    <InputNumber
                      min={60}
                      max={3600}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="MIP Gap (%)"
                    name="mipGap"
                    rules={[{ required: true, message: 'Please set MIP gap' }]}
                  >
                    <InputNumber
                      min={0.1}
                      max={10}
                      step={0.1}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  size="large"
                  icon={<PlayCircleOutlined />}
                  loading={runOptimizationMutation.isLoading}
                  disabled={!isOptimizationReady || isRunning}
                  block
                  className="btn-primary"
                >
                  {isRunning ? 'Optimization Running...' : 'Run Optimization'}
                </Button>
              </Form.Item>
            </Form>

            {runOptimizationMutation.error && (
              <Alert
                message="Optimization Failed"
                description={(runOptimizationMutation.error as any)?.response?.data?.detail || 'Unknown error occurred'}
                type="error"
                showIcon
                style={{ marginTop: 16 }}
              />
            )}
          </Card>
        </Col>

        {/* Current Run Status */}
        <Col xs={24} lg={12}>
          <Card title="Current Run Status" style={{ height: '100%' }}>
            {optimizationStatus ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text strong>Run ID:</Text>
                  <Text code>{optimizationStatus.run_id}</Text>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text strong>Status:</Text>
                  <Tag color={optimizationStatus.status === 'completed' ? 'green' : 
                              optimizationStatus.status === 'failed' ? 'red' : 'blue'}>
                    {getStatusIcon(optimizationStatus.status)}
                    {optimizationStatus.status.toUpperCase()}
                  </Tag>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text strong>Scenario:</Text>
                  <Text>{optimizationStatus.scenario_name}</Text>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text strong>Started:</Text>
                  <Text>{new Date(optimizationStatus.start_time).toLocaleTimeString()}</Text>
                </div>

                <Divider />

                <div>
                  <Text strong>Progress:</Text>
                  <Progress
                    percent={optimizationStatus.progress || 0}
                    strokeColor={getProgressColor(optimizationStatus.status)}
                    status={optimizationStatus.status === 'failed' ? 'exception' : 
                           optimizationStatus.status === 'completed' ? 'success' : 'active'}
                  />
                </div>

                {optimizationStatus.error_message && (
                  <Alert
                    message="Error"
                    description={optimizationStatus.error_message}
                    type="error"
                    showIcon
                  />
                )}

                {optimizationStatus.status === 'completed' && optimizationStatus.objective_value && (
                  <div style={{ 
                    background: '#f6ffed', 
                    border: '1px solid #b7eb8f',
                    borderRadius: '6px',
                    padding: '12px'
                  }}>
                    <Text strong style={{ color: '#2e7d32' }}>
                      Optimization Completed Successfully!
                    </Text>
                    <br />
                    <Text>
                      Total Cost: ₹{optimizationStatus.objective_value?.toLocaleString()}
                    </Text>
                    <br />
                    <Text type="secondary">
                      Solve Time: {optimizationStatus.solve_time?.toFixed(2)}s
                    </Text>
                  </div>
                )}
              </Space>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
                <Text>No optimization currently running</Text>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* Recent Runs */}
      <Card title="Recent Optimization Runs" style={{ marginTop: 16 }}>
        {recentRuns && recentRuns.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #f0f0f0' }}>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Run ID</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Scenario</th>
                  <th style={{ padding: '12px', textAlign: 'center' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Total Cost</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Solve Time</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Started</th>
                </tr>
              </thead>
              <tbody>
                {recentRuns.slice(0, 10).map((run, index) => (
                  <tr key={run.run_id} style={{ 
                    borderBottom: '1px solid #f0f0f0',
                    backgroundColor: index % 2 === 0 ? '#fafafa' : 'white'
                  }}>
                    <td style={{ padding: '12px' }}>
                      <Text code style={{ fontSize: '0.8rem' }}>
                        {run.run_id.slice(-8)}
                      </Text>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <Text>{run.scenario_name}</Text>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <Tag color={run.status === 'completed' ? 'green' : 
                                 run.status === 'failed' ? 'red' : 'blue'}>
                        {run.status.toUpperCase()}
                      </Tag>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>
                      <Text>
                        {run.objective_value ? 
                          `₹${run.objective_value.toLocaleString()}` : 
                          '-'
                        }
                      </Text>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>
                      <Text>
                        {run.solve_time ? 
                          `${run.solve_time.toFixed(1)}s` : 
                          '-'
                        }
                      </Text>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <Text type="secondary" style={{ fontSize: '0.9rem' }}>
                        {new Date(run.start_time).toLocaleString()}
                      </Text>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            <Text>No optimization runs found</Text>
          </div>
        )}
      </Card>
    </div>
  );
};

export default OptimizationConsole;