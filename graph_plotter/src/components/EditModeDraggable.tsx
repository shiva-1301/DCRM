import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Plotly from 'plotly.js-dist-min';
import { useData } from '../context/DataContext';
import { convertValue, getUnitType } from '../utils/unitConversion';
import { Download, ArrowLeft, RotateCcw, ZoomIn } from 'lucide-react';

export const EditModeDraggable: React.FC = () => {
    const navigate = useNavigate();
    const { data, selectedY, unitPrefs } = useData();
    const plotRef = useRef<HTMLDivElement>(null);

    const [modifiedSeries, setModifiedSeries] = useState<Record<string, number[]>>({});
    const [hasChanges, setHasChanges] = useState(false);
    const [editRange, setEditRange] = useState<[number, number]>([0, 100]);
    const [zoomStart, setZoomStart] = useState('0');
    const [zoomEnd, setZoomEnd] = useState('100');

    // Initialize modified series
    useEffect(() => {
        if (data) {
            const initial: Record<string, number[]> = {};
            Object.keys(data.series).forEach(key => {
                initial[key] = [...data.series[key]];
            });
            setModifiedSeries(initial);
            setEditRange([0, Math.min(100, data.time.length - 1)]);
            setZoomEnd(Math.min(100, data.time.length - 1).toString());
        }
    }, [data]);

    // Create and update plot
    useEffect(() => {
        if (!plotRef.current || !data || selectedY.length === 0 || Object.keys(modifiedSeries).length === 0) return;

        const [start, end] = editRange;
        const rangeSize = end - start + 1;
        const maxDisplayPoints = 500;
        const step = Math.max(1, Math.floor(rangeSize / maxDisplayPoints));

        const xData: number[] = [];
        const displayIndices: number[] = [];

        for (let i = start; i <= end; i += step) {
            xData.push(convertValue(data.time[i], 'time', unitPrefs.time));
            displayIndices.push(i);
        }

        const traces = selectedY.map(yKey => {
            const type = getUnitType(yKey);
            const targetUnit = unitPrefs[type];

            if (!modifiedSeries[yKey]) {
                return {
                    x: xData,
                    y: [],
                    type: 'scatter' as const,
                    mode: 'lines+markers' as const,
                    name: targetUnit ? `${yKey} (${targetUnit})` : yKey,
                    marker: { size: 12, line: { width: 2, color: 'white' } },
                    line: { width: 2 },
                };
            }

            const yData = displayIndices.map(i =>
                convertValue(modifiedSeries[yKey][i], type, targetUnit)
            );

            return {
                x: xData,
                y: yData,
                type: 'scatter' as const,
                mode: 'lines+markers' as const,
                name: targetUnit ? `${yKey} (${targetUnit})` : yKey,
                marker: { size: 12, line: { width: 2, color: 'white' } },
                line: { width: 2 },
            };
        });

        const layout = {
            autosize: true,
            title: {
                text: `Edit Mode - Click and hold points, then drag vertically to edit values`,
                font: { size: 14 }
            },
            xaxis: {
                title: { text: `Time (${unitPrefs.time})` },
                showgrid: true,
                fixedrange: false,
            },
            yaxis: {
                title: { text: 'Value' },
                showgrid: true,
                fixedrange: false,
            },
            showlegend: true,
            legend: { orientation: 'h' as const, y: -0.15 },
            margin: { l: 60, r: 20, t: 60, b: 80 },
            hovermode: 'closest' as const,
            dragmode: false as const, // Disable pan to allow point dragging
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            editable: true,
            modeBarButtonsToAdd: ['pan2d', 'select2d', 'lasso2d'] as any,
        };

        Plotly.react(plotRef.current, traces, layout, config);

        // Custom point dragging implementation
        const plotElement = plotRef.current as any;
        let isDragging = false;
        let draggedPoint: { traceIndex: number; pointIndex: number; seriesKey: string } | null = null;
        let startY = 0;
        let startValue = 0;

        const handleMouseDown = (event: any) => {
            if (event.points && event.points.length > 0) {
                const point = event.points[0];
                const traceIndex = point.curveNumber;
                const pointIndex = point.pointIndex;
                const seriesKey = selectedY[traceIndex];

                if (seriesKey) {
                    isDragging = true;
                    draggedPoint = { traceIndex, pointIndex, seriesKey };
                    startY = event.event.clientY;

                    const actualIndex = displayIndices[pointIndex];
                    const type = getUnitType(seriesKey);
                    const targetUnit = unitPrefs[type];
                    startValue = convertValue(modifiedSeries[seriesKey][actualIndex], type, targetUnit);

                    console.log('Started dragging point:', { seriesKey, pointIndex: actualIndex, startValue });
                }
            }
        };

        const handleMouseMove = (event: MouseEvent) => {
            if (!isDragging || !draggedPoint || !plotElement._fullLayout) return;

            const deltaY = startY - event.clientY;
            const yaxis = plotElement._fullLayout.yaxis;

            // Calculate the value change based on pixel movement
            const yRange = yaxis.range[1] - yaxis.range[0];
            const plotHeight = plotElement.clientHeight - layout.margin.t - layout.margin.b;
            const valuePerPixel = yRange / plotHeight;
            const deltaValue = deltaY * valuePerPixel;

            const newValue = startValue + deltaValue;
            const actualIndex = displayIndices[draggedPoint.pointIndex];

            // Update the value
            const type = getUnitType(draggedPoint.seriesKey);
            const targetUnit = unitPrefs[type];
            const scale = targetUnit === 'ms' ? 1000 :
                targetUnit === 'mA' ? 1000 :
                    targetUnit === 'uA' ? 1000000 :
                        targetUnit === 'cm' ? 0.1 :
                            targetUnit === 'm' ? 0.001 :
                                targetUnit === 'mOhm' ? 0.001 :
                                    targetUnit === 'Ohm' ? 0.000001 : 1;

            const baseValue = newValue / scale;

            setModifiedSeries(prev => {
                if (!draggedPoint) return prev; // Safety check
                const newSeries = { ...prev };
                newSeries[draggedPoint.seriesKey] = [...newSeries[draggedPoint.seriesKey]];
                newSeries[draggedPoint.seriesKey][actualIndex] = baseValue;
                return newSeries;
            });
            setHasChanges(true);
        };

        const handleMouseUp = () => {
            if (isDragging) {
                console.log('Stopped dragging');
                isDragging = false;
                draggedPoint = null;
            }
        };

        // Attach event listeners
        plotElement.on('plotly_click', handleMouseDown);
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);

        // Cleanup function
        return () => {
            if (plotRef.current) {
                const element = plotRef.current as any;
                if (element.removeAllListeners) {
                    element.removeAllListeners('plotly_click');
                }
            }
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };

    }, [data, selectedY, modifiedSeries, editRange, unitPrefs, hasChanges]);

    const handleApplyZoom = () => {
        if (!data) return;
        const start = Math.max(0, parseInt(zoomStart) || 0);
        const end = Math.min(data.time.length - 1, parseInt(zoomEnd) || 100);
        if (start < end) {
            setEditRange([start, end]);
        }
    };

    const handleSmooth = () => {
        if (!data || selectedY.length === 0) return;
        const [start, end] = editRange;

        setModifiedSeries(prev => {
            const newSeries = { ...prev };
            selectedY.forEach(seriesKey => {
                const series = [...newSeries[seriesKey]];
                for (let i = start + 1; i < end; i++) {
                    const avg = (series[i - 1] + series[i] + series[i + 1]) / 3;
                    series[i] = avg;
                }
                newSeries[seriesKey] = series;
            });
            return newSeries;
        });
        setHasChanges(true);
    };

    const handleReset = () => {
        if (data) {
            const reset: Record<string, number[]> = {};
            Object.keys(data.series).forEach(key => {
                reset[key] = [...data.series[key]];
            });
            setModifiedSeries(reset);
            setHasChanges(false);
        }
    };

    const handleExport = () => {
        if (!data) return;

        // Build CSV content in Hyderabad format
        let csv = '';

        // Add metadata if present (without "METADATA" header, matching Hyderabad format)
        if (Object.keys(data.metadata).length > 0) {
            Object.entries(data.metadata).forEach(([key, value]) => {
                csv += `${key},${value},\r\n`;
            });
            csv += '\r\n';
        }

        // Add column headers with separator (matching Hyderabad format)
        const seriesKeys = Object.keys(modifiedSeries);
        const headers = [...seriesKeys];
        csv += headers.join(',') + ', ,' + '\r\n';  // Add separator column

        // Add all data rows
        for (let i = 0; i < data.time.length; i++) {
            const row: string[] = [];

            // Add all series values
            seriesKeys.forEach(key => {
                row.push((modifiedSeries[key][i]?.toFixed(3) || '0.000'));
            });

            // Add data row with separator column and time
            csv += row.join(',') + ` ,${data.time[i].toFixed(2)},` + '\r\n';
        }

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dcrm_modified_${new Date().getTime()}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    if (!data) {
        return (
            <div className="flex items-center justify-center h-screen bg-slate-100">
                <div className="text-center">
                    <p className="text-slate-600 mb-4">No data loaded. Please load a file first.</p>
                    <button
                        onClick={() => navigate('/')}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                        Go Back to Viewer
                    </button>
                </div>
            </div>
        );
    }

    if (selectedY.length === 0) {
        return (
            <div className="flex items-center justify-center h-screen bg-slate-100">
                <div className="text-center">
                    <p className="text-slate-600 mb-4">Please select at least one series to edit.</p>
                    <button
                        onClick={() => navigate('/')}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                        Go Back to Viewer
                    </button>
                </div>
            </div>
        );
    }

    if (Object.keys(modifiedSeries).length === 0) {
        return (
            <div className="flex items-center justify-center h-screen bg-slate-100">
                <div className="text-center">
                    <p className="text-slate-600">Loading data...</p>
                </div>
            </div>
        );
    }

    const [start, end] = editRange;
    const rangeSize = end - start + 1;

    return (
        <div className="flex flex-col h-screen bg-slate-100">
            <header className="h-16 bg-white border-b border-slate-200 flex items-center px-6 justify-between flex-shrink-0 shadow-sm">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-2 px-3 py-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        Back to Viewer
                    </button>
                    <h1 className="text-xl font-bold text-slate-800">Edit Mode (Draggable)</h1>
                    {hasChanges && (
                        <span className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded-full">
                            Modified
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleSmooth}
                        className="flex items-center gap-2 px-4 py-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                        Smooth
                    </button>
                    <button
                        onClick={handleReset}
                        disabled={!hasChanges}
                        className="flex items-center gap-2 px-4 py-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <RotateCcw className="w-4 h-4" />
                        Reset
                    </button>
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors shadow-sm"
                    >
                        <Download className="w-4 h-4" />
                        Export CSV
                    </button>
                </div>
            </header>

            <div className="mx-6 mt-4 p-4 bg-white border border-slate-200 rounded-lg shadow-sm">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <ZoomIn className="w-5 h-5 text-slate-600" />
                        <span className="font-semibold text-slate-700">Zoom to Range:</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <label className="text-sm text-slate-600">Start Index:</label>
                        <input
                            type="number"
                            value={zoomStart}
                            onChange={(e) => setZoomStart(e.target.value)}
                            className="w-24 px-3 py-1 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            min="0"
                            max={data.time.length - 1}
                        />
                    </div>
                    <div className="flex items-center gap-2">
                        <label className="text-sm text-slate-600">End Index:</label>
                        <input
                            type="number"
                            value={zoomEnd}
                            onChange={(e) => setZoomEnd(e.target.value)}
                            className="w-24 px-3 py-1 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            min="0"
                            max={data.time.length - 1}
                        />
                    </div>
                    <button
                        onClick={handleApplyZoom}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        Apply Zoom
                    </button>
                    <div className="text-sm text-slate-500">
                        Showing {rangeSize} points
                    </div>
                </div>
            </div>

            <div className="mx-6 mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-semibold text-blue-900 mb-2">How to Edit:</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                    <li>• <strong>Click on any point</strong> to select it, then <strong>drag up or down</strong> to change its value</li>
                    <li>• <strong>Release the mouse</strong> to finish editing that point</li>
                    <li>• <strong>Zoom to a specific range</strong> using the controls above for easier editing</li>
                    <li>• <strong>Use the Pan tool</strong> in the toolbar to navigate without editing</li>
                    <li>• <strong>Click "Smooth"</strong> to apply smoothing to the visible range</li>
                    <li>• <strong>Click "Reset"</strong> to restore original values</li>
                    <li>• <strong>Click "Export CSV"</strong> to download ALL modified data</li>
                </ul>
            </div>

            <div className="flex-1 p-6">
                <div
                    ref={plotRef}
                    className="w-full h-full bg-white rounded-xl shadow-sm border border-slate-200 p-4 cursor-crosshair"
                />
            </div>
        </div>
    );
};
