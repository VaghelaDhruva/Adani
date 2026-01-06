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
  Input,
  InputNumber,
  DatePicker,
  Space,
  message,
  Descriptions
} from 'antd';
import { 
  CheckSquareOutlined, 
  PlusOutlined, 
  FileTextOutlined,
  WarningOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface GRN {
  id: string;
  shipmentId: string;
  vehicleNumber: string;
  deliveryDate: string;
  unloadingStart: string;
  unloadingEnd: string;
  plannedQuantity: number;
  receivedQuantity: number;
  variance: number;
  variancePercent: number;
  status: 'Pending' | 'In Progress' | 'Completed' | 'Discrepancy';
  receivedBy: string;
  remarks?: string;
  grnNumber?: string;
}

const DeliveryGRN = () => {
  const [grns, setGrns] = useState<GRN[]>([
    {
      id: 'GRN-001',
      shipmentId: 'SH-001',
      vehicleNumber: 'CG-01-AB-1234',
      deliveryDate: '2025-01-10',
      unloadingStart: '14:30',
      unloadingEnd: '16:15',
      plannedQuantity: 2500,
      receivedQuantity: 2485,
      variance: -15,
      variancePercent: -0.6,
      status: 'Completed',
      receivedBy: 'Warehouse Manager',
      remarks: 'Minor spillage during transport',
      grnNumber: 'GRN-2025-001'
    },
    {
      id: 'GRN-002',
      shipmentId: 'SH-003',
      vehicleNumber: 'TS-09-CD-5678',
      deliveryDate: '2025-01-08',
      unloadingStart: '12:00',
      unloadingEnd: '13:30',
      plannedQuantity: 3200,
      receivedQuantity: 3150,
      variance: -50,
      variancePercent: -1.56,
      status: 'Discrepancy',
      receivedBy: 'Site Supervisor',
      remarks: 'Weight difference noted, investigating cause'
    },
    {
      id: 'GRN-003',
      shipmentId: 'SH-002',
      vehicleNumber: 'RAKE-5678',
      deliveryDate: '2025-01-11',
      unloadingStart: '18:00',
      unloadingEnd: '',
      plannedQuantity: 1800,
      receivedQuantity: 1350,
      variance: 0,
      variancePercent: 0,
      status: 'In Progress',
      receivedBy: 'Terminal Operator'
    },
    {
      id: 'GRN-004',
      shipmentId: 'SH-004',
      vehicleNumber: 'RAKE-9012',
      deliveryDate: '2025-01-15',
      unloadingStart: '10:00',
      unloadingEnd: '12:30',
      plannedQuantity: 2800,
      receivedQuantity: 2795,
      variance: -5,
      variancePercent: -0.18,
      status: 'Completed',
      receivedBy: 'Plant Manager',
      remarks: 'Excellent delivery condition',
      grnNumber: 'GRN-2025-004'
    },
    {
      id: 'GRN-005',
      shipmentId: 'SH-005',
      vehicleNumber: 'VESSEL-001',
      deliveryDate: '2025-01-19',
      unloadingStart: '08:00',
      unloadingEnd: '',
      plannedQuantity: 4500,
      receivedQuantity: 0,
      variance: 0,
      variancePercent: 0,
      status: 'Pending',
      receivedBy: 'Port Authority'
    },
    {
      id: 'GRN-006',
      shipmentId: 'SH-006',
      vehicleNumber: 'KA-03-EF-9012',
      deliveryDate: '2025-01-16',
      unloadingStart: '14:00',
      unloadingEnd: '16:45',
      plannedQuantity: 3600,
      receivedQuantity: 3580,
      variance: -20,
      variancePercent: -0.56,
      status: 'Completed',
      receivedBy: 'Quality Inspector',
      remarks: 'Good quality material received',
      grnNumber: 'GRN-2025-006'
    }
  ]);

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedGrn, setSelectedGrn] = useState<GRN | null>(null);
  const [form] = Form.useForm();

  const handleCreateGRN = (grn: GRN) => {
    setSelectedGrn(grn);
    form.setFieldsValue({
      ...grn,
      deliveryDate: grn.deliveryDate,
      unloadingStart: grn.unloadingStart,
      unloadingEnd: grn.unloadingEnd
    });
    setIsModalVisible(true);
  };

  const handleSubmit = (values: any) => {
    const updatedGrn = {
      ...selectedGrn!,
      ...values,
      receivedQuantity: values.receivedQuantity,
      variance: values.receivedQuantity - selectedGrn!.plannedQuantity,
      variancePercent: ((values.receivedQuantity - selectedGrn!.plannedQuantity) / selectedGrn!.plannedQuantity) * 100,
      status: Math.abs(((values.receivedQuantity - selectedGrn!.plannedQuantity) / selectedGrn!.plannedQuantity) * 100) > 2 ? 'Discrepancy' : 'Completed',
      grnNumber: selectedGrn!.grnNumber || `GRN-2025-${String(grns.length + 1).padStart(3, '0')}`
    };

    setGrns(grns.map(grn => grn.id === selectedGrn!.id ? updatedGrn : grn));
    setIsModalVisible(false);
    message.success('GRN updated successfully!');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Pending': return 'blue';
      case 'In Progress': return 'orange';
      case 'Completed': return 'green';
      case 'Discrepancy': return 'red';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Pending': return <FileTextOutlined />;
      case 'In Progress': return <CheckSquareOutlined />;
      case 'Completed': return <CheckCircleOutlined />;
      case 'Discrepancy': return <WarningOutlined />;
      default: return null;
    }
  };

  const getVarianceColor = (variance: number) => {
    if (Math.abs(variance) <= 25) return '#52c41a'; // Green for acceptable variance
    if (Math.abs(variance) <= 50) return '#faad14'; // Orange for moderate variance
    return '#f5222d'; // Red for high variance
  };

  const columns = [
    {
      title: 'GRN ID',
      dataIndex: 'id',
      key: 'id',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'Vehicle',
      dataIndex: 'vehicleNumber',
      key: 'vehicleNumber',
      render: (text: string, record: GRN) => (
        <Space direction="vertical" size="small">
          <Text strong>{text}</Text>
          <Text style={{ fontSize: '12px' }}>Shipment: {record.shipmentId}</Text>
        </Space>
      )
    },
    {
      title: 'Delivery Date',
      dataIndex: 'deliveryDate',
      key: 'deliveryDate',
    },
    {
      title: 'Unloading Time',
      key: 'unloading',
      render: (record: GRN) => (
        <Space direction="vertical" size="small">
          <Text style={{ fontSize: '12px' }}>Start: {record.unloadingStart}</Text>
          {record.unloadingEnd && (
            <Text style={{ fontSize: '12px' }}>End: {record.unloadingEnd}</Text>
          )}
        </Space>
      )
    },
    {
      title: 'Quantity (MT)',
      key: 'quantity',
      render: (record: GRN) => (
        <Space direction="vertical" size="small">
          <Text>Planned: {record.plannedQuantity.toLocaleString()}</Text>
          <Text strong>Received: {record.receivedQuantity.toLocaleString()}</Text>
        </Space>
      )
    },
    {
      title: 'Variance',
      key: 'variance',
      render: (record: GRN) => (
        <Space direction="vertical" size="small">
          <Text style={{ color: getVarianceColor(record.variance) }}>
            {record.variance > 0 ? '+' : ''}{record.variance} MT
          </Text>
          <Text style={{ fontSize: '11px', color: getVarianceColor(record.variance) }}>
            ({record.variancePercent > 0 ? '+' : ''}{record.variancePercent.toFixed(2)}%)
          </Text>
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
      title: 'Received By',
      dataIndex: 'receivedBy',
      key: 'receivedBy',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: GRN) => (
        <Space>
          <Button 
            size="small" 
            icon={<FileTextOutlined />}
            onClick={() => handleCreateGRN(record)}
          >
            {record.status === 'Completed' ? 'View' : 'Update'}
          </Button>
        </Space>
      )
    }
  ];

  const totalDeliveries = grns.length;
  const completedDeliveries = grns.filter(g => g.status === 'Completed').length;
  const discrepancies = grns.filter(g => g.status === 'Discrepancy').length;
  const totalReceived = grns.reduce((sum, g) => sum + g.receivedQuantity, 0);

  return (
    <div>
      <Title level={2} style={{ color: '#1f4e79', marginBottom: 24 }}>
        <CheckSquareOutlined /> Delivery & GRN
      </Title>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#1890ff', margin: 0 }}>
                {totalDeliveries}
              </Title>
              <Text type="secondary">Total Deliveries</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#52c41a', margin: 0 }}>
                {completedDeliveries}
              </Title>
              <Text type="secondary">Completed</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#f5222d', margin: 0 }}>
                {discrepancies}
              </Title>
              <Text type="secondary">Discrepancies</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#1f4e79', margin: 0 }}>
                {totalReceived.toLocaleString()}
              </Title>
              <Text type="secondary">Total Received (MT)</Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* GRN Table */}
      <Card title="Goods Receipt Notes (GRN)">
        <Table
          dataSource={grns}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
          scroll={{ x: 1000, y: 400 }}
          rowClassName={(record) => {
            if (record.status === 'Discrepancy') return 'discrepancy-row';
            return '';
          }}
        />
      </Card>

      {/* GRN Details Modal */}
      <Modal
        title={`GRN Details - ${selectedGrn?.id}`}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedGrn && (
          <>
            <Descriptions bordered column={2} style={{ marginBottom: 24 }}>
              <Descriptions.Item label="Shipment ID">{selectedGrn.shipmentId}</Descriptions.Item>
              <Descriptions.Item label="Vehicle">{selectedGrn.vehicleNumber}</Descriptions.Item>
              <Descriptions.Item label="Delivery Date">{selectedGrn.deliveryDate}</Descriptions.Item>
              <Descriptions.Item label="Planned Quantity">{selectedGrn.plannedQuantity} MT</Descriptions.Item>
            </Descriptions>

            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
            >
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    name="unloadingStart"
                    label="Unloading Start Time"
                    rules={[{ required: true, message: 'Please enter start time' }]}
                  >
                    <Input placeholder="HH:MM" />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    name="unloadingEnd"
                    label="Unloading End Time"
                  >
                    <Input placeholder="HH:MM" />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    name="receivedQuantity"
                    label="Received Quantity (MT)"
                    rules={[{ required: true, message: 'Please enter received quantity' }]}
                  >
                    <InputNumber
                      min={0}
                      style={{ width: '100%' }}
                      placeholder="Enter actual received quantity"
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    name="receivedBy"
                    label="Received By"
                    rules={[{ required: true, message: 'Please enter receiver name' }]}
                  >
                    <Input placeholder="Enter receiver name" />
                  </Form.Item>
                </Col>
                <Col xs={24}>
                  <Form.Item
                    name="remarks"
                    label="Remarks"
                  >
                    <TextArea 
                      rows={3} 
                      placeholder="Enter any remarks about the delivery..."
                    />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item style={{ textAlign: 'right', marginTop: 24 }}>
                <Space>
                  <Button onClick={() => setIsModalVisible(false)}>
                    Cancel
                  </Button>
                  <Button type="primary" htmlType="submit">
                    Update GRN
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </>
        )}
      </Modal>

      <style jsx>{`
        .discrepancy-row {
          background-color: #fff2f0 !important;
        }
      `}</style>
    </div>
  );
};

export default DeliveryGRN;