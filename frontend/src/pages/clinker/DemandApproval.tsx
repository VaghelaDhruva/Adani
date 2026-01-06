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
  Select,
  Space,
  message,
  Descriptions,
  Alert,
  Statistic,
  Progress
} from 'antd';
import { 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  ClockCircleOutlined,
  EyeOutlined,
  ExclamationCircleOutlined,
  TruckOutlined,
  HomeOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface DemandRequest {
  id: string;
  requestId: string;
  customerName: string;
  sourcePlant: string;
  destinationLocation: string;
  productType: string;
  requestedQuantity: number;
  urgencyLevel: 'Low' | 'Medium' | 'High' | 'Critical';
  requestedDeliveryDate: string;
  submittedDate: string;
  submittedBy: string;
  status: 'Pending' | 'Under Review' | 'Approved' | 'Rejected' | 'Partially Approved';
  approvedQuantity?: number;
  approvedBy?: string;
  approvalDate?: string;
  rejectionReason?: string;
  estimatedCost: number;
  availableInventory: number;
  comments?: string;
}

const DemandApproval = () => {
  const [demandRequests, setDemandRequests] = useState<DemandRequest[]>([
    {
      id: 'DR-001',
      requestId: 'REQ-2025-001',
      customerName: 'Ambuja Cement Ltd',
      sourcePlant: 'ACC Jamul Plant',
      destinationLocation: 'Ambuja Dadri Terminal',
      productType: 'OPC Clinker',
      requestedQuantity: 2500,
      urgencyLevel: 'High',
      requestedDeliveryDate: '2025-01-15',
      submittedDate: '2025-01-05',
      submittedBy: 'Regional Sales Manager',
      status: 'Pending',
      estimatedCost: 2125000,
      availableInventory: 25000,
      comments: 'Urgent requirement for ongoing project'
    },
    {
      id: 'DR-002',
      requestId: 'REQ-2025-002',
      customerName: 'Orient Cement',
      sourcePlant: 'Ambuja Ambujanagar Plant',
      destinationLocation: 'Orient Devapur Plant',
      productType: 'PPC Clinker',
      requestedQuantity: 1800,
      urgencyLevel: 'Medium',
      requestedDeliveryDate: '2025-01-20',
      submittedDate: '2025-01-06',
      submittedBy: 'Sales Executive',
      status: 'Under Review',
      estimatedCost: 1170000,
      availableInventory: 35000
    },
    {
      id: 'DR-003',
      requestId: 'REQ-2025-003',
      customerName: 'Penna Cement',
      sourcePlant: 'Orient Devapur Plant',
      destinationLocation: 'Penna Krishnapatnam Terminal',
      productType: 'OPC Clinker',
      requestedQuantity: 3200,
      urgencyLevel: 'Critical',
      requestedDeliveryDate: '2025-01-12',
      submittedDate: '2025-01-07',
      submittedBy: 'Key Account Manager',
      status: 'Approved',
      approvedQuantity: 3200,
      approvedBy: 'Plant Manager',
      approvalDate: '2025-01-08',
      estimatedCost: 2720000,
      availableInventory: 24000,
      comments: 'Critical customer requirement - expedite processing'
    },
    {
      id: 'DR-004',
      requestId: 'REQ-2025-004',
      customerName: 'Sanghi Industries',
      sourcePlant: 'Penna Tandur Plant',
      destinationLocation: 'Sanghi Sanghipuram Plant',
      productType: 'PPC Clinker',
      requestedQuantity: 4500,
      urgencyLevel: 'Low',
      requestedDeliveryDate: '2025-01-25',
      submittedDate: '2025-01-04',
      submittedBy: 'Regional Manager',
      status: 'Partially Approved',
      approvedQuantity: 2800,
      approvedBy: 'Supply Chain Head',
      approvalDate: '2025-01-07',
      estimatedCost: 3825000,
      availableInventory: 14000,
      comments: 'Approved partial quantity due to inventory constraints'
    },
    {
      id: 'DR-005',
      requestId: 'REQ-2025-005',
      customerName: 'ACC Limited',
      sourcePlant: 'Sanghi Sanghipuram Plant',
      destinationLocation: 'ACC Vizag Terminal',
      productType: 'OPC Clinker',
      requestedQuantity: 5000,
      urgencyLevel: 'High',
      requestedDeliveryDate: '2025-01-18',
      submittedDate: '2025-01-08',
      submittedBy: 'Business Head',
      status: 'Rejected',
      rejectionReason: 'Insufficient inventory and production capacity',
      estimatedCost: 4250000,
      availableInventory: 8500
    },
    {
      id: 'DR-006',
      requestId: 'REQ-2025-006',
      customerName: 'Ambuja Cement',
      sourcePlant: 'ACC Wadi Plant',
      destinationLocation: 'Ambuja Tuticorin Terminal',
      productType: 'PPC Clinker',
      requestedQuantity: 3600,
      urgencyLevel: 'Medium',
      requestedDeliveryDate: '2025-01-22',
      submittedDate: '2025-01-09',
      submittedBy: 'Sales Manager',
      status: 'Pending',
      estimatedCost: 3060000,
      availableInventory: 45000
    }
  ]);

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<DemandRequest | null>(null);
  const [actionType, setActionType] = useState<'approve' | 'reject' | 'view'>('view');
  const [form] = Form.useForm();

  const handleViewRequest = (request: DemandRequest) => {
    setSelectedRequest(request);
    setActionType('view');
    setIsModalVisible(true);
  };

  const handleApproveRequest = (request: DemandRequest) => {
    setSelectedRequest(request);
    setActionType('approve');
    form.setFieldsValue({
      approvedQuantity: request.requestedQuantity,
      comments: ''
    });
    setIsModalVisible(true);
  };

  const handleRejectRequest = (request: DemandRequest) => {
    setSelectedRequest(request);
    setActionType('reject');
    form.setFieldsValue({
      rejectionReason: '',
      comments: ''
    });
    setIsModalVisible(true);
  };

  const handleSubmitAction = (values: any) => {
    if (!selectedRequest) return;

    const updatedRequest = { ...selectedRequest };
    
    if (actionType === 'approve') {
      updatedRequest.status = values.approvedQuantity === selectedRequest.requestedQuantity ? 'Approved' : 'Partially Approved';
      updatedRequest.approvedQuantity = values.approvedQuantity;
      updatedRequest.approvedBy = 'Current User';
      updatedRequest.approvalDate = new Date().toISOString().split('T')[0];
      updatedRequest.comments = values.comments;
      message.success(`Request ${updatedRequest.status.toLowerCase()} successfully!`);
    } else if (actionType === 'reject') {
      updatedRequest.status = 'Rejected';
      updatedRequest.rejectionReason = values.rejectionReason;
      updatedRequest.comments = values.comments;
      message.success('Request rejected successfully!');
    }

    setDemandRequests(requests => 
      requests.map(req => req.id === selectedRequest.id ? updatedRequest : req)
    );
    
    setIsModalVisible(false);
    form.resetFields();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Pending': return 'orange';
      case 'Under Review': return 'blue';
      case 'Approved': return 'green';
      case 'Partially Approved': return 'lime';
      case 'Rejected': return 'red';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Pending': return <ClockCircleOutlined />;
      case 'Under Review': return <EyeOutlined />;
      case 'Approved': return <CheckCircleOutlined />;
      case 'Partially Approved': return <CheckCircleOutlined />;
      case 'Rejected': return <CloseCircleOutlined />;
      default: return null;
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'Low': return 'green';
      case 'Medium': return 'orange';
      case 'High': return 'red';
      case 'Critical': return 'magenta';
      default: return 'default';
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
      title: 'Request ID',
      dataIndex: 'requestId',
      key: 'requestId',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'Customer',
      dataIndex: 'customerName',
      key: 'customerName',
      render: (text: string, record: DemandRequest) => (
        <Space direction="vertical" size="small">
          <Text strong>{text}</Text>
          <Text style={{ fontSize: '12px' }}>{record.productType}</Text>
        </Space>
      )
    },
    {
      title: 'Route',
      key: 'route',
      render: (record: DemandRequest) => (
        <Space direction="vertical" size="small">
          <Text><HomeOutlined /> {record.sourcePlant}</Text>
          <Text type="secondary">↓</Text>
          <Text><TruckOutlined /> {record.destinationLocation}</Text>
        </Space>
      )
    },
    {
      title: 'Quantity (MT)',
      key: 'quantity',
      render: (record: DemandRequest) => (
        <Space direction="vertical" size="small">
          <Text strong>Req: {record.requestedQuantity.toLocaleString()}</Text>
          {record.approvedQuantity && (
            <Text style={{ color: '#52c41a' }}>App: {record.approvedQuantity.toLocaleString()}</Text>
          )}
        </Space>
      )
    },
    {
      title: 'Urgency',
      dataIndex: 'urgencyLevel',
      key: 'urgencyLevel',
      render: (urgency: string) => (
        <Tag color={getUrgencyColor(urgency)}>
          {urgency === 'Critical' && <ExclamationCircleOutlined />} {urgency}
        </Tag>
      )
    },
    {
      title: 'Delivery Date',
      dataIndex: 'requestedDeliveryDate',
      key: 'requestedDeliveryDate',
      render: (date: string) => <Text>{date}</Text>
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
      render: (cost: number) => formatCurrency(cost)
    },
    {
      title: 'Inventory',
      key: 'inventory',
      render: (record: DemandRequest) => {
        const availabilityPercent = (record.requestedQuantity / record.availableInventory) * 100;
        return (
          <Space direction="vertical" size="small">
            <Text>{record.availableInventory.toLocaleString()} MT</Text>
            <Progress 
              percent={Math.min(availabilityPercent, 100)} 
              size="small"
              status={availabilityPercent > 80 ? 'exception' : 'normal'}
              showInfo={false}
            />
          </Space>
        );
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: DemandRequest) => (
        <Space>
          <Button 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => handleViewRequest(record)}
          >
            View
          </Button>
          {record.status === 'Pending' && (
            <>
              <Button 
                size="small" 
                type="primary"
                icon={<CheckCircleOutlined />}
                onClick={() => handleApproveRequest(record)}
              >
                Approve
              </Button>
              <Button 
                size="small" 
                danger
                icon={<CloseCircleOutlined />}
                onClick={() => handleRejectRequest(record)}
              >
                Reject
              </Button>
            </>
          )}
        </Space>
      )
    }
  ];

  const totalRequests = demandRequests.length;
  const pendingRequests = demandRequests.filter(r => r.status === 'Pending').length;
  const approvedRequests = demandRequests.filter(r => r.status === 'Approved' || r.status === 'Partially Approved').length;
  const rejectedRequests = demandRequests.filter(r => r.status === 'Rejected').length;
  const totalValue = demandRequests.reduce((sum, r) => sum + r.estimatedCost, 0);

  return (
    <div>
      <Title level={2} style={{ color: '#1f4e79', marginBottom: 24 }}>
        <CheckCircleOutlined /> Demand Approval Dashboard
      </Title>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Requests"
              value={totalRequests}
              prefix={<ClockCircleOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Pending Approval"
              value={pendingRequests}
              prefix={<ExclamationCircleOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Approved"
              value={approvedRequests}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Value"
              value={totalValue}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<TruckOutlined style={{ color: '#1f4e79' }} />}
              valueStyle={{ color: '#1f4e79' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Urgent Requests Alert */}
      {demandRequests.some(r => r.urgencyLevel === 'Critical' && r.status === 'Pending') && (
        <Alert
          message="Critical Requests Pending"
          description="There are critical priority requests awaiting approval. Please review immediately."
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Demand Requests Table */}
      <Card title="Demand Requests">
        <Table
          dataSource={demandRequests}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
          scroll={{ x: 1400, y: 400 }}
          rowClassName={(record) => {
            if (record.urgencyLevel === 'Critical' && record.status === 'Pending') return 'critical-row';
            if (record.status === 'Rejected') return 'rejected-row';
            return '';
          }}
        />
      </Card>

      {/* Action Modal */}
      <Modal
        title={
          actionType === 'view' ? 'Request Details' :
          actionType === 'approve' ? 'Approve Request' : 'Reject Request'
        }
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={actionType === 'view' ? [
          <Button key="close" onClick={() => setIsModalVisible(false)}>
            Close
          </Button>
        ] : null}
        width={800}
      >
        {selectedRequest && (
          <>
            <Descriptions bordered column={2} style={{ marginBottom: 24 }}>
              <Descriptions.Item label="Request ID">{selectedRequest.requestId}</Descriptions.Item>
              <Descriptions.Item label="Customer">{selectedRequest.customerName}</Descriptions.Item>
              <Descriptions.Item label="Product Type">{selectedRequest.productType}</Descriptions.Item>
              <Descriptions.Item label="Urgency">{selectedRequest.urgencyLevel}</Descriptions.Item>
              <Descriptions.Item label="Source Plant">{selectedRequest.sourcePlant}</Descriptions.Item>
              <Descriptions.Item label="Destination">{selectedRequest.destinationLocation}</Descriptions.Item>
              <Descriptions.Item label="Requested Quantity">{selectedRequest.requestedQuantity.toLocaleString()} MT</Descriptions.Item>
              <Descriptions.Item label="Available Inventory">{selectedRequest.availableInventory.toLocaleString()} MT</Descriptions.Item>
              <Descriptions.Item label="Delivery Date">{selectedRequest.requestedDeliveryDate}</Descriptions.Item>
              <Descriptions.Item label="Estimated Cost">{formatCurrency(selectedRequest.estimatedCost)}</Descriptions.Item>
              <Descriptions.Item label="Submitted By">{selectedRequest.submittedBy}</Descriptions.Item>
              <Descriptions.Item label="Submitted Date">{selectedRequest.submittedDate}</Descriptions.Item>
            </Descriptions>

            {actionType !== 'view' && (
              <Form
                form={form}
                layout="vertical"
                onFinish={handleSubmitAction}
              >
                {actionType === 'approve' && (
                  <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="approvedQuantity"
                        label="Approved Quantity (MT)"
                        rules={[{ required: true, message: 'Please enter approved quantity' }]}
                      >
                        <Input 
                          type="number" 
                          max={selectedRequest.requestedQuantity}
                          placeholder="Enter approved quantity"
                        />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="comments"
                        label="Approval Comments"
                      >
                        <TextArea 
                          rows={3} 
                          placeholder="Enter approval comments..."
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                )}

                {actionType === 'reject' && (
                  <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="rejectionReason"
                        label="Rejection Reason"
                        rules={[{ required: true, message: 'Please select rejection reason' }]}
                      >
                        <Select placeholder="Select rejection reason">
                          <Option value="insufficient_inventory">Insufficient Inventory</Option>
                          <Option value="production_capacity">Production Capacity Constraints</Option>
                          <Option value="logistics_unavailable">Logistics Unavailable</Option>
                          <Option value="quality_issues">Quality Issues</Option>
                          <Option value="commercial_terms">Commercial Terms</Option>
                          <Option value="other">Other</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="comments"
                        label="Additional Comments"
                      >
                        <TextArea 
                          rows={3} 
                          placeholder="Enter additional comments..."
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                )}
                
                <Form.Item style={{ textAlign: 'right', marginTop: 24 }}>
                  <Space>
                    <Button onClick={() => setIsModalVisible(false)}>
                      Cancel
                    </Button>
                    <Button 
                      type="primary" 
                      htmlType="submit"
                      danger={actionType === 'reject'}
                    >
                      {actionType === 'approve' ? 'Approve Request' : 'Reject Request'}
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            )}
          </>
        )}
      </Modal>

      <style jsx>{`
        .critical-row {
          background-color: #fff2f0 !important;
          border-left: 4px solid #ff4d4f !important;
        }
        .rejected-row {
          background-color: #f6f6f6 !important;
        }
      `}</style>
    </div>
  );
};

export default DemandApproval;