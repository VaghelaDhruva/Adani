import React, { useState } from 'react';
import { 
  Card, 
  Table, 
  Row, 
  Col, 
  Typography, 
  Tag, 
  Button,
  Progress,
  Space,
  Timeline,
  Statistic
} from 'antd';
import { 
  LoadingOutlined, 
  PlayCircleOutlined, 
  CheckCircleOutlined,
  ClockCircleOutlined,
  TruckOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;

interface LoadingActivity {
  id: string;
  dispatchId: string;
  vehicleNumber: string;
  quantity: number;
  loadingStart: string;
  loadingEnd?: string;
  actualWeight: number;
  status: 'Scheduled' | 'Loading' | 'Completed';
  progress: number;
  lrNumber?: string;
  driverName: string;
}

const LoadingExecution = () => {
  const [loadingActivities] = useState<LoadingActivity[]>([
    {
      id: 'LD-001',
      dispatchId: 'DP-001',
      vehicleNumber: 'CG-01-AB-1234',
      quantity: 2500,
      loadingStart: '2025-01-08 08:00',
      loadingEnd: '2025-01-08 10:30',
      actualWeight: 2485,
      status: 'Completed',
      progress: 100,
      lrNumber: 'LR-2025-001',
      driverName: 'Rajesh Kumar'
    },
    {
      id: 'LD-002',
      dispatchId: 'DP-002',
      vehicleNumber: 'RAKE-5678',
      quantity: 1800,
      loadingStart: '2025-01-07 14:00',
      actualWeight: 1350,
      status: 'Loading',
      progress: 75,
      driverName: 'Suresh Reddy'
    },
    {
      id: 'LD-003',
      dispatchId: 'DP-003',
      vehicleNumber: 'TS-09-CD-5678',
      quantity: 3200,
      loadingStart: '2025-01-08 15:00',
      actualWeight: 0,
      status: 'Scheduled',
      progress: 0,
      driverName: 'Amit Singh'
    },
    {
      id: 'LD-004',
      dispatchId: 'DP-004',
      vehicleNumber: 'RAKE-9012',
      quantity: 2800,
      loadingStart: '2025-01-10 09:00',
      actualWeight: 2100,
      status: 'Loading',
      progress: 75,
      driverName: 'Venkat Rao'
    },
    {
      id: 'LD-005',
      dispatchId: 'DP-005',
      vehicleNumber: 'VESSEL-001',
      quantity: 4500,
      loadingStart: '2025-01-12 06:00',
      loadingEnd: '2025-01-12 18:00',
      actualWeight: 4485,
      status: 'Completed',
      progress: 100,
      lrNumber: 'LR-2025-005',
      driverName: 'Captain Sharma'
    },
    {
      id: 'LD-006',
      dispatchId: 'DP-006',
      vehicleNumber: 'KA-03-EF-9012',
      quantity: 3600,
      loadingStart: '2025-01-11 10:00',
      actualWeight: 2700,
      status: 'Loading',
      progress: 75,
      driverName: 'Ravi Kumar'
    }
  ]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Scheduled': return 'blue';
      case 'Loading': return 'orange';
      case 'Completed': return 'green';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Scheduled': return <ClockCircleOutlined />;
      case 'Loading': return <LoadingOutlined />;
      case 'Completed': return <CheckCircleOutlined />;
      default: return null;
    }
  };

  const columns = [
    {
      title: 'Loading ID',
      dataIndex: 'id',
      key: 'id',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'Vehicle Details',
      key: 'vehicle',
      render: (record: LoadingActivity) => (
        <Space direction="vertical" size="small">
          <Text strong>{record.vehicleNumber}</Text>
          <Text style={{ fontSize: '12px' }}>{record.driverName}</Text>
        </Space>
      )
    },
    {
      title: 'Planned Qty',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (value: number) => `${value.toLocaleString()} MT`
    },
    {
      title: 'Actual Weight',
      dataIndex: 'actualWeight',
      key: 'actualWeight',
      render: (value: number, record: LoadingActivity) => (
        <Space direction="vertical" size="small">
          <Text strong>{value > 0 ? `${value.toLocaleString()} MT` : 'Pending'}</Text>
          {value > 0 && (
            <Text style={{ fontSize: '11px', color: record.actualWeight < record.quantity ? '#faad14' : '#52c41a' }}>
              Variance: {((record.actualWeight - record.quantity) / record.quantity * 100).toFixed(1)}%
            </Text>
          )}
        </Space>
      )
    },
    {
      title: 'Loading Progress',
      key: 'progress',
      render: (record: LoadingActivity) => (
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Progress 
            percent={record.progress} 
            size="small"
            status={record.status === 'Completed' ? 'success' : 'active'}
          />
          <Text style={{ fontSize: '11px' }}>
            {record.status === 'Loading' ? 'In Progress' : 
             record.status === 'Completed' ? 'Completed' : 'Scheduled'}
          </Text>
        </Space>
      )
    },
    {
      title: 'Timeline',
      key: 'timeline',
      render: (record: LoadingActivity) => (
        <Space direction="vertical" size="small">
          <Text style={{ fontSize: '12px' }}>Start: {record.loadingStart}</Text>
          {record.loadingEnd && (
            <Text style={{ fontSize: '12px' }}>End: {record.loadingEnd}</Text>
          )}
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {status}
        </Tag>
      )
    },
    {
      title: 'LR Number',
      dataIndex: 'lrNumber',
      key: 'lrNumber',
      render: (text: string) => text || <Text type="secondary">Pending</Text>
    }
  ];

  const totalScheduled = loadingActivities.filter(a => a.status === 'Scheduled').length;
  const totalLoading = loadingActivities.filter(a => a.status === 'Loading').length;
  const totalCompleted = loadingActivities.filter(a => a.status === 'Completed').length;
  const totalWeight = loadingActivities.reduce((sum, a) => sum + a.actualWeight, 0);

  return (
    <div>
      <Title level={2} style={{ color: '#1f4e79', marginBottom: 24 }}>
        <LoadingOutlined /> Loading & Dispatch Execution
      </Title>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Scheduled"
              value={totalScheduled}
              prefix={<ClockCircleOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Loading"
              value={totalLoading}
              prefix={<LoadingOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Completed"
              value={totalCompleted}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Loaded"
              value={totalWeight}
              suffix="MT"
              prefix={<TruckOutlined style={{ color: '#1f4e79' }} />}
              valueStyle={{ color: '#1f4e79' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* Loading Activities Table */}
        <Col xs={24} lg={16}>
          <Card title="Loading Activities">
            <Table
              dataSource={loadingActivities}
              columns={columns}
              rowKey="id"
              pagination={false}
              size="small"
              scroll={{ x: 1000, y: 400 }}
            />
          </Card>
        </Col>

        {/* Real-time Timeline */}
        <Col xs={24} lg={8}>
          <Card title="Today's Loading Timeline">
            <Timeline
              items={[
                {
                  color: 'green',
                  children: (
                    <div>
                      <Text strong>08:00 - Loading Started</Text>
                      <br />
                      <Text type="secondary">MH-01-AB-1234 - 2500 MT</Text>
                    </div>
                  ),
                },
                {
                  color: 'green',
                  children: (
                    <div>
                      <Text strong>10:30 - Loading Completed</Text>
                      <br />
                      <Text type="secondary">Actual: 2485 MT, LR: LR-2025-001</Text>
                    </div>
                  ),
                },
                {
                  color: 'blue',
                  children: (
                    <div>
                      <Text strong>14:00 - Loading In Progress</Text>
                      <br />
                      <Text type="secondary">RAKE-5678 - 75% Complete</Text>
                    </div>
                  ),
                },
                {
                  color: 'gray',
                  children: (
                    <div>
                      <Text strong>15:00 - Scheduled</Text>
                      <br />
                      <Text type="secondary">TS-09-CD-5678 - 3200 MT</Text>
                    </div>
                  ),
                },
              ]}
            />
          </Card>

          {/* Quick Actions */}
          <Card title="Quick Actions" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button 
                type="primary" 
                icon={<PlayCircleOutlined />}
                block
              >
                Start Loading
              </Button>
              <Button 
                icon={<CheckCircleOutlined />}
                block
              >
                Complete Loading
              </Button>
              <Button 
                icon={<TruckOutlined />}
                block
              >
                Generate LR
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default LoadingExecution;