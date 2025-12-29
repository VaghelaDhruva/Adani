import React from 'react';
import { Card, Alert, Typography, Space, Tag, Collapse, Table, Button } from 'antd';
import { useQuery } from 'react-query';
import { 
  CheckCircleOutlined, 
  WarningOutlined, 
  CloseCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { fetchValidationReport } from '../services/api';

const { Title, Text } = Typography;
const { Panel } = Collapse;

const DataValidation = () => {
  const { 
    data: validationData, 
    isLoading, 
    error,
    refetch 
  } = useQuery(
    'validation-report',
    fetchValidationReport,
    {
      refetchInterval: 30000,
    }
  );

  const getStageIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'pass':
        return <CheckCircleOutlined style={{ color: '#2e7d32' }} />;
      case 'warn':
        return <WarningOutlined style={{ color: '#f57c00' }} />;
      case 'fail':
        return <CloseCircleOutlined style={{ color: '#d32f2f' }} />;
      default:
        return null;
    }
  };

  const getStageColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'pass':
        return 'success';
      case 'warn':
        return 'warning';
      case 'fail':
        return 'error';
      default:
        return 'default';
    }
  };

  if (error) {
    return (
      <Alert
        message="Error Loading Validation Report"
        description="Failed to load validation data. Please try again."
        type="error"
        showIcon
        action={<Button onClick={() => refetch()} icon={<ReloadOutlined />}>Retry</Button>}
      />
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Space direction="vertical" size="small">
          <Title level={2} style={{ margin: 0, color: '#1f4e79' }}>
            Data Validation Report
          </Title>
          <Text type="secondary">
            Comprehensive 5-stage validation pipeline with detailed error reporting
          </Text>
        </Space>
        
        <div style={{ marginTop: 16 }}>
          <Button 
            onClick={() => refetch()} 
            icon={<ReloadOutlined />}
            loading={isLoading}
          >
            Refresh Report
          </Button>
        </div>
      </div>

      {/* Optimization Readiness Alert */}
      {validationData?.optimization_blocked && (
        <Alert
          message="Optimization Blocked"
          description={
            <div>
              <Text>The following critical errors must be resolved before optimization can run:</Text>
              <ul style={{ marginTop: 8, marginBottom: 0 }}>
                {validationData.blocking_errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          }
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {!validationData?.optimization_blocked && (
        <Alert
          message="Validation Passed"
          description="All critical validation stages have passed. Optimization is ready to run."
          type="success"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Validation Stages */}
      <Card title="Validation Pipeline Stages" loading={isLoading}>
        <Collapse>
          {validationData?.stages?.map((stage, index) => (
            <Panel
              header={
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <Tag color={getStageColor(stage.status)} icon={getStageIcon(stage.status)}>
                    {stage.status.toUpperCase()}
                  </Tag>
                  <Text strong>Stage {index + 1}: {stage.stage.replace('_', ' ').toUpperCase()}</Text>
                  {stage.errors.length > 0 && (
                    <Tag color="red">{stage.errors.length} errors</Tag>
                  )}
                  {stage.warnings.length > 0 && (
                    <Tag color="orange">{stage.warnings.length} warnings</Tag>
                  )}
                </div>
              }
              key={stage.stage}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                {/* Errors */}
                {stage.errors.length > 0 && (
                  <div>
                    <Text strong style={{ color: '#d32f2f' }}>Errors:</Text>
                    <div style={{ marginTop: 8 }}>
                      {stage.errors.map((error, errorIndex) => (
                        <Alert
                          key={errorIndex}
                          message={error.error}
                          type="error"
                          style={{ marginBottom: 8 }}
                          description={
                            <div>
                              {error.table && <Text type="secondary">Table: {error.table}</Text>}
                              {error.column && <Text type="secondary"> | Column: {error.column}</Text>}
                              {error.severity && <Text type="secondary"> | Severity: {error.severity}</Text>}
                            </div>
                          }
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Warnings */}
                {stage.warnings.length > 0 && (
                  <div>
                    <Text strong style={{ color: '#f57c00' }}>Warnings:</Text>
                    <div style={{ marginTop: 8 }}>
                      {stage.warnings.map((warning, warningIndex) => (
                        <Alert
                          key={warningIndex}
                          message={warning.warning}
                          type="warning"
                          style={{ marginBottom: 8 }}
                          description={
                            <div>
                              {warning.table && <Text type="secondary">Table: {warning.table}</Text>}
                              {warning.impact && <Text type="secondary"> | Impact: {warning.impact}</Text>}
                            </div>
                          }
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Row-level Errors */}
                {stage.row_level_errors && stage.row_level_errors.length > 0 && (
                  <div>
                    <Text strong style={{ color: '#d32f2f' }}>Row-level Issues:</Text>
                    <Table
                      dataSource={stage.row_level_errors.slice(0, 10)} // Show first 10
                      size="small"
                      pagination={false}
                      style={{ marginTop: 8 }}
                      columns={[
                        {
                          title: 'Table',
                          dataIndex: 'table',
                          key: 'table',
                          width: 150,
                        },
                        {
                          title: 'Row',
                          dataIndex: 'row',
                          key: 'row',
                          width: 80,
                          align: 'center',
                        },
                        {
                          title: 'Error',
                          dataIndex: 'error',
                          key: 'error',
                        },
                        {
                          title: 'Context',
                          key: 'context',
                          render: (record: any) => (
                            <div>
                              {Object.entries(record)
                                .filter(([key]) => !['table', 'row', 'error'].includes(key))
                                .map(([key, value]) => (
                                  <div key={key} style={{ fontSize: '0.8rem' }}>
                                    <Text type="secondary">{key}: {String(value)}</Text>
                                  </div>
                                ))
                              }
                            </div>
                          ),
                        },
                      ]}
                    />
                    {stage.row_level_errors.length > 10 && (
                      <Text type="secondary" style={{ fontSize: '0.9rem' }}>
                        ... and {stage.row_level_errors.length - 10} more row-level errors
                      </Text>
                    )}
                  </div>
                )}

                {/* No Issues */}
                {stage.errors.length === 0 && stage.warnings.length === 0 && 
                 (!stage.row_level_errors || stage.row_level_errors.length === 0) && (
                  <div style={{ 
                    textAlign: 'center', 
                    padding: '20px', 
                    background: '#f6ffed',
                    borderRadius: '6px',
                    border: '1px solid #b7eb8f'
                  }}>
                    <CheckCircleOutlined style={{ color: '#2e7d32', fontSize: '1.5rem' }} />
                    <div style={{ marginTop: 8 }}>
                      <Text style={{ color: '#2e7d32' }}>All checks passed for this stage</Text>
                    </div>
                  </div>
                )}
              </Space>
            </Panel>
          ))}
        </Collapse>
      </Card>

      {/* Summary Statistics */}
      <Card title="Validation Summary" style={{ marginTop: 16 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div style={{ textAlign: 'center', padding: '16px', background: '#f0f0f0', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1f4e79' }}>
              {validationData?.stages?.length || 0}
            </div>
            <Text type="secondary">Validation Stages</Text>
          </div>
          <div style={{ textAlign: 'center', padding: '16px', background: '#fff2e8', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f57c00' }}>
              {validationData?.stages?.reduce((sum, stage) => sum + stage.warnings.length, 0) || 0}
            </div>
            <Text type="secondary">Total Warnings</Text>
          </div>
          <div style={{ textAlign: 'center', padding: '16px', background: '#ffebee', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#d32f2f' }}>
              {validationData?.stages?.reduce((sum, stage) => sum + stage.errors.length, 0) || 0}
            </div>
            <Text type="secondary">Total Errors</Text>
          </div>
          <div style={{ textAlign: 'center', padding: '16px', background: '#e8f5e8', borderRadius: '8px' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#2e7d32' }}>
              {validationData?.stages?.filter(stage => stage.status === 'pass').length || 0}
            </div>
            <Text type="secondary">Stages Passed</Text>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default DataValidation;