import React, { useState } from 'react';
import { 
  Card, 
  Table, 
  Row, 
  Col, 
  Typography, 
  Tag, 
  Button,
  Space,
  Statistic,
  Progress,
  Descriptions
} from 'antd';
import { 
  DollarOutlined, 
  FileTextOutlined, 
  CalculatorOutlined,
  TruckOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;

interface BillingRecord {
  id: string;
  grnId: string;
  vehicleNumber: string;
  route: string;
  quantity: number;
  transportMode: string;
  distance: number;
  baseRate: number;
  totalFreight: number;
  fuelSurcharge: number;
  otherCharges: number;
  totalAmount: number;
  costPerMT: number;
  invoiceNumber?: string;
  invoiceDate?: string;
  paymentStatus: 'Pending' | 'Approved' | 'Paid';
  carrier: string;
}

const BillingCosting = () => {
  const [billingRecords] = useState<BillingRecord[]>([
    {
      id: 'BILL-001',
      grnId: 'GRN-001',
      vehicleNumber: 'CG-01-AB-1234',
      route: 'ACC Jamul Plant → Ambuja Dadri Terminal',
      quantity: 2485,
      transportMode: 'Road',
      distance: 1200,
      baseRate: 850,
      totalFreight: 2112250,
      fuelSurcharge: 105612,
      otherCharges: 25000,
      totalAmount: 2242862,
      costPerMT: 902,
      invoiceNumber: 'INV-2025-001',
      invoiceDate: '2025-01-10',
      paymentStatus: 'Approved',
      carrier: 'Adani Logistics'
    },
    {
      id: 'BILL-002',
      grnId: 'GRN-002',
      vehicleNumber: 'TS-09-CD-5678',
      route: 'Orient Devapur Plant → ACC Sindri Terminal',
      quantity: 3150,
      transportMode: 'Road',
      distance: 150,
      baseRate: 400,
      totalFreight: 1260000,
      fuelSurcharge: 63000,
      otherCharges: 15000,
      totalAmount: 1338000,
      costPerMT: 425,
      invoiceNumber: 'INV-2025-002',
      invoiceDate: '2025-01-08',
      paymentStatus: 'Paid',
      carrier: 'Express Transporters'
    },
    {
      id: 'BILL-003',
      grnId: 'GRN-003',
      vehicleNumber: 'RAKE-5678',
      route: 'Ambuja Ambujanagar Plant → Penna Krishnapatnam Terminal',
      quantity: 1350,
      transportMode: 'Rail',
      distance: 1600,
      baseRate: 650,
      totalFreight: 877500,
      fuelSurcharge: 43875,
      otherCharges: 20000,
      totalAmount: 941375,
      costPerMT: 697,
      paymentStatus: 'Pending',
      carrier: 'Indian Railways'
    },
    {
      id: 'BILL-004',
      grnId: 'GRN-004',
      vehicleNumber: 'RAKE-9012',
      route: 'Penna Tandur Plant → Ambuja Sankrail Terminal',
      quantity: 2795,
      transportMode: 'Rail',
      distance: 1600,
      baseRate: 650,
      totalFreight: 1816750,
      fuelSurcharge: 90837,
      otherCharges: 30000,
      totalAmount: 1937587,
      costPerMT: 693,
      invoiceNumber: 'INV-2025-004',
      invoiceDate: '2025-01-15',
      paymentStatus: 'Approved',
      carrier: 'Indian Railways'
    },
    {
      id: 'BILL-005',
      grnId: 'GRN-005',
      vehicleNumber: 'VESSEL-001',
      route: 'Sanghi Sanghipuram Plant → ACC Vizag Terminal',
      quantity: 4500,
      transportMode: 'Sea',
      distance: 1600,
      baseRate: 400,
      totalFreight: 1800000,
      fuelSurcharge: 90000,
      otherCharges: 50000,
      totalAmount: 1940000,
      costPerMT: 431,
      paymentStatus: 'Pending',
      carrier: 'Coastal Shipping Corp'
    },
    {
      id: 'BILL-006',
      grnId: 'GRN-006',
      vehicleNumber: 'KA-03-EF-9012',
      route: 'ACC Wadi Plant → Ambuja Tuticorin Terminal',
      quantity: 3580,
      transportMode: 'Road',
      distance: 600,
      baseRate: 750,
      totalFreight: 2685000,
      fuelSurcharge: 134250,
      otherCharges: 35000,
      totalAmount: 2854250,
      costPerMT: 797,
      invoiceNumber: 'INV-2025-006',
      invoiceDate: '2025-01-16',
      paymentStatus: 'Paid',
      carrier: 'Reliable Cargo'
    }
  ]);

  const getPaymentStatusColor = (status: string) => {
    switch (status) {
      case 'Pending': return 'orange';
      case 'Approved': return 'blue';
      case 'Paid': return 'green';
      default: return 'default';
    }
  };

  const getPaymentStatusIcon = (status: string) => {
    switch (status) {
      case 'Pending': return <ClockCircleOutlined />;
      case 'Approved': return <FileTextOutlined />;
      case 'Paid': return <CheckCircleOutlined />;
      default: return null;
    }
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 10000000) {
      return `₹${(amount / 10000000).toFixed(2)} Cr`;
    } else if (amount >= 100000) {
      return `₹${(amount / 100000).toFixed(2)} L`;
    } else {
      return `₹${amount.toLocaleString()}`;
    }
  };

  const columns = [
    {
      title: 'Bill ID',
      dataIndex: 'id',
      key: 'id',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'GRN/Vehicle',
      key: 'grn',
      render: (record: BillingRecord) => (
        <Space direction="vertical" size="small">
          <Text>{record.grnId}</Text>
          <Text style={{ fontSize: '12px' }}>{record.vehicleNumber}</Text>
        </Space>
      )
    },
    {
      title: 'Route & Mode',
      key: 'route',
      render: (record: BillingRecord) => (
        <Space direction="vertical" size="small">
          <Text>{record.route}</Text>
          <Tag color="blue">{record.transportMode}</Tag>
          <Text style={{ fontSize: '11px' }}>{record.distance} km</Text>
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
      title: 'Freight Cost',
      key: 'freight',
      render: (record: BillingRecord) => (
        <Space direction="vertical" size="small">
          <Text strong>{formatCurrency(record.totalFreight)}</Text>
          <Text style={{ fontSize: '11px' }}>Base: ₹{record.baseRate}/MT</Text>
        </Space>
      )
    },
    {
      title: 'Additional Charges',
      key: 'charges',
      render: (record: BillingRecord) => (
        <Space direction="vertical" size="small">
          <Text style={{ fontSize: '12px' }}>Fuel: {formatCurrency(record.fuelSurcharge)}</Text>
          <Text style={{ fontSize: '12px' }}>Other: {formatCurrency(record.otherCharges)}</Text>
        </Space>
      )
    },
    {
      title: 'Total Amount',
      key: 'total',
      render: (record: BillingRecord) => (
        <Space direction="vertical" size="small">
          <Text strong style={{ color: '#1f4e79' }}>{formatCurrency(record.totalAmount)}</Text>
          <Text style={{ fontSize: '11px' }}>₹{record.costPerMT}/MT</Text>
        </Space>
      )
    },
    {
      title: 'Invoice',
      key: 'invoice',
      render: (record: BillingRecord) => (
        <Space direction="vertical" size="small">
          {record.invoiceNumber ? (
            <>
              <Text style={{ fontSize: '12px' }}>{record.invoiceNumber}</Text>
              <Text style={{ fontSize: '11px' }}>{record.invoiceDate}</Text>
            </>
          ) : (
            <Text type="secondary">Pending</Text>
          )}
        </Space>
      )
    },
    {
      title: 'Payment Status',
      dataIndex: 'paymentStatus',
      key: 'paymentStatus',
      render: (status: string) => (
        <Tag color={getPaymentStatusColor(status)} icon={getPaymentStatusIcon(status)}>
          {status}
        </Tag>
      )
    },
    {
      title: 'Carrier',
      dataIndex: 'carrier',
      key: 'carrier',
      render: (text: string) => <Text style={{ fontSize: '12px' }}>{text}</Text>
    }
  ];

  const totalAmount = billingRecords.reduce((sum, record) => sum + record.totalAmount, 0);
  const totalQuantity = billingRecords.reduce((sum, record) => sum + record.quantity, 0);
  const avgCostPerMT = totalAmount / totalQuantity;
  const pendingPayments = billingRecords.filter(r => r.paymentStatus === 'Pending').length;
  const paidAmount = billingRecords.filter(r => r.paymentStatus === 'Paid').reduce((sum, r) => sum + r.totalAmount, 0);

  // Mode-wise analysis
  const roadCost = billingRecords.filter(r => r.transportMode === 'Road').reduce((sum, r) => sum + r.totalAmount, 0);
  const railCost = billingRecords.filter(r => r.transportMode === 'Rail').reduce((sum, r) => sum + r.totalAmount, 0);
  const roadQuantity = billingRecords.filter(r => r.transportMode === 'Road').reduce((sum, r) => sum + r.quantity, 0);
  const railQuantity = billingRecords.filter(r => r.transportMode === 'Rail').reduce((sum, r) => sum + r.quantity, 0);

  return (
    <div>
      <Title level={2} style={{ color: '#1f4e79', marginBottom: 24 }}>
        <DollarOutlined /> Billing & Costing
      </Title>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Billing"
              value={totalAmount}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<DollarOutlined style={{ color: '#1f4e79' }} />}
              valueStyle={{ color: '#1f4e79' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Avg Cost/MT"
              value={avgCostPerMT}
              precision={0}
              prefix="₹"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Pending Payments"
              value={pendingPayments}
              prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Payment Rate"
              value={(paidAmount / totalAmount) * 100}
              precision={1}
              suffix="%"
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        {/* Mode-wise Cost Analysis */}
        <Col xs={24} lg={12}>
          <Card title="Transport Mode Analysis">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Row justify="space-between">
                  <Text strong>Road Transport</Text>
                  <Text>{formatCurrency(roadCost)}</Text>
                </Row>
                <Progress 
                  percent={(roadCost / totalAmount) * 100} 
                  size="small"
                  showInfo={false}
                />
                <Text style={{ fontSize: '11px' }}>
                  {roadQuantity.toLocaleString()} MT • ₹{Math.round(roadCost / roadQuantity)}/MT
                </Text>
              </div>
              
              <div>
                <Row justify="space-between">
                  <Text strong>Rail Transport</Text>
                  <Text>{formatCurrency(railCost)}</Text>
                </Row>
                <Progress 
                  percent={(railCost / totalAmount) * 100} 
                  size="small"
                  showInfo={false}
                />
                <Text style={{ fontSize: '11px' }}>
                  {railQuantity.toLocaleString()} MT • ₹{Math.round(railCost / railQuantity)}/MT
                </Text>
              </div>
            </Space>
          </Card>
        </Col>

        {/* Cost Breakdown */}
        <Col xs={24} lg={12}>
          <Card title="Cost Breakdown">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Base Freight">
                {formatCurrency(billingRecords.reduce((sum, r) => sum + r.totalFreight, 0))}
              </Descriptions.Item>
              <Descriptions.Item label="Fuel Surcharge">
                {formatCurrency(billingRecords.reduce((sum, r) => sum + r.fuelSurcharge, 0))}
              </Descriptions.Item>
              <Descriptions.Item label="Other Charges">
                {formatCurrency(billingRecords.reduce((sum, r) => sum + r.otherCharges, 0))}
              </Descriptions.Item>
              <Descriptions.Item label="Total Amount">
                <Text strong style={{ color: '#1f4e79' }}>
                  {formatCurrency(totalAmount)}
                </Text>
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>

      {/* Billing Records Table */}
      <Card 
        title="Billing Records" 
        extra={
          <Space>
            <Button icon={<CalculatorOutlined />}>
              Calculate Costs
            </Button>
            <Button type="primary" icon={<FileTextOutlined />}>
              Generate Invoice
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={billingRecords}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
          scroll={{ x: 1400, y: 400 }}
        />
      </Card>
    </div>
  );
};

export default BillingCosting;