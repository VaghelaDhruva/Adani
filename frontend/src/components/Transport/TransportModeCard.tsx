import React from 'react';
import { Card, Badge, Tooltip, Space, Typography, Alert } from 'antd';
import { TransportMode } from '../../types/transport';
import { 
  Truck, 
  Train, 
  Ship, 
  Plane, 
  Clock, 
  IndianRupee, 
  Weight, 
  Package,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Leaf
} from 'lucide-react';

const { Text, Title } = Typography;

interface TransportModeCardProps {
  mode: TransportMode;
  isSelected: boolean;
  isAvailable: boolean;
  onSelect: () => void;
  violations?: Array<{
    severity: 'error' | 'warning' | 'info';
    message: string;
  }>;
}

const TransportModeCard: React.FC<TransportModeCardProps> = ({
  mode,
  isSelected,
  isAvailable,
  onSelect,
  violations = []
}) => {
  const getModeIcon = (modeId: string) => {
    switch (modeId) {
      case 'road': return <Truck size={32} />;
      case 'rail': return <Train size={32} />;
      case 'sea': return <Ship size={32} />;
      case 'air': return <Plane size={32} />;
      default: return <Package size={32} />;
    }
  };

  const getReliabilityColor = (reliability: number) => {
    if (reliability >= 0.9) return '#52c41a';
    if (reliability >= 0.8) return '#faad14';
    return '#ff4d4f';
  };

  const getCarbonFootprintColor = (footprint: number) => {
    if (footprint <= 0.05) return '#52c41a';
    if (footprint <= 0.2) return '#faad14';
    return '#ff4d4f';
  };

  return (
    <Card
      hoverable={!isSelected && isAvailable}
      className={`transport-mode-card ${isSelected ? 'selected' : ''} ${!isAvailable ? 'disabled' : ''}`}
      onClick={isAvailable && !isSelected ? onSelect : undefined}
      style={{
        height: '100%',
        border: isSelected ? '2px solid #1890ff' : undefined,
        opacity: isAvailable ? 1 : 0.6,
        cursor: isAvailable && !isSelected ? 'pointer' : 'default',
        position: 'relative',
        overflow: 'visible'
      }}
      bodyStyle={{ padding: '16px' }}
    >
      {/* Status Badge */}
      <div style={{ position: 'absolute', top: '8px', right: '8px' }}>
        {isSelected && (
          <Badge status="success" text="Selected" />
        )}
        {!isAvailable && (
          <Badge status="error" text="Unavailable" />
        )}
      </div>

      {/* Mode Header */}
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ color: isSelected ? '#1890ff' : '#666' }}>
            {getModeIcon(mode.id)}
          </div>
          <div style={{ flex: 1 }}>
            <Title level={5} style={{ margin: 0, color: isSelected ? '#1890ff' : '#262626' }}>
              {mode.name}
            </Title>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {mode.description}
            </Text>
          </div>
        </div>

        {/* Key Metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '8px' }}>
          <Tooltip title={`Cost per ton-km: ₹${mode.costPerTonKm}`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <IndianRupee size={14} color="#666" />
              <Text style={{ fontSize: '12px' }}>₹{mode.costPerTonKm}/t-km</Text>
            </div>
          </Tooltip>

          <Tooltip title={`Average speed: ${mode.avgSpeed} km/h`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={14} color="#666" />
              <Text style={{ fontSize: '12px' }}>{mode.avgSpeed} km/h</Text>
            </div>
          </Tooltip>

          <Tooltip title={`Capacity: ${mode.minVolume}-${mode.maxVolume} tonnes`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Package size={14} color="#666" />
              <Text style={{ fontSize: '12px' }}>{mode.minVolume}-{mode.maxVolume}t</Text>
            </div>
          </Tooltip>

          <Tooltip title={`Max weight: ${mode.maxWeight} tonnes`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Weight size={14} color="#666" />
              <Text style={{ fontSize: '12px' }}>Max {mode.maxWeight}t</Text>
            </div>
          </Tooltip>
        </div>

        {/* Additional Metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '8px' }}>
          <Tooltip title={`Carbon footprint: ${mode.carbonFootprint} kg CO₂ per tonne-km`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Leaf size={14} color="#666" />
              <Text style={{ fontSize: '12px' }}>{mode.carbonFootprint} kg/t-km</Text>
            </div>
          </Tooltip>

          <Tooltip title={`Reliability: ${(mode.reliability * 100).toFixed(0)}%`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle size={14} color="#666" />
              <Text style={{ fontSize: '12px' }}>{(mode.reliability * 100).toFixed(0)}%</Text>
            </div>
          </Tooltip>
        </div>

        {/* Reliability and Environmental Impact */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
          <div>
            <Text style={{ fontSize: '12px', color: '#666' }}>Reliability: </Text>
            <Badge 
              color={getReliabilityColor(mode.reliability)} 
              text={`${(mode.reliability * 100).toFixed(0)}%`}
              style={{ fontSize: '12px' }}
            />
          </div>
          <div>
            <Text style={{ fontSize: '12px', color: '#666' }}>Carbon: </Text>
            <Badge 
              color={getCarbonFootprintColor(mode.carbonFootprint)} 
              text={`${mode.carbonFootprint.toFixed(2)} kg/t-km`}
              style={{ fontSize: '12px' }}
            />
          </div>
        </div>

        {/* Special Requirements */}
        <div style={{ marginTop: '8px' }}>
          <Space wrap>
            {mode.specialHandling && (
              <Badge color="orange" text="Special Handling" style={{ fontSize: '10px' }} />
            )}
            {mode.weatherDependent && (
              <Badge color="blue" text="Weather Dependent" style={{ fontSize: '10px' }} />
            )}
            {mode.infrastructureRequired.length > 0 && (
              <Tooltip title={mode.infrastructureRequired.join(', ')}>
                <Badge color="purple" text={`${mode.infrastructureRequired.length} infra requirements`} style={{ fontSize: '10px' }} />
              </Tooltip>
            )}
          </Space>
        </div>

        {/* Industry-specific Notes */}
        {mode.notes && (
          <div style={{ marginTop: '8px' }}>
            <Alert
              message="Industry Note"
              description={mode.notes}
              type="info"
              showIcon
              style={{ fontSize: '11px' }}
            />
          </div>
        )}

        {/* Violations */}
        {violations.length > 0 && (
          <div style={{ marginTop: '8px' }}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              {violations.map((violation, index) => (
                <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {violation.severity === 'error' && <XCircle size={12} color="#ff4d4f" />}
                  {violation.severity === 'warning' && <AlertTriangle size={12} color="#faad14" />}
                  {violation.severity === 'info' && <CheckCircle size={12} color="#1890ff" />}
                  <Text style={{ fontSize: '11px', color: violation.severity === 'error' ? '#ff4d4f' : '#faad14' }}>
                    {violation.message}
                  </Text>
                </div>
              ))}
            </Space>
          </div>
        )}
      </Space>

      <style jsx>{`
        .transport-mode-card {
          transition: all 0.3s ease;
        }
        
        .transport-mode-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .transport-mode-card.selected {
          background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%);
        }
        
        .transport-mode-card.disabled {
          background: #f5f5f5;
        }
      `}</style>
    </Card>
  );
};

export default TransportModeCard;
