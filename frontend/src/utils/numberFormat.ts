// Indian Number Formatting Utility
// Shared across all dashboard components

// Format number with Indian numbering system (K, L, Cr)
export const formatIndianNumber = (num: number): string => {
  if (num >= 10000000) { // 1 Crore
    const crores = num / 10000000;
    return `${crores.toFixed(2)} Cr`;
  } else if (num >= 100000) { // 1 Lakh
    const lakhs = num / 100000;
    return `${lakhs.toFixed(2)} L`;
  } else if (num >= 1000) { // 1 Thousand
    const thousands = num / 1000;
    return `${thousands.toFixed(1)} K`;
  } else {
    return num.toFixed(1); // Show decimal for numbers like 53.2
  }
};

// Format currency with Indian numbering system
export const formatIndianCurrency = (num: number): string => {
  if (num >= 10000000) { // 1 Crore
    const crores = num / 10000000;
    return `₹${crores.toFixed(2)} Cr`;
  } else if (num >= 100000) { // 1 Lakh
    const lakhs = num / 100000;
    return `₹${lakhs.toFixed(2)} L`;
  } else if (num >= 1000) { // 1 Thousand
    const thousands = num / 1000;
    return `₹${thousands.toFixed(1)} K`;
  } else {
    return `₹${num.toFixed(1)}`; // Show decimal for small amounts
  }
};

// Format large numbers with appropriate units
export const formatLargeNumber = (num: number, unit: string = ''): string => {
  const formatted = formatIndianNumber(num);
  return unit ? `${formatted} ${unit}` : formatted;
};

// Format weight in tonnes with Indian numbering
export const formatWeight = (tonnes: number): string => {
  return formatLargeNumber(tonnes, 'tonnes');
};

// Format volume in tonnes with Indian numbering
export const formatVolume = (tonnes: number): string => {
  return formatLargeNumber(tonnes, 'tonnes');
};

// Format cost per unit with Indian numbering
export const formatCostPerUnit = (cost: number, unit: string): string => {
  return `₹${formatIndianNumber(cost)}/${unit}`;
};

// Parse Indian number input (K, L, Cr) to regular number
export const parseIndianNumber = (input: string): number => {
  const str = input.toString().trim();
  if (str.includes('Cr')) return parseFloat(str.replace(/[^0-9.]/g, '')) * 10000000;
  if (str.includes('L')) return parseFloat(str.replace(/[^0-9.]/g, '')) * 100000;
  if (str.includes('K')) return parseFloat(str.replace(/[^0-9.]/g, '')) * 1000;
  return parseFloat(str.replace(/[^0-9.]/g, '')) || 0;
};

// Industry-specific clinker data validation
export const validateClinkerData = (volume: number, weight: number): boolean => {
  // Clinker density should be around 1440 kg/m³
  const density = weight > 0 ? (weight * 1000) / volume : 0;
  return density >= 1400 && density <= 1500; // Acceptable range for clinker
};

// Get clinker density from volume and weight
export const getClinkerDensity = (volume: number, weight: number): number => {
  return weight > 0 && volume > 0 ? (weight * 1000) / volume : 1440; // Default 1440 kg/m³
};

// Format percentage with Indian numbering if needed
export const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

// Format ratio with Indian numbering
export const formatRatio = (numerator: number, denominator: number): string => {
  const ratio = denominator > 0 ? numerator / denominator : 0;
  return formatIndianNumber(ratio);
};
