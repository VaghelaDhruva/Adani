import React from 'react';
import { RadialBarChart, RadialBar, ResponsiveContainer, Legend, Cell } from 'recharts';

interface ServiceMetricsData {
  demand_fulfillment_rate: number;
  on_time_delivery: number;
  service_level: number;
  stockout_triggered: boolean;
}

interface Props {
  data?: ServiceMetricsData;
}

interface ChartDataItem {
  name: string;
  value: number;
  fill: string;
}

const ServiceMetricsChart = ({ data }: Props) => {
  if (!data) {
    return <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>No data available</div>;
  }

  const chartData: ChartDataItem[] = [
    {
      name: 'Demand Fulfillment',
      value: data.demand_fulfillment_rate * 100,
      fill: '#2e7d32',
    },
    {
      name: 'On-Time Delivery',
      value: data.on_time_delivery * 100,
      fill: '#1f4e79',
    },
    {
      name: 'Service Level',
      value: data.service_level * 100,
      fill: '#f57c00',
    },
  ];

  const CustomLegend = ({ payload }: { payload?: any[] }) => {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '16px' }}>
        {payload?.map((entry: any, index: number) => (
          <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div
              style={{
                width: '12px',
                height: '12px',
                backgroundColor: entry.color,
                borderRadius: '2px',
              }}
            />
            <span style={{ fontSize: '0.9rem', color: '#666' }}>
              {entry.value}: {entry.payload.value.toFixed(1)}%
            </span>
          </div>
        ))}
        {data.stockout_triggered && (
          <div style={{ 
            marginTop: '8px', 
            padding: '8px', 
            background: '#fff3e0', 
            borderRadius: '4px',
            border: '1px solid #ffcc02'
          }}>
            <span style={{ fontSize: '0.9rem', color: '#f57c00', fontWeight: 600 }}>
              ⚠️ Stockout Event Detected
            </span>
          </div>
        )}
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadialBarChart
        cx="50%"
        cy="50%"
        innerRadius="20%"
        outerRadius="80%"
        data={chartData}
        startAngle={90}
        endAngle={-270}
      >
        <RadialBar
          dataKey="value"
          cornerRadius={4}
          fill="#8884d8"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </RadialBar>
        <Legend content={CustomLegend} />
      </RadialBarChart>
    </ResponsiveContainer>
  );
};

export default ServiceMetricsChart;