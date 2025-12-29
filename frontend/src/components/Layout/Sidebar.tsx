import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  CheckCircleOutlined,
  PlayCircleOutlined,
  BarChartOutlined,
  SwapOutlined,
  SettingOutlined,
  HeartOutlined
} from '@ant-design/icons';

const { Sider } = Layout;

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'KPI Dashboard',
    },
    {
      key: '/data-health',
      icon: <HeartOutlined />,
      label: 'Data Health',
    },
    {
      key: '/data-validation',
      icon: <CheckCircleOutlined />,
      label: 'Data Validation',
    },
    {
      key: '/optimization',
      icon: <PlayCircleOutlined />,
      label: 'Optimization Console',
    },
    {
      key: '/results',
      icon: <BarChartOutlined />,
      label: 'Results Dashboard',
    },
    {
      key: '/scenarios',
      icon: <SwapOutlined />,
      label: 'Scenario Comparison',
    },
    {
      key: '/system',
      icon: <SettingOutlined />,
      label: 'System Health',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <Sider
      width={250}
      style={{
        background: 'linear-gradient(180deg, #1f4e79 0%, #2e7d32 100%)',
        boxShadow: '2px 0 8px rgba(0,0,0,0.15)',
      }}
    >
      <div
        style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '1.2rem',
          fontWeight: 'bold',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          marginBottom: 16,
        }}
      >
        🏭 Clinker SCO
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{
          background: 'transparent',
          border: 'none',
        }}
        theme="dark"
      />
    </Sider>
  );
};

export default Sidebar;