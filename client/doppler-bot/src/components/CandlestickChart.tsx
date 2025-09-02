'use client';

import { useEffect, useRef, useState } from 'react';
import { CandlestickSeries, HistogramSeries, LineSeries, createChart, ColorType } from 'lightweight-charts';
import { Box, FormControlLabel, Switch, Grid, Paper, Typography } from '@mui/material';
import { calculateMACD, calculateVWAP, calculateRSI, calculateEMA } from '../utils/indicators';
import { Stock } from '@/types';

interface CandlestickChartProps {
    stock: Stock;
    onUnselect?: () => void;
}

const CandlestickChart = ({ stock, onUnselect }: CandlestickChartProps) => {
    const chartRef = useRef<HTMLDivElement>(null);
    const macdChartRef = useRef<HTMLDivElement>(null);
    const rsiChartRef = useRef<HTMLDivElement>(null);
    const chartInstance = useRef<any>(null);
    const macdChartInstance = useRef<any>(null);
    const rsiChartInstance = useRef<any>(null);
    const seriesRef = useRef<any>(null);
    const volumeSeriesRef = useRef<any>(null);
    const macdSeriesRef = useRef<any>(null);
    const signalSeriesRef = useRef<any>(null);
    const histogramSeriesRef = useRef<any>(null);
    const vwapSeriesRef = useRef<any>(null);
    const ema200SeriesRef = useRef<any>(null);
    const rsiSeriesRef = useRef<any>(null);
    const [latestData, setLatestData] = useState<any>(null);
    const [macdData, setMacdData] = useState<any>(null);
    const [rsiData, setRsiData] = useState<any>(null);
    const [showVWAP, setShowVWAP] = useState(true);
    const [showEMA200, setShowEMA200] = useState(true);
    const [showRSI, setShowRSI] = useState(true);
    const [showMACD, setShowMACD] = useState(true);
    const [tooltipData, setTooltipData] = useState<any>(null);
    const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

    useEffect(() => {
        const handleResize = () => {
            if (chartRef.current && chartInstance.current) {
                chartInstance.current.applyOptions({ width: chartRef.current.clientWidth });
            }
            if (macdChartRef.current && macdChartInstance.current) {
                macdChartInstance.current.applyOptions({ width: macdChartRef.current.clientWidth });
            }
            if (rsiChartRef.current && rsiChartInstance.current) {
                rsiChartInstance.current.applyOptions({ width: rsiChartRef.current.clientWidth });
            }
        };

        // Initialize main chart
        if (chartRef.current) {
            chartInstance.current = createChart(chartRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: '#242424' },
                    textColor: '#ffffff',
                },
                width: chartRef.current.clientWidth,
                height: 300,
                timeScale: {
                    timeVisible: true,
                    secondsVisible: true,
                    rightOffset: 12,
                    barSpacing: 6,
                    fixLeftEdge: true,
                    lockVisibleTimeRangeOnResize: true,
                },
                grid: {
                    vertLines: {
                        color: '#333333',
                        style: 0,
                    },
                    horzLines: {
                        color: '#333333',
                        style: 0,
                    },
                },
            });

            chartInstance.current.timeScale().fitContent();
            chartInstance.current.timeScale().scrollToPosition(5);

            seriesRef.current = chartInstance.current.addSeries(CandlestickSeries, {
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
                priceFormat: {
                    type: 'price',
                    precision: 4,
                    minMove: 0.0001,
                }
            });

            // Add VWAP line
            vwapSeriesRef.current = chartInstance.current.addSeries(LineSeries, {
                color: '#9C27B0',
                lineWidth: 1,
                priceLineVisible: false,
                lastValueVisible: false,
                visible: showVWAP
            });

            // Add EMA200 line
            ema200SeriesRef.current = chartInstance.current.addSeries(LineSeries, {
                color: '#FF9800',
                lineWidth: 1,
                priceLineVisible: false,
                lastValueVisible: false,
                visible: showEMA200
            });

            // Add volume series
            volumeSeriesRef.current = chartInstance.current.addSeries(HistogramSeries, {
                color: '#26a69a',
                priceFormat: {
                    type: 'volume',
                },
                priceScaleId: 'volume',
            });
            volumeSeriesRef.current.priceScale().applyOptions({
                scaleMargins: {
                    top: 0.7,
                    bottom: 0,
                },
            });

            // Add time scale sync handlers
            chartInstance.current.timeScale().subscribeVisibleLogicalRangeChange((range: any) => {
                if (range && macdChartInstance.current) {
                    macdChartInstance.current.timeScale().setVisibleLogicalRange(range);
                }
                if (range && rsiChartInstance.current) {
                    rsiChartInstance.current.timeScale().setVisibleLogicalRange(range);
                }
            });
        }

        // Initialize MACD chart
        if (macdChartRef.current) {
            macdChartInstance.current = createChart(macdChartRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: '#242424' },
                    textColor: '#ffffff',
                },
                width: macdChartRef.current.clientWidth,
                height: 150,
                timeScale: {
                    timeVisible: true,
                    secondsVisible: true,
                    rightOffset: 12,
                    barSpacing: 6,
                    fixLeftEdge: true,
                    lockVisibleTimeRangeOnResize: true,
                },
                grid: {
                    vertLines: {
                        color: '#333333',
                        style: 0,
                    },
                    horzLines: {
                        color: '#333333',
                        style: 0,
                    },
                },
            });

            macdChartInstance.current.timeScale().fitContent();
            macdChartInstance.current.timeScale().scrollToPosition(5);

            // Add MACD series
            macdSeriesRef.current = macdChartInstance.current.addSeries(LineSeries, {
                color: '#2962FF',
                lineWidth: 1,
                visible: showMACD,
                priceFormat: {
                    type: 'price',
                    precision: 4,
                    minMove: 0.0001,
                }
            });

            signalSeriesRef.current = macdChartInstance.current.addSeries(LineSeries, {
                color: '#FF6D00',
                lineWidth: 1,
                visible: showMACD,
                priceFormat: {
                    type: 'price',
                    precision: 4,
                    minMove: 0.0001,
                }
            });

            histogramSeriesRef.current = macdChartInstance.current.addSeries(HistogramSeries, {
                color: '#26a69a',
                visible: showMACD,
                priceFormat: {
                    type: 'price',
                    precision: 4,
                    minMove: 0.0001,
                }
            });

            // Add time scale sync handlers
            macdChartInstance.current.timeScale().subscribeVisibleLogicalRangeChange((range: any) => {
                if (range && chartInstance.current) {
                    chartInstance.current.timeScale().setVisibleLogicalRange(range);
                }
                if (range && rsiChartInstance.current) {
                    rsiChartInstance.current.timeScale().setVisibleLogicalRange(range);
                }
            });
        }

        // Initialize RSI chart
        if (rsiChartRef.current) {
            rsiChartInstance.current = createChart(rsiChartRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: '#242424' },
                    textColor: '#ffffff',
                },
                width: rsiChartRef.current.clientWidth,
                height: 150,
                timeScale: {
                    timeVisible: true,
                    secondsVisible: true,
                    rightOffset: 12,
                    barSpacing: 6,
                    fixLeftEdge: true,
                    lockVisibleTimeRangeOnResize: true,
                },
                grid: {
                    vertLines: {
                        color: '#333333',
                        style: 0,
                    },
                    horzLines: {
                        color: '#333333',
                        style: 0,
                    },
                },
            });

            rsiChartInstance.current.timeScale().fitContent();
            rsiChartInstance.current.timeScale().scrollToPosition(5);

            // Add RSI series
            rsiSeriesRef.current = rsiChartInstance.current.addSeries(LineSeries, {
                color: '#E91E63',
                lineWidth: 1,
                visible: showRSI
            });

            // Add overbought/oversold lines
            rsiChartInstance.current.addSeries(LineSeries, {
                color: '#666666',
                lineWidth: 1,
                lineStyle: 2, // dashed
                price: 70,
            });

            rsiChartInstance.current.addSeries(LineSeries, {
                color: '#666666',
                lineWidth: 1,
                lineStyle: 2, // dashed
                price: 30,
            });

            // Add time scale sync handlers
            rsiChartInstance.current.timeScale().subscribeVisibleLogicalRangeChange((range: any) => {
                if (range && chartInstance.current) {
                    chartInstance.current.timeScale().setVisibleLogicalRange(range);
                }
                if (range && macdChartInstance.current) {
                    macdChartInstance.current.timeScale().setVisibleLogicalRange(range);
                }
            });
        }

        // Add crosshair move handler for main chart
        if (chartInstance.current) {
            chartInstance.current.subscribeCrosshairMove((param: any) => {
                if (param.point === undefined || !param.time || param.point.x < 0 || param.point.y < 0) {
                    setTooltipData(null);
                    return;
                }

                const data = param.seriesData.get(seriesRef.current);
                const volumeData = param.seriesData.get(volumeSeriesRef.current);
                const vwapData = param.seriesData.get(vwapSeriesRef.current);
                const ema200Data = param.seriesData.get(ema200SeriesRef.current);

                if (data) {
                    const tooltipInfo = {
                        ...data,
                        volume: volumeData ? volumeData.value : null,
                        vwap: vwapData ? vwapData.value : null,
                        ema200: ema200Data ? ema200Data.value : null,
                        time: new Date(param.time * 1000).toLocaleString(),
                    };

                    setTooltipData(tooltipInfo);
                    setTooltipPosition({ x: param.point.x, y: param.point.y });

                    setLatestData({
                        ...data,
                        volume: volumeData ? volumeData.value : null,
                        vwap: vwapData ? vwapData.value : null,
                        ema200: ema200Data ? ema200Data.value : null,
                    });
                } else {
                    setTooltipData(null);
                }
            });
        }

        if (macdChartInstance.current) {
            macdChartInstance.current.subscribeCrosshairMove((param: any) => {
                if (param.point === undefined || !param.time || param.point.x < 0 || param.point.y < 0) {
                    return;
                }

                const macdData = param.seriesData.get(macdSeriesRef.current);
                const signalData = param.seriesData.get(signalSeriesRef.current);
                const histogramData = param.seriesData.get(histogramSeriesRef.current);

                if (macdData) {
                    setMacdData({
                        macd: macdData.value,
                        signal: signalData ? signalData.value : null,
                        histogram: histogramData ? histogramData.value : null,
                    });
                }
            });
        }

        if (rsiChartInstance.current) {
            rsiChartInstance.current.subscribeCrosshairMove((param: any) => {
                if (param.point === undefined || !param.time || param.point.x < 0 || param.point.y < 0) {
                    return;
                }

                const rsiData = param.seriesData.get(rsiSeriesRef.current);

                if (rsiData) {
                    setRsiData({
                        rsi: rsiData.value,
                    });
                }
            });
        }

        window.addEventListener('resize', handleResize);

        // Cleanup function
        return () => {
            window.removeEventListener('resize', handleResize);
            if (chartInstance.current) {
                chartInstance.current.remove();
                chartInstance.current = null;
            }
            if (macdChartInstance.current) {
                macdChartInstance.current.remove();
                macdChartInstance.current = null;
            }
            if (rsiChartInstance.current) {
                rsiChartInstance.current.remove();
                rsiChartInstance.current = null;
            }
            seriesRef.current = null;
            volumeSeriesRef.current = null;
            macdSeriesRef.current = null;
            signalSeriesRef.current = null;
            histogramSeriesRef.current = null;
            vwapSeriesRef.current = null;
            ema200SeriesRef.current = null;
            rsiSeriesRef.current = null;
        };
    }, []);

    useEffect(() => {
        if (stock.candles && stock.candles.length > 0) {
            const stock_data = stock.candles.map((candle: any, index: number) => ({
                time: new Date(candle.timestamp).getTime() / 1000,
                open: candle.open,
                high: candle.high,
                low: candle.low,
                close: candle.close,
                volume: candle.volume
            })).sort((a: any, b: any) => a.time - b.time);

            const volume_data = stock.candles.map((candle: any, index: number) => ({
                time: new Date(candle.timestamp).getTime() / 1000,
                value: candle.volume,
                color: candle.close >= candle.open ? '#26a69a55' : '#ef535055',
            })).sort((a: any, b: any) => a.time - b.time);

            const closes = stock_data.map((d: any) => d.close);
            const { macd, signal, histogram } = calculateMACD(closes);
            const vwap = calculateVWAP(stock_data);
            const ema200 = calculateEMA(closes, 200);
            const rsi = calculateRSI(closes);

            const macd_data = stock_data.map((d: any, i: number) => ({
                time: d.time,
                value: macd[i] !== null ? macd[i] : 0
            }));

            const signal_data = stock_data.map((d: any, i: number) => ({
                time: d.time,
                value: signal[i] !== null ? signal[i] : 0
            }));

            const histogram_data = stock_data.map((d: any, i: number) => ({
                time: d.time,
                value: histogram[i] !== null ? histogram[i] : 0,
                color: (histogram[i] !== null ? histogram[i] : 0) >= 0 ? '#26a69a55' : '#ef535055'
            }));

            const vwap_data = stock_data.map((d: any, i: number) => ({
                time: d.time,
                value: vwap[i] !== null ? vwap[i] : 0
            }));

            const ema200_data = stock_data.map((d: any, i: number) => ({
                time: d.time,
                value: ema200[i] !== null ? ema200[i] : 0
            }));

            const rsi_data = stock_data.map((d: any, i: number) => ({
                time: d.time,
                value: rsi[i] !== null ? rsi[i] : 0
            }));

            if (seriesRef.current) {
                seriesRef.current.setData(stock_data);
                if (stock_data.length > 0) {
                    const lastData = stock_data[stock_data.length - 1];
                    const lastVolume = volume_data[volume_data.length - 1];
                    setLatestData({
                        ...lastData,
                        volume: lastVolume ? lastVolume.value : null
                    });

                    setRsiData({
                        rsi: rsi[rsi.length - 1] || 0
                    });
                }
            }

            if (volumeSeriesRef.current) {
                volumeSeriesRef.current.setData(volume_data);
            }

            if (macdSeriesRef.current) {
                macdSeriesRef.current.setData(macd_data);
            }

            if (signalSeriesRef.current) {
                signalSeriesRef.current.setData(signal_data);
            }

            if (histogramSeriesRef.current) {
                histogramSeriesRef.current.setData(histogram_data);
            }

            if (vwapSeriesRef.current) {
                vwapSeriesRef.current.setData(vwap_data);
            }

            if (ema200SeriesRef.current) {
                ema200SeriesRef.current.setData(ema200_data);
            }

            if (rsiSeriesRef.current) {
                rsiSeriesRef.current.setData(rsi_data);
            }
        }
    }, [stock.candles]);

    return (
        <Box sx={{ flexGrow: 1, mb: 4, padding: 2, backgroundColor: '#242424', borderRadius: 2 }} key={stock.ticker}>
            <div style={{ position: 'relative', width: '100%' }}>
                <div ref={chartRef} style={{ position: 'relative', height: '300px' }} />
                <div ref={macdChartRef} style={{ position: 'relative', height: '150px', display: showMACD ? 'block' : 'none' }} />
                <div ref={rsiChartRef} style={{ position: 'relative', height: '150px', display: showRSI ? 'block' : 'none' }} />

                {/* OHLCV Tooltip */}
                {tooltipData && (
                    <Paper
                        sx={{
                            position: 'absolute',
                            left: tooltipPosition.x + 10,
                            top: tooltipPosition.y - 10,
                            zIndex: 1000,
                            backgroundColor: 'rgba(36, 36, 36, 0.95)',
                            padding: '12px',
                            borderRadius: '8px',
                            border: '1px solid #333333',
                            minWidth: '200px',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                        }}
                    >
                        <Typography variant="caption" sx={{ color: '#888', display: 'block', mb: 1 }}>
                            {tooltipData.time}
                        </Typography>
                        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, fontSize: '0.8rem' }}>
                            <Box sx={{ color: '#26a69a' }}>O: {tooltipData.open?.toFixed(4)}</Box>
                            <Box sx={{ color: '#ef5350' }}>H: {tooltipData.high?.toFixed(4)}</Box>
                            <Box sx={{ color: '#ef5350' }}>L: {tooltipData.low?.toFixed(4)}</Box>
                            <Box sx={{ color: '#26a69a' }}>C: {tooltipData.close?.toFixed(4)}</Box>
                            <Box sx={{ color: '#888', gridColumn: '1 / -1' }}>V: {tooltipData.volume?.toLocaleString()}</Box>
                            {tooltipData.vwap && (
                                <Box sx={{ color: '#9C27B0', gridColumn: '1 / -1' }}>
                                    VWAP: {tooltipData.vwap.toFixed(4)}
                                </Box>
                            )}
                            {tooltipData.ema200 && (
                                <Box sx={{ color: '#FF9800', gridColumn: '1 / -1' }}>
                                    EMA200: {tooltipData.ema200.toFixed(4)}
                                </Box>
                            )}
                        </Box>
                    </Paper>
                )}

                <Box sx={{
                    position: 'absolute',
                    top: 10,
                    right: 10,
                    zIndex: 100,
                    backgroundColor: 'rgba(36, 36, 36, 0.8)',
                    padding: '8px',
                    borderRadius: '4px',
                    border: '1px solid #333333'
                }}>
                    <FormControlLabel
                        control={
                            <Switch
                                checked={showMACD}
                                onChange={(e) => {
                                    setShowMACD(e.target.checked);
                                    if (macdChartRef.current) {
                                        macdChartRef.current.style.display = e.target.checked ? 'block' : 'none';
                                    }
                                }}
                                size="small"
                            />
                        }
                        label={<span style={{ color: '#2962FF' }}>MACD</span>}
                        sx={{ '& .MuiFormControlLabel-label': { fontSize: '0.8rem' } }}
                    />
                    <FormControlLabel
                        control={
                            <Switch
                                checked={showVWAP}
                                onChange={(e) => {
                                    setShowVWAP(e.target.checked);
                                    if (vwapSeriesRef.current) {
                                        vwapSeriesRef.current.applyOptions({ visible: e.target.checked });
                                    }
                                }}
                                size="small"
                            />
                        }
                        label={<span style={{ color: '#9C27B0' }}>VWAP</span>}
                        sx={{ '& .MuiFormControlLabel-label': { fontSize: '0.8rem' } }}
                    />
                    <FormControlLabel
                        control={
                            <Switch
                                checked={showEMA200}
                                onChange={(e) => {
                                    setShowEMA200(e.target.checked);
                                    if (ema200SeriesRef.current) {
                                        ema200SeriesRef.current.applyOptions({ visible: e.target.checked });
                                    }
                                }}
                                size="small"
                            />
                        }
                        label={<span style={{ color: '#FF9800' }}>EMA200</span>}
                        sx={{ '& .MuiFormControlLabel-label': { fontSize: '0.8rem' } }}
                    />
                    <FormControlLabel
                        control={
                            <Switch
                                checked={showRSI}
                                onChange={(e) => {
                                    setShowRSI(e.target.checked);
                                    if (rsiChartRef.current) {
                                        rsiChartRef.current.style.display = e.target.checked ? 'block' : 'none';
                                    }
                                }}
                                size="small"
                            />
                        }
                        label={<span style={{ color: '#E91E63' }}>RSI</span>}
                        sx={{ '& .MuiFormControlLabel-label': { fontSize: '0.8rem' } }}
                    />
                </Box>
            </div>
        </Box>
    );
};

export default CandlestickChart;
