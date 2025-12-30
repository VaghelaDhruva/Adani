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
        background: 'linear-gradient(180deg, #1f4e79 0%, #1565c0 35%, #42a5f5 70%, #64b5f6 100%)',
        boxShadow: '4px 0 16px rgba(31, 78, 121, 0.25)',
        borderRight: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      <div
        style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '1.3rem',
          fontWeight: 'bold',
          borderBottom: '1px solid rgba(255, 255, 255, 0.15)',
          marginBottom: 16,
          textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
          background: 'rgba(255, 255, 255, 0.05)',
        }}
      >
        Adani
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