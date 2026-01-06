import React, { useState } from 'react';
import { 
  Card, 
  Table, 
  Row, 
  Col, 
  Typography, 
  Tag, 
  Button,
  Modal,
  Form,
  Select,
  DatePicker,
  Input,
  Space,
  message
} from 'antd';
import { 
  TruckOutlined, 
  PlusOutlined, 
  EditOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

interface DispatchPlan {
  id: string;
  orderId: string;
  sourcePlant: string;
  destinationPlant: string;
  quantity: number;
  transportMode: string;
  carrier: string;
  vehicleNumber: string;
  driverName: string;
  driverPhone: string;
  plannedLoadingDate: string;
  plannedDeliveryDate: string;
  status: 'Planned' | 'Assigned' | 'Loading' | 'Dispatched';
  estimatedCost: number;
}

const DispatchPlanning = () => {
  const [dispatchPlans, setDispatchPlans] = useState<DispatchPlan[]>([
    {
      id: 'DP-001',
      orderId: 'ORD-001',
      sourcePlant: 'ACC Jamul Plant',
      destinationPlant: 'Ambuja Dadri Terminal',
      quantity: 2500,
      transportMode: 'Road',
      carrier: 'Adani Logistics',
      vehicleNumber: 'CG-01-AB-1234',
      driverName: 'Rajesh Kumar',
      driverPhone: '+91-9876543210',
      plannedLoadingDate: '2025-01-08',
      plannedDeliveryDate: '2025-01-11',
      status: 'Assigned',
      estimatedCost: 3000000
    },
    {
      id: 'DP-002',
      orderId: 'ORD-002',
      sourcePlant: 'Ambuja Ambujanagar Plant',
      destinationPlant: 'Penna Krishnapatnam Terminal',
      quantity: 1800,
      transportMode: 'Rail',
      carrier: 'Indian Railways',
      vehicleNumber: 'RAKE-5678',
      driverName: 'Suresh Reddy',
      driverPhone: '+91-9876543211',
      plannedLoadingDate: '2025-01-07',
      plannedDeliveryDate: '2025-01-12',
      status: 'Loading',
      estimatedCost: 1170000
    },
    {
      id: 'DP-003',
      orderId: 'ORD-003',
      sourcePlant: 'Orient Devapur Plant',
      destinationPlant: 'ACC Sindri Terminal',
      quantity: 3200,
      transportMode: 'Road',
      carrier: 'Express Transporters',
      vehicleNumber: 'TS-09-CD-5678',
      driverName: 'Amit Singh',
      driverPhone: '+91-9876543212',
      plannedLoadingDate: '2025-01-09',
      plannedDeliveryDate: '2025-01-13',
      status: 'Planned',
      estimatedCost: 2720000
    },
    {
      id: 'DP-004',
      orderId: 'ORD-004',
      sourcePlant: 'Penna Tandur Plant',
      destinationPlant: 'Ambuja Sankrail Terminal',
      quantity: 2800,
      transportMode: 'Rail',
      carrier: 'Indian Railways',
      vehicleNumber: 'RAKE-9012',
      driverName: 'Venkat Rao',
      driverPhone: '+91-9876543213',
      plannedLoadingDate: '2025-01-10',
      plannedDeliveryDate: '2025-01-15',
      status: 'Assigned',
      estimatedCost: 1820000
    },
    {
      id: 'DP-005',
      orderId: 'ORD-005',
      sourcePlant: 'Sanghi Sanghipuram Plant',
      destinationPlant: 'ACC Vizag Terminal',
      quantity: 4500,
      transportMode: 'Sea',
      carrier: 'Coastal Shipping Corp',
      vehicleNumber: 'VESSEL-001',
      driverName: 'Captain Sharma',
      driverPhone: '+91-9876543214',
      plannedLoadingDate: '2025-01-12',
      plannedDeliveryDate: '2025-01-19',
      status: 'Dispatched',
      estimatedCost: 1800000
    },
    {
      id: 'DP-006',
      orderId: 'ORD-006',
      sourcePlant: 'ACC Wadi Plant',
      destinationPlant: 'Ambuja Tuticorin Terminal',
      quantity: 3600,
      transportMode: 'Road',
      carrier: 'Reliable Cargo',
      vehicleNumber: 'KA-03-EF-9012',
      driverName: 'Ravi Kumar',
      driverPhone: '+91-9876543215',
      plannedLoadingDate: '2025-01-11',
      plannedDeliveryDate: '2025-01-16',
      status: 'Loading',
      estimatedCost: 4320000
    }
  ]);

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingPlan, setEditingPlan] = useState<DispatchPlan | null>(null);
  const [form] = Form.useForm();

  const carriers = [
    'Adani Logistics',
    'Indian Railways',
    'Coastal Shipping Corp',
    'Express Transporters',
    'Reliable Cargo'
  ];

  const transportModes = ['Road', 'Rail', 'Sea'];

  const handleCreatePlan = () => {
    setEditingPlan(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEditPlan = (plan: DispatchPlan) => {
    setEditingPlan(plan);
    form.setFieldsValue({
      ...plan,
      plannedLoadingDate: plan.plannedLoadingDate,
      plannedDeliveryDate: plan.plannedDeliveryDate
    });
    setIsModalVisible(true);
  };

  const handleSubmit = (values: any) => {
    if (editingPlan) {
      // Update existing plan
      setDispatchPlans(plans => 
        plans.map(plan => 
          plan.id === editingPlan.id 
            ? { ...plan, ...values, plannedLoadingDate: values.plannedLoadingDate.format('YYYY-MM-DD'), plannedDeliveryDate: values.plannedDeliveryDate.format('YYYY-MM-DD') }
            : plan
        )
      );
      message.success('Dispatch plan updated successfully!');
    } else {
      // Create new plan
      const newPlan: DispatchPlan = {
        id: `DP-${String(dispatchPlans.length + 1).padStart(3, '0')}`,
        ...values,
        plannedLoadingDate: values.plannedLoadingDate.format('YYYY-MM-DD'),
        plannedDeliveryDate: values.plannedDeliveryDate.format('YYYY-MM-DD'),
        status: 'Planned' as const,
        estimatedCost: values.quantity * (values.transportMode === 'Road' ? 85 : values.transportMode === 'Rail' ? 65 : 40)
      };
      setDispatchPlans([...dispatchPlans, newPlan]);
      message.success('Dispatch plan created successfully!');
    }
    setIsModalVisible(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Planned': return 'blue';
      case 'Assigned': return 'orange';
      case 'Loading': return 'purple';
      case 'Dispatched': return 'green';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Planned': return <ClockCircleOutlined />;
      case 'Assigned': return <EditOutlined />;
      case 'Loading': return <TruckOutlined />;
      case 'Dispatched': return <CheckCircleOutlined />;
      default: return null;
    }
  };

  const columns = [
    {
      title: 'Dispatch ID',
      dataIndex: 'id',
      key: 'id',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'Order ID',
      dataIndex: 'orderId',
      key: 'orderId',
      render: (text: string) => <Text type="secondary">{text}</Text>
    },
    {
      title: 'Route',
      key: 'route',
      render: (record: DispatchPlan) => (
        <Space direction="vertical" size="small">
          <Text strong>{record.sourcePlant}</Text>
          <Text type="secondary">↓</Text>
          <Text>{record.destinationPlant}</Text>
        </Space>
      )
    },
    {
      title: 'Quantity',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (value: number) => `${value.toLocaleString()} MT`
    },
    {
      title: 'Transport',
      key: 'transport',
      render: (record: DispatchPlan) => (
        <Space direction="vertical" size="small">
          <Tag color="blue">{record.transportMode}</Tag>
          <Text style={{ fontSize: '12px' }}>{record.carrier}</Text>
        </Space>
      )
    },
    {
      title: 'Vehicle/Driver',
      key: 'vehicle',
      render: (record: DispatchPlan) => (
        <Space direction="vertical" size="small">
          <Text strong>{record.vehicleNumber}</Text>
          <Text style={{ fontSize: '12px' }}>{record.driverName}</Text>
          <Text style={{ fontSize: '11px', color: '#666' }}>{record.driverPhone}</Text>
        </Space>
      )
    },
    {
      title: 'Schedule',
      key: 'schedule',
      render: (record: DispatchPlan) => (
        <Space direction="vertical" size="small">
          <Text style={{ fontSize: '12px' }}>Loading: {record.plannedLoadingDate}</Text>
          <Text style={{ fontSize: '12px' }}>Delivery: {record.plannedDeliveryDate}</Text>
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
      title: 'Est. Cost',
      dataIndex: 'estimatedCost',
      key: 'estimatedCost',
      render: (value: number) => `₹${(value/100000).toFixed(1)}L`
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: DispatchPlan) => (
        <Button 
          size="small" 
          icon={<EditOutlined />}
          onClick={() => handleEditPlan(record)}
        >
          Edit
        </Button>
      )
    }
  ];

  const totalQuantity = dispatchPlans.reduce((sum, plan) => sum + plan.quantity, 0);
  const totalCost = dispatchPlans.reduce((sum, plan) => sum + plan.estimatedCost, 0);
  const plannedCount = dispatchPlans.filter(p => p.status === 'Planned').length;
  const activeCount = dispatchPlans.filter(p => ['Assigned', 'Loading'].includes(p.status)).length;

  return (
    <div>
      <Title level={2} style={{ color: '#1f4e79', marginBottom: 24 }}>
        <TruckOutlined /> Dispatch Planning
      </Title>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#1890ff', margin: 0 }}>
                {dispatchPlans.length}
              </Title>
              <Text type="secondary">Total Plans</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#52c41a', margin: 0 }}>
                {totalQuantity.toLocaleString()}
              </Title>
              <Text type="secondary">Total MT</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#faad14', margin: 0 }}>
                {activeCount}
              </Title>
              <Text type="secondary">Active Plans</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#1f4e79', margin: 0 }}>
                ₹{(totalCost/10000000).toFixed(1)}Cr
              </Title>
              <Text type="secondary">Total Cost</Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Dispatch Plans Table */}
      <Card 
        title="Dispatch Plans" 
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleCreatePlan}
          >
            Create Plan
          </Button>
        }
      >
        <Table
          dataSource={dispatchPlans}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingPlan ? "Edit Dispatch Plan" : "Create Dispatch Plan"}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="orderId"
                label="Order ID"
                rules={[{ required: true, message: 'Please enter order ID' }]}
              >
                <Input placeholder="Enter order ID" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="quantity"
                label="Quantity (MT)"
                rules={[{ required: true, message: 'Please enter quantity' }]}
              >
                <Input type="number" placeholder="Enter quantity" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="sourcePlant"
                label="Source Plant"
                rules={[{ required: true, message: 'Please enter source plant' }]}
              >
                <Input placeholder="Enter source plant" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="destinationPlant"
                label="Destination Plant"
                rules={[{ required: true, message: 'Please enter destination' }]}
              >
                <Input placeholder="Enter destination" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="transportMode"
                label="Transport Mode"
                rules={[{ required: true, message: 'Please select transport mode' }]}
              >
                <Select placeholder="Select transport mode">
                  {transportModes.map(mode => (
                    <Option key={mode} value={mode}>{mode}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="carrier"
                label="Carrier"
                rules={[{ required: true, message: 'Please select carrier' }]}
              >
                <Select placeholder="Select carrier">
                  {carriers.map(carrier => (
                    <Option key={carrier} value={carrier}>{carrier}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="vehicleNumber"
                label="Vehicle Number"
                rules={[{ required: true, message: 'Please enter vehicle number' }]}
              >
                <Input placeholder="Enter vehicle number" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="driverName"
                label="Driver Name"
                rules={[{ required: true, message: 'Please enter driver name' }]}
              >
                <Input placeholder="Enter driver name" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="driverPhone"
                label="Driver Phone"
                rules={[{ required: true, message: 'Please enter driver phone' }]}
              >
                <Input placeholder="Enter driver phone" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="plannedLoadingDate"
                label="Planned Loading Date"
                rules={[{ required: true, message: 'Please select loading date' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="plannedDeliveryDate"
                label="Planned Delivery Date"
                rules={[{ required: true, message: 'Please select delivery date' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item style={{ textAlign: 'right', marginTop: 24 }}>
            <Space>
              <Button onClick={() => setIsModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {editingPlan ? 'Update Plan' : 'Create Plan'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DispatchPlanning;