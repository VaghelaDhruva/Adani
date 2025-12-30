import React from 'react';
import { Table, Tag, Progress } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';

interface TransportUtilizationData {
  from: string;
  to: string;
  mode: string;
  trips: number;
  capacity_used_pct: number;
  sbq_compliance: string;
  violations: number;
}

interface Props {
  data?: TransportUtilizationData[];
}

const TransportUtilizationTable = ({ data }: Props) => {
  if (!data || data.length === 0) {
    return <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>No data available</div>;
  }

  const columns: ColumnsType<TransportUtilizationData> = [
    {
      title: 'Route',
      key: 'route',
      width: 280,
      render: (_, record: TransportUtilizationData) => (
        <div>
          <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#1f4e79' }}>
            {record.from} → {record.to}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>
            {record.mode.toUpperCase()}
          </div>
        </div>
      ),
    },
    {
      title: 'Trips',
      dataIndex: 'trips',
      key: 'trips',
      width: 100,
      align: 'center',
      render: (trips: number) => (
        <span style={{ fontWeight: 600 }}>{trips}</span>
      ),
    },
    {
      title: 'Capacity Used',
      key: 'capacity',
      width: 160,
      align: 'center',
      render: (_, record: TransportUtilizationData) => (
        <div style={{ width: '100%' }}>
          <Progress
            percent={record.capacity_used_pct * 100}
            size="small"
            strokeColor={
              record.capacity_used_pct > 0.9 ? '#d32f2f' :
              record.capacity_used_pct > 0.7 ? '#f57c00' : '#2e7d32'
            }
            format={(percent?: number) => `${percent?.toFixed(0)}%`}
          />
        </div>
      ),
    },
    {
      title: 'SBQ Compliance',
      key: 'compliance',
      width: 160,
      align: 'center',
      render: (_, record: TransportUtilizationData) => (
        <div>
          <Tag
            color={record.sbq_compliance === 'Yes' ? 'green' : 'red'}
            icon={record.sbq_compliance === 'Yes' ? <CheckCircleOutlined /> : <WarningOutlined />}
          >
            {record.sbq_compliance}
          </Tag>
          {record.violations > 0 && (
            <div style={{ fontSize: '0.8rem', color: '#d32f2f', marginTop: '4px' }}>
              {record.violations} violations
            </div>
          )}
        </div>
      ),
    },
  ];

  return (
    <Table<TransportUtilizationData>
      dataSource={data}
      columns={columns}
      pagination={false}
      size="small"
      rowKey={(record) => `${record.from}-${record.to}-${record.mode}`}
      className="data-table transport-utilization-table"
      style={{ fontSize: '0.9rem' }}
      scroll={{ x: 700 }}
    />
  );
};

export default TransportUtilizationTable;