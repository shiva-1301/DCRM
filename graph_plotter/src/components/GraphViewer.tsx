import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { useData } from '../context/DataContext';
import { getUnitType, convertValue } from '../utils/unitConversion';

export const GraphViewer: React.FC = () => {
    const {
        data, data2, fileLabels,
        selectedX, selectedY, selectedY2,
        xAxisSource, range, showGrid, showLegend, unitPrefs
    } = useData();

    const plotData = useMemo(() => {
        if (!data && !data2) return { data: [], xTitle: '' };

        // Determine which file to use for X-axis
        const sourceData = xAxisSource === 'file1' ? data : data2;
        if (!sourceData) return { data: [], xTitle: '' };

        // Slice data based on range
        const start = range[0];
        const end = range[1] + 1; // Slice is exclusive at end

        // Get X data from source
        let xData: number[] = [];
        let xTitle = selectedX;

        if (selectedX === 'Time') {
            const targetUnit = unitPrefs.time;
            xData = sourceData.time.slice(start, end).map(v => convertValue(v, 'time', targetUnit));
            xTitle = `Time (${targetUnit})`;
        } else if (selectedX === 'Index') {
            xData = Array.from({ length: end - start }, (_, i) => start + i);
        } else {
            const type = getUnitType(selectedX);
            const targetUnit = unitPrefs[type];
            xData = (sourceData.series[selectedX]?.slice(start, end) || []).map(v => convertValue(v, type, targetUnit));
            xTitle = targetUnit ? `${selectedX} (${targetUnit})` : selectedX;
        }

        const seriesData: any[] = [];

        // Add File 1 series (blue colors)
        if (data && selectedY.length > 0) {
            selectedY.forEach((yKey, idx) => {
                const type = getUnitType(yKey);
                const targetUnit = unitPrefs[type];
                const yData = (data.series[yKey]?.slice(start, end) || []).map(v => convertValue(v, type, targetUnit));

                // Use blue color palette for File 1
                const blueColors = ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#1e40af', '#1d4ed8'];

                seriesData.push({
                    x: xData,
                    y: yData,
                    type: 'scatter' as const,
                    mode: 'lines' as const,
                    name: `📘 ${fileLabels.file1}: ${yKey}${targetUnit ? ` (${targetUnit})` : ''}`,
                    line: {
                        shape: 'spline' as const,
                        color: blueColors[idx % blueColors.length],
                        width: 2
                    },
                });
            });
        }

        // Add File 2 series (green colors)
        if (data2 && selectedY2.length > 0) {
            selectedY2.forEach((yKey, idx) => {
                const type = getUnitType(yKey);
                const targetUnit = unitPrefs[type];
                const yData = (data2.series[yKey]?.slice(start, end) || []).map(v => convertValue(v, type, targetUnit));

                // Use green color palette for File 2
                const greenColors = ['#16a34a', '#22c55e', '#4ade80', '#86efac', '#15803d', '#166534'];

                seriesData.push({
                    x: xData,
                    y: yData,
                    type: 'scatter' as const,
                    mode: 'lines' as const,
                    name: `📗 ${fileLabels.file2}: ${yKey}${targetUnit ? ` (${targetUnit})` : ''}`,
                    line: {
                        shape: 'spline' as const,
                        color: greenColors[idx % greenColors.length],
                        width: 2,
                        dash: 'dot' as const  // Dotted line to distinguish from File 1
                    },
                });
            });
        }

        return {
            data: seriesData,
            xTitle
        };
    }, [data, data2, fileLabels, selectedX, selectedY, selectedY2, xAxisSource, range, unitPrefs]);

    if (!data && !data2) {
        return (
            <div className="flex items-center justify-center h-full bg-slate-50 text-slate-400">
                No data loaded
            </div>
        );
    }

    return (
        <div className="w-full h-full p-4 bg-white rounded-xl shadow-sm border border-slate-200">
            <Plot
                data={plotData.data}
                layout={{
                    autosize: true,
                    title: { text: 'DCRM Comparison Analysis' },
                    xaxis: {
                        title: { text: plotData.xTitle },
                        showgrid: showGrid,
                        zeroline: false,
                    },
                    yaxis: {
                        title: { text: 'Value' },
                        showgrid: showGrid,
                        zeroline: false,
                    },
                    showlegend: showLegend,
                    legend: { orientation: 'h', y: -0.2 },
                    margin: { l: 50, r: 20, t: 40, b: 80 },
                    hovermode: 'closest',
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
                config={{
                    responsive: true,
                    displayModeBar: true,
                    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                }}
            />
        </div>
    );
};
