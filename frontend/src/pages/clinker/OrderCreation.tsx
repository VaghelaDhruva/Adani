import React, { useState } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Select, 
  DatePicker, 
  InputNumber, 
  Button, 
  Row, 
  Col, 
  Typography, 
  Space,
  Table,
  Tag,
  message
} from 'antd';
import { PlusOutlined, SaveOutlined, CheckCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

interface Order {
  id: string;
  sourcePlant: string;
  destinationPlant: string;
  quantity: number;
  requiredDate: string;
  priority: string;
  status: string;
  createdBy: string;
  createdAt: string;
}

const OrderCreation = () => {
  const [form] = Form.useForm();
  const [orders, setOrders] = useState<Order[]>([
    {
      id: 'ORD-001',
      sourcePlant: 'ACC Jamul Plant',
      destinationPlant: 'Ambuja Dadri Terminal',
      quantity: 2500,
      requiredDate: '2025-01-15',
      priority: 'High',
      status: 'Pending',
      createdBy: 'ACC Sales Team',
      createdAt: '2025-01-05'
    },
    {
      id: 'ORD-002',
      sourcePlant: 'Ambuja Ambujanagar Plant',
      destinationPlant: 'Penna Krishnapatnam Terminal',
      quantity: 1800,
      requiredDate: '2025-01-12',
      priority: 'Medium',
      status: 'Approved',
      createdBy: 'Ambuja Plant Manager',
      createdAt: '2025-01-04'
    },
    {
      id: 'ORD-003',
      sourcePlant: 'Orient Devapur Plant',
      destinationPlant: 'ACC Sindri Terminal',
      quantity: 3200,
      requiredDate: '2025-01-18',
      priority: 'Critical',
      status: 'Approved',
      createdBy: 'Orient Operations',
      createdAt: '2025-01-03'
    },
    {
      id: 'ORD-004',
      sourcePlant: 'Penna Tandur Plant',
      destinationPlant: 'Ambuja Sankrail Terminal',
      quantity: 2800,
      requiredDate: '2025-01-20',
      priority: 'High',
      status: 'Pending',
      createdBy: 'Penna Logistics',
      createdAt: '2025-01-02'
    },
    {
      id: 'ORD-005',
      sourcePlant: 'Sanghi Sanghipuram Plant',
      destinationPlant: 'ACC Vizag Terminal',
      quantity: 4500,
      requiredDate: '2025-01-25',
      priority: 'Medium',
      status: 'In Transit',
      createdBy: 'Sanghi Sales',
      createdAt: '2025-01-01'
    },
    {
      id: 'ORD-006',
      sourcePlant: 'ACC Wadi Plant',
      destinationPlant: 'Ambuja Tuticorin Terminal',
      quantity: 3600,
      requiredDate: '2025-01-22',
      priority: 'High',
      status: 'Approved',
      createdBy: 'ACC Karnataka',
      createdAt: '2024-12-30'
    },
    {
      id: 'ORD-007',
      sourcePlant: 'Ambuja Marwar Mundwa Plant',
      destinationPlant: 'Orient Jalgaon Terminal',
      quantity: 2200,
      requiredDate: '2025-01-28',
      priority: 'Low',
      status: 'Pending',
      createdBy: 'Ambuja Rajasthan',
      createdAt: '2024-12-29'
    },
    {
      id: 'ORD-008',
      sourcePlant: 'ACC Chaibasa Plant',
      destinationPlant: 'Penna Patas Terminal',
      quantity: 1900,
      requiredDate: '2025-01-30',
      priority: 'Medium',
      status: 'Draft',
      createdBy: 'ACC Jharkhand',
      createdAt: '2024-12-28'
    }
  ]);

  const plants = [
    'ACC Jamul Plant',
    'ACC Kymore Plant',
    'ACC Chanda Plant',
    'ACC Wadi Plant',
    'ACC Gagal Plant',
    'Ambuja Ambujanagar Plant',
    'Ambuja Darlaghat Plant',
    'Ambuja Maratha Plant',
    'Ambuja Rabriyawas Plant',
    'Ambuja Bhatapara Plant',
    'Sanghi Sanghipuram Plant',
    'Penna Talaricheruvu Plant',
    'Penna Boyareddypalli Plant',
    'Penna Tandur Plant',
    'Orient Devapur Plant',
    'Orient Chittapur Plant',
    'ACC Tikaria Terminal',
    'ACC Sindri Terminal',
    'Ambuja Roorkee Terminal',
    'Ambuja Dadri Terminal',
    'Ambuja Sankrail Terminal',
    'Penna Krishnapatnam Terminal',
    'Orient Jalgaon Terminal'
  ];

  const priorities = ['Low', 'Medium', 'High', 'Critical'];

  const handleSubmit = (values: any) => {
    const newOrder: Order = {
      id: `ORD-${String(orders.length + 1).padStart(3, '0')}`,
      sourcePlant: values.sourcePlant,
      destinationPlant: values.destinationPlant,
      quantity: values.quantity,
      requiredDate: values.requiredDate.format('YYYY-MM-DD'),
      priority: values.priority,
      status: 'Pending',
      createdBy: 'Current User',
      createdAt: new Date().toISOString().split('T')[0]
    };

    setOrders([...orders, newOrder]);
    form.resetFields();
    message.success('Order created successfully!');
  };

  const columns = [
    {
      title: 'Order ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      fixed: 'left' as const,
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'Source Plant',
      dataIndex: 'sourcePlant',
      key: 'sourcePlant',
      width: 200,
      ellipsis: true,
    },
    {
      title: 'Destination',
      dataIndex: 'destinationPlant',
      key: 'destinationPlant',
      width: 200,
      ellipsis: true,
    },
    {
      title: 'Quantity (MT)',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 120,
      render: (value: number) => `${value.toLocaleString()} MT`
    },
    {
      title: 'Required Date',
      dataIndex: 'requiredDate',
      key: 'requiredDate',
      width: 120,
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority: string) => {
        const color = priority === 'Critical' ? 'red' : 
                     priority === 'High' ? 'orange' :
                     priority === 'Medium' ? 'blue' : 'green';
        return <Tag color={color}>{priority}</Tag>;
      }
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const color = status === 'Approved' ? 'green' : 
                     status === 'Pending' ? 'orange' : 
                     status === 'In Transit' ? 'blue' :
                     status === 'Draft' ? 'gray' : 'red';
        return <Tag color={color}>{status}</Tag>;
      }
    },
    {
      title: 'Created By',
      dataIndex: 'createdBy',
      key: 'createdBy',
      width: 150,
      ellipsis: true,
    },
    {
      title: 'Created Date',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 120,
    }
  ];

  return (
    <div style={{ padding: '0 16px' }}>
      <Title level={2} style={{ color: '#1f4e79', marginBottom: 24 }}>
        <PlusOutlined /> Order & Demand Creation
      </Title>
      
      <Row gutter={[24, 24]} style={{ minHeight: '70vh' }}>
        {/* Order Creation Form */}
        <Col xs={24} xl={8} lg={10}>
          <Card 
            title="Create New Clinker Order" 
            extra={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            style={{ height: '600px', overflow: 'auto' }}
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
            >
              <Form.Item
                name="sourcePlant"
                label="Source Plant"
                rules={[{ required: true, message: 'Please select source plant' }]}
              >
                <Select 
                  placeholder="Select source plant"
                  showSearch
                  filterOption={(input, option) =>
                    (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {plants.map(plant => (
                    <Option key={plant} value={plant}>{plant}</Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="destinationPlant"
                label="Destination Plant/Customer"
                rules={[{ required: true, message: 'Please select destination' }]}
              >
                <Select 
                  placeholder="Select destination"
                  showSearch
                  filterOption={(input, option) =>
                    (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {plants.map(plant => (
                    <Option key={plant} value={plant}>{plant}</Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="quantity"
                label="Quantity (MT)"
                rules={[{ required: true, message: 'Please enter quantity' }]}
              >
                <InputNumber
                  min={1}
                  max={10000}
                  style={{ width: '100%' }}
                  placeholder="Enter quantity in MT"
                />
              </Form.Item>

              <Form.Item
                name="requiredDate"
                label="Required Delivery Date"
                rules={[{ required: true, message: 'Please select delivery date' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                name="priority"
                label="Priority Level"
                rules={[{ required: true, message: 'Please select priority' }]}
              >
                <Select placeholder="Select priority">
                  {priorities.map(priority => (
                    <Option key={priority} value={priority}>{priority}</Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  icon={<SaveOutlined />}
                  size="large"
                  style={{ width: '100%' }}
                >
                  Create Order
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* Orders List */}
        <Col xs={24} xl={16} lg={14}>
          <Card 
            title="Recent Orders" 
            extra={<Text>Total: {orders.length} orders</Text>}
            style={{ height: '600px' }}
          >
            <div style={{ height: '500px', overflow: 'hidden' }}>
              <Table
                dataSource={orders}
                columns={columns}
                rowKey="id"
                pagination={false}
                size="small"
                scroll={{ 
                  y: 450,
                  x: 1200
                }}
                style={{ 
                  width: '100%'
                }}
              />
            </div>
          </Card>
        </Col>
      </Row>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#1890ff', margin: 0 }}>
                {orders.length}
              </Title>
              <Text type="secondary">Total Orders</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#52c41a', margin: 0 }}>
                {orders.filter(o => o.status === 'Approved').length}
              </Title>
              <Text type="secondary">Approved</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#faad14', margin: 0 }}>
                {orders.filter(o => o.status === 'Pending').length}
              </Title>
              <Text type="secondary">Pending</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#1f4e79', margin: 0 }}>
                {orders.reduce((sum, o) => sum + o.quantity, 0).toLocaleString()}
              </Title>
              <Text type="secondary">Total MT</Text>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default OrderCreation;