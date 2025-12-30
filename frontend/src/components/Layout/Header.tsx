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
        background: 'rgba(255, 255, 255, 0.95)',
        padding: '0 24px',
        boxShadow: '0 4px 12px rgba(31, 78, 121, 0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(31, 78, 121, 0.15)',
        height: 64,
      }}
    >
      <div
  style={{
    flex: 1,
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    paddingTop: 6,      // <-- prevents clipping
  }}
>
  <Typography.Title
    level={4}
    style={{
      margin: 0,         // <-- overrides antd default
      color: "#1f4e79",
      fontWeight: 700,
      textShadow: "0 1px 2px rgba(31, 78, 121, 0.1)",
      fontSize: "1.4rem",
      lineHeight: 1.25,  // <-- slightly taller line box
    }}
  >
   Clinker Supply Chain Optimization Platform
  </Typography.Title>

  <Text
    type="secondary"
    style={{
      fontSize: "0.9rem",
      color: "#2d3748",
      fontWeight: 500,
      marginTop: 2,
    }}
  >
    Production-ready optimization with validated data pipeline
  </Text>
</div>

      <Space size="large" style={{ flexShrink: 0 }}>
        {/* System Status */}
        <Space>
          <Badge
            color={getStatusColor(systemHealth?.status)}
            text={
              <Text style={{ fontSize: '0.9rem', color: '#2d3748', fontWeight: 500 }}>
                System: {systemHealth?.status || 'Unknown'}
              </Text>
            }
          />
          <Button
            type="text"
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            size="small"
            style={{ color: '#1f4e79' }}
          />
        </Space>

        {/* Optimization Status */}
        <Space>
          <Badge
            color={getStatusColor(systemHealth?.optimization_ready ? 'ready' : 'blocked')}
            text={
              <Text style={{ fontSize: '0.9rem', color: '#2d3748', fontWeight: 500 }}>
                Optimization: {systemHealth?.optimization_ready ? 'Ready' : 'Blocked'}
              </Text>
            }
          />
        </Space>

        {/* Notifications */}
        <Badge count={systemHealth?.alerts?.length || 0} size="small">
          <Button 
            type="text" 
            icon={<BellOutlined />} 
            style={{ color: '#1f4e79' }}
          />
        </Badge>

        {/* User */}
        <Button 
          type="text" 
          icon={<UserOutlined />}
          style={{ color: '#1f4e79', fontWeight: 500 }}
        >
          Admin
        </Button>
      </Space>
    </AntHeader>
  );
};

export default Header;