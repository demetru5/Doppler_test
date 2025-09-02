import { Stock } from "@/types";

// Utility function to get color based on indicator type and value
export const getIndicatorColor = (type: string, value: number): string => {
    if (value === null || value === undefined || isNaN(value)) return 'inherit';

    switch (type) {
        case 'technical_score':
            if (value >= 70) return '#4caf50'; // Green - excellent
            if (value >= 50) return '#8bc34a'; // Light green - good
            if (value >= 30) return '#ff9800'; // Orange - moderate
            return '#f44336'; // Red - poor

        case 'float_share':
            if (value < 20000000) return '#4caf50'; // Green - excellent
            return '#ff9800'; // Orange - moderate

        case 'rvol':
            if (value >= 2.5) return '#4caf50'; // Green - excellent
            if (value >= 1.5) return '#8bc34a'; // Light green - good
            if (value >= 1.0) return '#ff9800'; // Orange - moderate
            return '#f44336'; // Red - poor

        case 'a2v':
            if (value >= 0.50) return '#4caf50'; // Green - excellent
            if (value >= 0) return '#ff9800'; // Orange - moderate
            return '#f44336'; // Red - poor

        case 'volume_ratio':
            if (value >= 2.5) return '#4caf50'; // Green - excellent
            if (value >= 1.5) return '#8bc34a'; // Light green - good
            if (value >= 1.0) return '#ff9800'; // Orange - moderate
            return '#f44336'; // Red - poor

        case 'atr_hod':
            if (value <= 1) return '#4caf50'; // Green - excellent
            if (value <= 2.83) return '#ff9800'; // Orange - moderate
            return '#f44336'; // Red - poor

        case 'roc':
            if (value > 3) return '#4caf50'; // Green - excellent
            if (value >= 1 && value <= 3) return '#ff9800'; // Orange - moderate
            return 'inherit'; // Default

        case 'adx':
            if (value > 25) return '#4caf50'; // Green - excellent
            if (value > 10) return '#ff9800'; // Orange - moderate
            return '#f44336'; // Red - poor

        case 'vwap_slope':
            if (value > 0) return '#4caf50'; // Green - excellent
            if (value == 0) return '#ff9800'; // Orange - moderate
            return '#f44336'; // Red - poor

        case 'zenp':
            if (value > 1) return '#4caf50'; // Green - excellent
            if (value > 0.5) return '#ff9800'; // Orange - moderate
            return '#f44336'; // Red - poor

        case 'atr_spread':
            if (value < 0.2) return '#4caf50'; // Green - excellent
            if (value < 0.5) return '#ff9800'; // Orange - moderate
            return '#f44336'; // Red - poor

        case 'probability':
            if (value >= 0.5) return '#4caf50'; // Green - excellent
            if (value >= 0.25) return '#ff9800'; // Orange - moderate
            return '#f44336'; // Red - poor

        default:
            return value < 0 ? '#f44336' : 'inherit'; // Red for negative values
    }
};

// Helper function to format numbers
export const formatNumber = (value: number, decimals: number = 2): string => {
    if (value === null || value === undefined || isNaN(value) || value === Infinity) return 'N/A';
    return value.toFixed(decimals);
};

// Helper function to format large numbers
export const formatLargeNumber = (value: number): string => {
    if (value === null || value === undefined || isNaN(value)) return 'N/A';
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toFixed(0);
};

// Helper function to check all green condition
export const checkAllGreen = (stock: Stock) => {
    return (
        stock?.scores?.technical_score >= 70 &&
        stock.float_share && stock.float_share < 20000000 &&
        stock?.indicators?.RVol >= 2.5 &&
        stock?.indicators?.ATR_to_VWAP >= 0.50 &&
        stock?.indicators?.Volume_Ratio >= 2.5 &&
        stock?.indicators?.ATR_to_HOD <= 1 &&
        stock?.indicators?.ROC > 3 &&
        stock?.indicators?.ADX > 25 &&
        stock?.indicators?.VWAP_Slope >= 0 &&
        stock?.indicators?.ZENP > 1 &&
        stock?.indicators?.ATR_Spread < 0.2
    )
}

// Helper function for green indicator counts
export const getGreenIndicatorCount = (stock: Stock) => {
    return (
        (stock?.scores?.technical_score >= 70 ? 1 : 0) +
        (stock.float_share && stock.float_share < 20000000 ? 1 : 0) +
        (stock?.indicators?.RVol >= 2.5 ? 1 : 0) +
        (stock?.indicators?.ATR_to_VWAP >= 0.50 ? 1 : 0) +
        (stock?.indicators?.Volume_Ratio >= 2.5 ? 1 : 0) +
        (stock?.indicators?.ATR_to_HOD <= 1 ? 1 : 0) +
        (stock?.indicators?.ROC > 3 ? 1 : 0) +
        (stock?.indicators?.ADX > 25 ? 1 : 0) +
        (stock?.indicators?.VWAP_Slope >= 0 ? 1 : 0) +
        (stock?.indicators?.ZenP > 1 ? 1 : 0) +
        (stock?.indicators?.ATR_Spread < 0.2 ? 1 : 0)
    )
}

// Helper function for human readable date time
export const humanReadableDateTime = (datetime: string) => {
    return new Date(datetime).toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    }).replace(',', '')
}