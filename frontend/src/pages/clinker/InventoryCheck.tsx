import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Row, 
  Col, 
  Typography, 
  Tag, 
  Progress, 
  Alert,
  Space,
  Button,
  Input,
  Select
} from 'antd';
import { 
  InboxOutlined, 
  WarningOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  SearchOutlined,
  ReloadOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

interface InventoryData {
  plantId: string;
  plantName: string;
  currentStock: number;
  safetyStock: number;
  maxCapacity: number;
  lastUpdated: string;
  status: 'Good' | 'Low' | 'Critical';
  plannedProduction: number;
  reservedStock: number;
  availableStock: number;
}

const InventoryCheck = () => {
  const [inventoryData, setInventoryData] = useState<InventoryData[]>([
    {
      plantId: 'IU_01',
      plantName: 'ACC Jamul Plant',
      currentStock: 25000,
      safetyStock: 6000,
      maxCapacity: 90000,
      lastUpdated: '2025-01-06 14:30',
      status: 'Good',
      plannedProduction: 15000,
      reservedStock: 7500,
      availableStock: 19000
    },
    {
      plantId: 'IU_02',
      plantName: 'ACC Kymore Plant',
      currentStock: 18000,
      safetyStock: 8000,
      maxCapacity: 65000,
      lastUpdated: '2025-01-06 14:25',
      status: 'Good',
      plannedProduction: 15000,
      reservedStock: 5400,
      availableStock: 10000
    },
    {
      plantId: 'IU_03',
      plantName: 'ACC Chanda Plant',
      currentStock: 20000,
      safetyStock: 5000,
      maxCapacity: 80000,
      lastUpdated: '2025-01-06 14:20',
      status: 'Good',
      plannedProduction: 15000,
      reservedStock: 6000,
      availableStock: 15000
    },
    {
      plantId: 'IU_04',
      plantName: 'ACC Wadi Plant',
      currentStock: 45000,
      safetyStock: 16000,
      maxCapacity: 150000,
      lastUpdated: '2025-01-06 14:35',
      status: 'Good',
      plannedProduction: 15000,
      reservedStock: 13500,
      availableStock: 29000
    },
    {
      plantId: 'IU_12',
      plantName: 'Ambuja Ambujanagar Plant',
      currentStock: 35000,
      safetyStock: 12000,
      maxCapacity: 130000,
      lastUpdated: '2025-01-06 14:15',
      status: 'Good',
      plannedProduction: 15000,
      reservedStock: 10500,
      availableStock: 23000
    },
    {
      plantId: 'IU_18',
      plantName: 'Sanghi Sanghipuram Plant',
      currentStock: 55000,
      safetyStock: 16000,
      maxCapacity: 180000,
      lastUpdated: '2025-01-06 14:10',
      status: 'Good',
      plannedProduction: 15000,
      reservedStock: 16500,
      availableStock: 39000
    },
    {
      plantId: 'GU_01',
      plantName: 'ACC Tikaria Terminal',
      currentStock: 5000,
      safetyStock: 9000,
      maxCapacity: 45000,
      lastUpdated: '2025-01-06 14:05',
      status: 'Critical',
      plannedProduction: 0,
      reservedStock: 1500,
      availableStock: 0
    },
    {
      plantId: 'GU_06',
      plantName: 'Ambuja Dadri Terminal',
      currentStock: 4500,
      safetyStock: 8400,
      maxCapacity: 42000,
      lastUpdated: '2025-01-06 14:00',
      status: 'Critical',
      plannedProduction: 0,
      reservedStock: 1350,
      availableStock: 0
    },
    {
      plantId: 'GU_10',
      plantName: 'Ambuja Sankrail Terminal',
      currentStock: 5500,
      safetyStock: 9600,
      maxCapacity: 48000,
      lastUpdated: '2025-01-06 13:55',
      status: 'Critical',
      plannedProduction: 0,
      reservedStock: 1650,
      availableStock: 0
    },
    {
      plantId: 'IU_19',
      plantName: 'Penna Talaricheruvu Plant',
      currentStock: 26000,
      safetyStock: 10000,
      maxCapacity: 100000,
      lastUpdated: '2025-01-06 13:50',
      status: 'Good',
      plannedProduction: 15000,
      reservedStock: 7800,
      availableStock: 16000
    }
  ]);

  const [filteredData, setFilteredData] = useState<InventoryData[]>(inventoryData);
  const [selectedPlant, setSelectedPlant] = useState<string>('all');

  useEffect(() => {
    let filtered = inventoryData;
    if (selectedPlant !== 'all') {
      filtered = inventoryData.filter(item => item.plantId === selectedPlant);
    }
    setFilteredData(filtered);
  }, [selectedPlant, inventoryData]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Good': return 'green';
      case 'Low': return 'orange';
      case 'Critical': return 'red';
      default: return 'default';
    }
  };

  const getStockLevel = (current: number, safety: number, max: number) => {
    const percentage = (current / max) * 100;
    let status: 'success' | 'normal' | 'exception' = 'success';
    
    if (current <= safety) {
      status = 'exception';
    } else if (current <= safety * 1.5) {
      status = 'normal';
    }
    
    return { percentage, status };
  };

  const columns = [
    {
      title: 'Plant',
      dataIndex: 'plantName',
      key: 'plantName',
      render: (text: string, record: InventoryData) => (
        <Space direction="vertical" size="small">
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>{record.plantId}</Text>
        </Space>
      )
    },
    {
      title: 'Current Stock',
      dataIndex: 'currentStock',
      key: 'currentStock',
      render: (value: number, record: InventoryData) => {
        const { percentage, status } = getStockLevel(value, record.safetyStock, record.maxCapacity);
        return (
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text strong>{value.toLocaleString()} MT</Text>
            <Progress 
              percent={percentage} 
              status={status}
              size="small"
              showInfo={false}
            />
          </Space>
        );
      }
    },
    {
      title: 'Available Stock',
      dataIndex: 'availableStock',
      key: 'availableStock',
      render: (value: number) => (
        <Text strong style={{ color: value > 1000 ? '#52c41a' : '#faad14' }}>
          {value.toLocaleString()} MT
        </Text>
      )
    },
    {
      title: 'Reserved',
      dataIndex: 'reservedStock',
      key: 'reservedStock',
      render: (value: number) => `${value.toLocaleString()} MT`
    },
    {
      title: 'Safety Stock',
      dataIndex: 'safetyStock',
      key: 'safetyStock',
      render: (value: number) => `${value.toLocaleString()} MT`
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)} icon={
          status === 'Good' ? <CheckCircleOutlined /> :
          status === 'Low' ? <WarningOutlined /> :
          <ExclamationCircleOutlined />
        }>
          {status}
        </Tag>
      )
    },
    {
      title: 'Last Updated',
      dataIndex: 'lastUpdated',
      key: 'lastUpdated',
      render: (text: string) => (
        <Text type="secondary" style={{ fontSize: '12px' }}>{text}</Text>
      )
    }
  ];

  const totalStock = inventoryData.reduce((sum, item) => sum + item.currentStock, 0);
  const totalAvailable = inventoryData.reduce((sum, item) => sum + item.availableStock, 0);
  const criticalPlants = inventoryData.filter(item => item.status === 'Critical').length;
  const lowStockPlants = inventoryData.filter(item => item.status === 'Low').length;

  return (
    <div>
      <Title level={2} style={{ color: '#1f4e79', marginBottom: 24 }}>
        <InboxOutlined /> Inventory & Availability Check
      </Title>

      {/* Alerts */}
      {criticalPlants > 0 && (
        <Alert
          message="Critical Stock Alert"
          description={`${criticalPlants} plant(s) have critical stock levels. Immediate action required.`}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      
      {lowStockPlants > 0 && (
        <Alert
          message="Low Stock Warning"
          description={`${lowStockPlants} plant(s) have low stock levels. Consider replenishment.`}
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
                {totalStock.toLocaleString()}
              </Title>
              <Text type="secondary">Total Stock (MT)</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#52c41a', margin: 0 }}>
                {totalAvailable.toLocaleString()}
              </Title>
              <Text type="secondary">Available (MT)</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#faad14', margin: 0 }}>
                {lowStockPlants}
              </Title>
              <Text type="secondary">Low Stock Plants</Text>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: '#f5222d', margin: 0 }}>
                {criticalPlants}
              </Title>
              <Text type="secondary">Critical Plants</Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Filters and Controls */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8}>
            <Select
              value={selectedPlant}
              onChange={setSelectedPlant}
              style={{ width: '100%' }}
              placeholder="Filter by plant"
            >
              <Option value="all">All Plants</Option>
              {inventoryData.map(item => (
                <Option key={item.plantId} value={item.plantId}>
                  {item.plantName}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={8}>
            <Search
              placeholder="Search plants..."
              allowClear
              onSearch={(value) => {
                if (!value) {
                  setFilteredData(inventoryData);
                } else {
                  const filtered = inventoryData.filter(item =>
                    item.plantName.toLowerCase().includes(value.toLowerCase())
                  );
                  setFilteredData(filtered);
                }
              }}
            />
          </Col>
          <Col xs={24} sm={8}>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => {
                // Simulate data refresh
                setInventoryData([...inventoryData]);
              }}
            >
              Refresh Data
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Inventory Table */}
      <Card title="Plant-wise Inventory Status" extra={<Text>Last updated: {new Date().toLocaleString()}</Text>}>
        <Table
          dataSource={filteredData}
          columns={columns}
          rowKey="plantId"
          pagination={false}
          size="middle"
          rowClassName={(record) => {
            if (record.status === 'Critical') return 'critical-row';
            if (record.status === 'Low') return 'low-stock-row';
            return '';
          }}
        />
      </Card>

      <style jsx>{`
        .critical-row {
          background-color: #fff2f0 !important;
        }
        .low-stock-row {
          background-color: #fffbe6 !important;
        }
      `}</style>
    </div>
  );
};

export default InventoryCheck;