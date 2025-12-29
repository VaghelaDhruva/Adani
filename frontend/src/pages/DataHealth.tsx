import React from 'react';
import { Row, Col, Card, Table, Tag, Statistic, Alert, Typography, Space, Button } from 'antd';
import { useQuery } from 'react-query';
import { 
  CheckCircleOutlined, 
  WarningOutlined, 
  CloseCircleOutlined,
  ReloadOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import { fetchDataHealth } from '../services/api';

const { Title, Text } = Typography;

const DataHealth = () => {
  const { 
    data: healthData, 
    isLoading, 
    error,
    refetch 
  } = useQuery(
    'data-health',
    fetchDataHealth,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'pass':
        return <CheckCircleOutlined style={{ color: '#2e7d32' }} />;
      case 'warning':
      case 'warn':
        return <WarningOutlined style={{ color: '#f57c00' }} />;
      case 'error':
      case 'fail':
        return <CloseCircleOutlined style={{ color: '#d32f2f' }} />;
      default:
        return <DatabaseOutlined style={{ color: '#666' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'pass':
        return 'success';
      case 'warning':
      case 'warn':
        return 'warning';
      case 'error':
      case 'fail':
        return 'error';
      default:
        return 'default';
    }
  };

  const tableColumns = [
    {
      title: 'Table Name',
      dataIndex: 'table_name',
      key: 'table_name',
      render: (name: string) => (
        <Text strong style={{ color: '#1f4e79' }}>
          {name.replace('_', ' ').toUpperCase()}
        </Text>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      align: 'center' as const,
      render: (status: string) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Records',
      dataIndex: 'record_count',
      key: 'record_count',
      align: 'right' as const,
      render: (count: number) => (
        <Text strong>{count.toLocaleString()}</Text>
      ),
    },
    {
      title: 'Last Updated',
      dataIndex: 'last_updated',
      key: 'last_updated',
      render: (date: string) => (
        <Text type="secondary">
          {date ? new Date(date).toLocaleString() : 'Never'}
        </Text>
      ),
    },
    {
      title: 'Issues',
      dataIndex: 'issues',
      key: 'issues',
      render: (issues: string[]) => (
        <div>
          {issues && issues.length > 0 ? (
            <Space direction="vertical" size="small">
              {issues.slice(0, 2).map((issue, index) => (
                <Tag key={index} color="red" style={{ fontSize: '0.8rem' }}>
                  {issue}
                </Tag>
              ))}
              {issues.length > 2 && (
                <Text type="secondary" style={{ fontSize: '0.8rem' }}>
                  +{issues.length - 2} more
                </Text>
              )}
            </Space>
          ) : (
            <Tag color="green" style={{ fontSize: '0.8rem' }}>
              No issues
            </Tag>
          )}
        </div>
      ),
    },
  ];

  if (error) {
    return (
      <Alert
        message="Error Loading Data Health"
        description="Failed to load data health status. Please check your connection and try again."
        type="error"
        showIcon
        action={
          <Button onClick={() => refetch()} icon={<ReloadOutlined />}>
            Retry
          </Button>
        }
      />
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Space direction="vertical" size="small">
          <Title level={2} style={{ margin: 0, color: '#1f4e79' }}>
            Data Health Status
          </Title>
          <Text type="secondary">
            Comprehensive monitoring of data quality across all tables
          </Text>
        </Space>
        
        <div style={{ marginTop: 16 }}>
          <Button 
            onClick={() => refetch()} 
            icon={<ReloadOutlined />}
            loading={isLoading}
          >
            Refresh Status
          </Button>
        </div>
      </div>

      {/* Overall Status */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="metric-card">
            <Statistic
              title="Overall Status"
              value={healthData?.overall_status || 'Unknown'}
              prefix={getStatusIcon(healthData?.overall_status || '')}
              valueStyle={{ 
                color: healthData?.overall_status === 'healthy' ? '#2e7d32' : 
                       healthData?.overall_status === 'warning' ? '#f57c00' : '#d32f2f'
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="metric-card">
            <Statistic
              title="Optimization Ready"
              value={healthData?.optimization_ready ? 'YES' : 'NO'}
              prefix={healthData?.optimization_ready ? 
                <CheckCircleOutlined style={{ color: '#2e7d32' }} /> :
                <CloseCircleOutlined style={{ color: '#d32f2f' }} />
              }
              valueStyle={{ 
                color: healthData?.optimization_ready ? '#2e7d32' : '#d32f2f'
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="metric-card">
            <Statistic
              title="Total Errors"
              value={healthData?.validation_summary?.total_errors || 0}
              prefix={<CloseCircleOutlined style={{ color: '#d32f2f' }} />}
              valueStyle={{ color: '#d32f2f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="metric-card">
            <Statistic
              title="Warnings"
              value={healthData?.validation_summary?.total_warnings || 0}
              prefix={<WarningOutlined style={{ color: '#f57c00' }} />}
              valueStyle={{ color: '#f57c00' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Optimization Readiness Alert */}
      {!healthData?.optimization_ready && (
        <Alert
          message="Optimization Blocked"
          description={`${healthData?.validation_summary?.blocking_errors || 0} critical errors are preventing optimization execution. Please resolve data quality issues before running optimization.`}
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Table Status */}
      <Card title="Table Status Details" style={{ marginBottom: 24 }}>
        <Table
          dataSource={healthData?.tables || []}
          columns={tableColumns}
          loading={isLoading}
          pagination={false}
          rowKey="table_name"
          className="data-table"
          size="middle"
        />
      </Card>

      {/* Data Freshness */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Data Freshness" style={{ height: '100%' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {healthData?.tables?.map(table => (
                <div key={table.table_name} style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 0',
                  borderBottom: '1px solid #f0f0f0'
                }}>
                  <Text>{table.table_name.replace('_', ' ')}</Text>
                  <Text type="secondary" style={{ fontSize: '0.9rem' }}>
                    {table.last_updated ? 
                      new Date(table.last_updated).toLocaleDateString() : 
                      'No data'
                    }
                  </Text>
                </div>
              ))}
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Critical Metrics" style={{ height: '100%' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 0'
              }}>
                <Text>Total Records</Text>
                <Text strong>
                  {healthData?.tables?.reduce((sum, table) => sum + table.record_count, 0).toLocaleString() || 0}
                </Text>
              </div>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 0'
              }}>
                <Text>Tables with Issues</Text>
                <Text strong style={{ color: '#d32f2f' }}>
                  {healthData?.tables?.filter(table => table.issues && table.issues.length > 0).length || 0}
                </Text>
              </div>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 0'
              }}>
                <Text>Healthy Tables</Text>
                <Text strong style={{ color: '#2e7d32' }}>
                  {healthData?.tables?.filter(table => table.status === 'healthy').length || 0}
                </Text>
              </div>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 0'
              }}>
                <Text>Blocking Errors</Text>
                <Text strong style={{ color: '#d32f2f' }}>
                  {healthData?.validation_summary?.blocking_errors || 0}
                </Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DataHealth;