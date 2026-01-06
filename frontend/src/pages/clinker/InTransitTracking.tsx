import React, { useState } from 'react';
import { 
  Card, 
  Table, 
  Row, 
  Col, 
  Typography, 
  Tag, 
  Progress,
  Space,
  Timeline,
  Alert,
  Button
} from 'antd';
import { 
  EnvironmentOutlined, 
  TruckOutlined, 
  WarningOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  PhoneOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;

interface Shipment {
  id: string;
  vehicleNumber: string;
  driverName: string;
  driverPhone: string;
  route: string;
  currentLocation: string;
  status: 'En Route' | 'Delayed' | 'Delivered' | 'At Destination';
  progress: number;
  estimatedArrival: string;
  actualDistance: number;
  totalDistance: number;
  delayMinutes?: number;
  lastUpdate: string;
}

const InTransitTracking = () => {
  const [shipments] = useState<Shipment[]>([
    {
      id: 'SH-001',
      vehicleNumber: 'CG-01-AB-1234',
      driverName: 'Rajesh Kumar',
      driverPhone: '+91-9876543210',
      route: 'ACC Jamul Plant → Ambuja Dadri Terminal',
      currentLocation: 'Vadodara, Gujarat',
      status: 'En Route',
      progress: 65,
      estimatedArrival: '2025-01-10 14:00',
      actualDistance: 780,
      totalDistance: 1200,
      lastUpdate: '2025-01-08 16:30'
    },
    {
      id: 'SH-002',
      vehicleNumber: 'RAKE-5678',
      driverName: 'Suresh Reddy',
      driverPhone: '+91-9876543211',
      route: 'Ambuja Ambujanagar Plant → Penna Krishnapatnam Terminal',
      currentLocation: 'Visakhapatnam, AP',
      status: 'Delayed',
      progress: 45,
      estimatedArrival: '2025-01-11 18:00',
      actualDistance: 720,
      totalDistance: 1600,
      delayMinutes: 180,
      lastUpdate: '2025-01-08 15:45'
    },
    {
      id: 'SH-003',
      vehicleNumber: 'TS-09-CD-5678',
      driverName: 'Amit Singh',
      driverPhone: '+91-9876543212',
      route: 'Orient Devapur Plant → ACC Sindri Terminal',
      currentLocation: 'Sindri Terminal',
      status: 'At Destination',
      progress: 100,
      estimatedArrival: '2025-01-08 12:00',
      actualDistance: 150,
      totalDistance: 150,
      lastUpdate: '2025-01-08 11:45'
    },
    {
      id: 'SH-004',
      vehicleNumber: 'RAKE-9012',
      driverName: 'Venkat Rao',
      driverPhone: '+91-9876543213',
      route: 'Penna Tandur Plant → Ambuja Sankrail Terminal',
      currentLocation: 'Bhubaneswar, Odisha',
      status: 'En Route',
      progress: 55,
      estimatedArrival: '2025-01-15 10:00',
      actualDistance: 880,
      totalDistance: 1600,
      lastUpdate: '2025-01-08 17:15'
    },
    {
      id: 'SH-005',
      vehicleNumber: 'VESSEL-001',
      driverName: 'Captain Sharma',
      driverPhone: '+91-9876543214',
      route: 'Sanghi Sanghipuram Plant → ACC Vizag Terminal',
      currentLocation: 'Kandla Port',
      status: 'En Route',
      progress: 25,
      estimatedArrival: '2025-01-19 08:00',
      actualDistance: 400,
      totalDistance: 1600,
      lastUpdate: '2025-01-08 18:00'
    },
    {
      id: 'SH-006',
      vehicleNumber: 'KA-03-EF-9012',
      driverName: 'Ravi Kumar',
      driverPhone: '+91-9876543215',
      route: 'ACC Wadi Plant → Ambuja Tuticorin Terminal',
      currentLocation: 'Bangalore, Karnataka',
      status: 'Delayed',
      progress: 30,
      estimatedArrival: '2025-01-16 14:00',
      actualDistance: 180,
      totalDistance: 600,
      delayMinutes: 120,
      lastUpdate: '2025-01-08 16:45'
    }
  ]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'En Route': return 'blue';
      case 'Delayed': return 'red';
      case 'At Destination': return 'orange';
      case 'Delivered': return 'green';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'En Route': return <TruckOutlined />;
      case 'Delayed': return <WarningOutlined />;
      case 'At Destination': return <EnvironmentOutlined />;
      case 'Delivered': return <CheckCircleOutlined />;
      default: return null;
    }
  };

  const columns = [
    {
      title: 'Shipment ID',
      dataIndex: 'id',
      key: 'id',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'Vehicle & Driver',
      key: 'vehicle',
      render: (record: Shipment) => (
        <Space direction="vertical" size="small">
          <Text strong>{record.vehicleNumber}</Text>
          <Text style={{ fontSize: '12px' }}>{record.driverName}</Text>
          <Text style={{ fontSize: '11px', color: '#666' }}>
            <PhoneOutlined /> {record.driverPhone}
          </Text>
        </Space>
      )
    },
    {
      title: 'Route',
      dataIndex: 'route',
      key: 'route',
      render: (text: string) => <Text>{text}</Text>
    },
    {
      title: 'Current Location',
      dataIndex: 'currentLocation',
      key: 'currentLocation',
      render: (text: string, record: Shipment) => (
        <Space direction="vertical" size="small">
          <Text strong>{text}</Text>
          <Text style={{ fontSize: '11px', color: '#666' }}>
            Updated: {record.lastUpdate}
          </Text>
        </Space>
      )
    },
    {
      title: 'Progress',
      key: 'progress',
      render: (record: Shipment) => (
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Progress 
            percent={record.progress} 
            size="small"
            status={record.status === 'Delayed' ? 'exception' : 'active'}
          />
          <Text style={{ fontSize: '11px' }}>
            {record.actualDistance} / {record.totalDistance} km
          </Text>
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: Shipment) => (
        <Space direction="vertical" size="small">
          <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
            {status}
          </Tag>
          {record.delayMinutes && (
            <Text style={{ fontSize: '11px', color: '#f5222d' }}>
              Delayed by {record.delayMinutes} min
            </Text>
          )}
        </Space>
      )
    },
    {
      title: 'ETA',
      dataIndex: 'estimatedArrival',
      key: 'estimatedArrival',
      render: (text: string) => (
        <Text style={{ fontSize: '12px' }}>{text}</Text>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: Shipment) => (
        <Space direction="vertical" size="small">
          <Button size="small" icon={<PhoneOutlined />}>
            Call Driver
          </Button>
          <Button size="small" icon={<EnvironmentOutlined />}>
            Track Live
          </Button>
        </Space>
      )
    }
  ];

  const enRouteCount = shipments.filter(s => s.status === 'En Route').length;
  const delayedCount = shipments.filter(s => s.status === 'Delayed').length;
  const atDestinationCount = shipments.filter(s => s.status === 'At Destination').length;
  const deliveredCount = shipments.filter(s => s.status === 'Delivered').length;

  return (
    <div>
      <Title level={2} style={{ color: '#1f4e79', marginBottom: 24 }}>
        <EnvironmentOutlined /> In-Transit Tracking
      </Title>

      {/* Alerts */}
      {delayedCount > 0 && (
        <Alert
          message="Delayed Shipments Alert"
          description={`${delayedCount} shipment(s) are experiencing delays. Monitor closely and take corrective action.`}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#1890ff', margin: 0 }}>
                {enRouteCount}
              </Title>
              <Text type="secondary">En Route</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#f5222d', margin: 0 }}>
                {delayedCount}
              </Title>
              <Text type="secondary">Delayed</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#faad14', margin: 0 }}>
                {atDestinationCount}
              </Title>
              <Text type="secondary">At Destination</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#52c41a', margin: 0 }}>
                {deliveredCount}
              </Title>
              <Text type="secondary">Delivered</Text>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* Shipments Table */}
        <Col xs={24} lg={16}>
          <Card title="Active Shipments">
            <Table
              dataSource={shipments}
              columns={columns}
              rowKey="id"
              pagination={false}
              size="small"
              scroll={{ x: 1200, y: 400 }}
              rowClassName={(record) => {
                if (record.status === 'Delayed') return 'delayed-row';
                return '';
              }}
            />
          </Card>
        </Col>

        {/* Live Updates */}
        <Col xs={24} lg={8}>
          <Card title="Live Updates">
            <Timeline
              items={[
                {
                  color: 'blue',
                  children: (
                    <div>
                      <Text strong>16:30 - Location Update</Text>
                      <br />
                      <Text type="secondary">CG-01-AB-1234 at Vadodara</Text>
                      <br />
                      <Text style={{ fontSize: '11px', color: '#52c41a' }}>On Schedule</Text>
                    </div>
                  ),
                },
                {
                  color: 'red',
                  children: (
                    <div>
                      <Text strong>15:45 - Delay Alert</Text>
                      <br />
                      <Text type="secondary">RAKE-5678 delayed by 3 hours</Text>
                      <br />
                      <Text style={{ fontSize: '11px', color: '#f5222d' }}>Traffic congestion</Text>
                    </div>
                  ),
                },
                {
                  color: 'green',
                  children: (
                    <div>
                      <Text strong>11:45 - Arrived</Text>
                      <br />
                      <Text type="secondary">TS-09-CD-5678 at Sindri Terminal</Text>
                      <br />
                      <Text style={{ fontSize: '11px', color: '#52c41a' }}>15 min early</Text>
                    </div>
                  ),
                },
              ]}
            />
          </Card>

          {/* Route Performance */}
          <Card title="Route Performance" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>ACC Jamul → Ambuja Dadri</Text>
                <Progress percent={85} size="small" status="active" />
                <Text style={{ fontSize: '11px' }}>Avg Transit: 2.1 days</Text>
              </div>
              <div>
                <Text strong>Ambuja Ambujanagar → Penna Krishnapatnam</Text>
                <Progress percent={60} size="small" status="exception" />
                <Text style={{ fontSize: '11px' }}>Avg Transit: 4.2 days</Text>
              </div>
              <div>
                <Text strong>Orient Devapur → ACC Sindri</Text>
                <Progress percent={95} size="small" status="success" />
                <Text style={{ fontSize: '11px' }}>Avg Transit: 0.8 days</Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      <style jsx>{`
        .delayed-row {
          background-color: #fff2f0 !important;
        }
      `}</style>
    </div>
  );
};

export default InTransitTracking;