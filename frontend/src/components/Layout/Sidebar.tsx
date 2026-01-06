import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  CarOutlined,
  ShoppingCartOutlined,
  InboxOutlined,
  TruckOutlined,
  LoadingOutlined,
  EnvironmentOutlined,
  CheckSquareOutlined,
  DollarOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';

const { Sider } = Layout;

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: 'core',
      label: 'Core Dashboards',
      type: 'group' as const,
    },
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'KPI Dashboard',
    },
    {
      key: '/transport',
      icon: <CarOutlined />,
      label: 'Transport Mode Selection',
    },
    {
      key: 'workflow',
      label: 'Clinker Workflow',
      type: 'group' as const,
    },
    {
      key: '/clinker/orders',
      icon: <ShoppingCartOutlined />,
      label: 'Order & Demand Creation',
    },
    {
      key: '/clinker/approval',
      icon: <CheckCircleOutlined />,
      label: 'Demand Approval',
    },
    {
      key: '/clinker/inventory',
      icon: <InboxOutlined />,
      label: 'Inventory & Availability',
    },
    {
      key: '/clinker/dispatch',
      icon: <TruckOutlined />,
      label: 'Dispatch Planning',
    },
    {
      key: '/clinker/loading',
      icon: <LoadingOutlined />,
      label: 'Loading & Dispatch',
    },
    {
      key: '/clinker/tracking',
      icon: <EnvironmentOutlined />,
      label: 'In-Transit Tracking',
    },
    {
      key: '/clinker/delivery',
      icon: <CheckSquareOutlined />,
      label: 'Delivery & GRN',
    },
    {
      key: '/clinker/billing',
      icon: <DollarOutlined />,
      label: 'Billing & Costing',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <Sider
      width={280}
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
        Clinker System
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