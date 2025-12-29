import React from 'react';
import { Layout, Typography, Space, Badge, Button } from 'antd';
import { BellOutlined, UserOutlined, ReloadOutlined } from '@ant-design/icons';
import { useQuery } from 'react-query';
import { fetchSystemHealth } from '../../services/api';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

const Header = () => {
  const { data: systemHealth, refetch } = useQuery(
    'systemHealth',
    fetchSystemHealth,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'ready':
        return '#52c41a';
      case 'warning':
        return '#faad14';
      case 'error':
      case 'blocked':
        return '#ff4d4f';
      default:
        return '#d9d9d9';
    }
  };

  return (
    <AntHeader
      style={{
        background: 'white',
        padding: '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <div>
        <Typography.Title level={4} style={{ margin: 0, color: '#1f4e79' }}>
          Supply Chain Optimization Platform
        </Typography.Title>
        <Text type="secondary" style={{ fontSize: '0.9rem' }}>
          Production-ready optimization with validated data pipeline
        </Text>
      </div>

      <Space size="large">
        {/* System Status */}
        <Space>
          <Badge
            color={getStatusColor(systemHealth?.status)}
            text={
              <Text style={{ fontSize: '0.9rem' }}>
                System: {systemHealth?.status || 'Unknown'}
              </Text>
            }
          />
          <Button
            type="text"
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            size="small"
          />
        </Space>

        {/* Optimization Status */}
        <Space>
          <Badge
            color={getStatusColor(systemHealth?.optimization_ready ? 'ready' : 'blocked')}
            text={
              <Text style={{ fontSize: '0.9rem' }}>
                Optimization: {systemHealth?.optimization_ready ? 'Ready' : 'Blocked'}
              </Text>
            }
          />
        </Space>

        {/* Notifications */}
        <Badge count={systemHealth?.alerts?.length || 0} size="small">
          <Button type="text" icon={<BellOutlined />} />
        </Badge>

        {/* User */}
        <Button type="text" icon={<UserOutlined />}>
          Admin
        </Button>
      </Space>
    </AntHeader>
  );
};

export default Header;