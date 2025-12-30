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
      name: 'Service Level',
      value: data.service_level * 100,
      fill: '#2e7d32',
    },
    {
      name: 'Demand Fulfillment',
      value: data.demand_fulfillment_rate * 100,
      fill: '#1f4e79',
    },
    {
      name: 'On-Time Delivery',
      value: data.on_time_delivery * 100,
      fill: '#f57c00',
    },
  ];

  const CustomLegend = ({ payload }: { payload?: any[] }) => {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '4px', 
        marginTop: '8px',
        fontSize: '0.85rem'
      }}>
        {payload?.map((entry: any, index: number) => (
          <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div
              style={{
                width: '8px',
                height: '8px',
                backgroundColor: entry.color,
                borderRadius: '2px',
                flexShrink: 0
              }}
            />
            <span style={{ color: '#666', lineHeight: '1.1' }}>
              {entry.value}: {entry.payload.value.toFixed(1)}%
            </span>
          </div>
        ))}
        {data.stockout_triggered && (
          <div style={{ 
            marginTop: '4px', 
            padding: '4px 6px', 
            background: '#fff3e0', 
            borderRadius: '3px',
            border: '1px solid #ffcc02',
            fontSize: '0.75rem'
          }}>
            <span style={{ color: '#f57c00', fontWeight: 600 }}>
              ⚠️ Stockout Event
            </span>
          </div>
        )}
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadialBarChart
        cx="50%"
        cy="50%"
        innerRadius="30%"
        outerRadius="85%"
        data={chartData}
        startAngle={90}
        endAngle={-270}
        margin={{ top: 5, right: 5, bottom: 5, left: 5 }}
      >
        <RadialBar
          dataKey="value"
          cornerRadius={3}
          fill="#8884d8"
          label={false}
          background={false}
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </RadialBar>
        <Legend 
          content={CustomLegend} 
          verticalAlign="bottom"
          align="center"
          wrapperStyle={{ paddingTop: '5px' }}
        />
      </RadialBarChart>
    </ResponsiveContainer>
  );
};

export default ServiceMetricsChart;