import React from 'react';
import { useData } from '../context/DataContext';
import { ChevronDown, ChevronRight, Settings, Activity, Zap, Move, Layers, Download, Ruler } from 'lucide-react';
import Papa from 'papaparse';
import { UNITS } from '../utils/unitConversion';

const Section: React.FC<{ title: string; icon: React.ReactNode; children: React.ReactNode }> = ({ title, icon, children }) => {
    const [isOpen, setIsOpen] = React.useState(true);
    return (
        <div className="mb-4 border border-slate-200 rounded-lg overflow-hidden">
            <button
                className="w-full flex items-center justify-between p-3 bg-slate-50 hover:bg-slate-100 transition-colors"
                onClick={() => setIsOpen(!isOpen)}
            >
                <div className="flex items-center gap-2 font-medium text-slate-700">
                    {icon}
                    {title}
                </div>
                {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
            {isOpen && <div className="p-3 bg-white">{children}</div>}
        </div>
    );
};

export const ControlPanel: React.FC = () => {
    const {
        data, data2, fileLabels,
        selectedY, setSelectedY,
        selectedY2, setSelectedY2,
        selectedX, setSelectedX,
        xAxisSource, setXAxisSource,
        range, setRange,
        showGrid, setShowGrid,
        showLegend, setShowLegend,
        unitPrefs, setUnitPrefs
    } = useData();

    const hasAnyData = data !== null || data2 !== null;
    if (!hasAnyData) return <div className="p-4 text-slate-400">Load files to see controls</div>;

    // X-axis options from the selected source
    const sourceData = xAxisSource === 'file1' ? data : data2;
    const xOptions = sourceData ? ['Time', 'Index', ...Object.keys(sourceData.series)] : ['Time', 'Index'];

    const handleExportCSV = () => {
        if (!data && !data2) return;

        const start = range[0];
        const end = range[1] + 1;

        // Export combined data from both files
        const exportData: any[] = [];
        const maxLength = Math.max(data?.time.length || 0, data2?.time.length || 0);

        for (let i = start; i < Math.min(end, maxLength); i++) {
            const row: Record<string, any> = {};

            if (data && i < data.time.length) {
                row[`${fileLabels.file1}_Time`] = data.time[i];
                Object.keys(data.series).forEach(key => {
                    row[`${fileLabels.file1}_${key}`] = data.series[key][i];
                });
            }

            if (data2 && i < data2.time.length) {
                row[`${fileLabels.file2}_Time`] = data2.time[i];
                Object.keys(data2.series).forEach(key => {
                    row[`${fileLabels.file2}_${key}`] = data2.series[key][i];
                });
            }

            exportData.push(row);
        }

        const csv = Papa.unparse(exportData);
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'dcrm_comparison_export.csv');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const toggleY = (key: string) => {
        if (selectedY.includes(key)) {
            setSelectedY(selectedY.filter(k => k !== key));
        } else {
            setSelectedY([...selectedY, key]);
        }
    };

    const toggleY2 = (key: string) => {
        if (selectedY2.includes(key)) {
            setSelectedY2(selectedY2.filter(k => k !== key));
        } else {
            setSelectedY2([...selectedY2, key]);
        }
    };

    const renderCheckbox = (key: string, isFile1: boolean) => {
        const isSelected = isFile1 ? selectedY.includes(key) : selectedY2.includes(key);
        const toggle = isFile1 ? toggleY : toggleY2;
        const color = isFile1 ? 'text-blue-600' : 'text-green-600';
        const hoverColor = isFile1 ? 'hover:text-blue-600' : 'hover:text-green-600';
        const checkboxColor = isFile1 ? 'text-blue-600 focus:ring-blue-500' : 'text-green-600 focus:ring-green-500';

        return (
            <label key={key} className={`flex items-center gap-2 mb-1 cursor-pointer ${hoverColor}`}>
                <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggle(key)}
                    className={`rounded ${checkboxColor}`}
                />
                <span className="text-sm truncate" title={key}>{key}</span>
            </label>
        );
    };

    return (
        <div className="h-full overflow-y-auto p-4 bg-white border-r border-slate-200 w-80 flex-shrink-0">
            <h2 className="text-xl font-bold text-slate-800 mb-6">Controls</h2>

            {/* X-Axis Source Selection */}
            <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-2">X-Axis Source</label>
                <div className="flex gap-2 mb-2">
                    <button
                        onClick={() => setXAxisSource('file1')}
                        disabled={!data}
                        className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${xAxisSource === 'file1'
                                ? 'bg-blue-600 text-white'
                                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                            } ${!data ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        📘 File 1
                    </button>
                    <button
                        onClick={() => setXAxisSource('file2')}
                        disabled={!data2}
                        className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${xAxisSource === 'file2'
                                ? 'bg-green-600 text-white'
                                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                            } ${!data2 ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        📗 File 2
                    </button>
                </div>
                <select
                    value={selectedX}
                    onChange={(e) => setSelectedX(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-md text-sm bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none"
                >
                    {xOptions.map(opt => (
                        <option key={opt} value={opt}>{opt}</option>
                    ))}
                </select>
            </div>

            <Section title="Graph Options" icon={<Settings size={18} />}>
                <label className="flex items-center gap-2 mb-2 cursor-pointer">
                    <input type="checkbox" checked={showGrid} onChange={e => setShowGrid(e.target.checked)} />
                    <span className="text-sm">Show Grid</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={showLegend} onChange={e => setShowLegend(e.target.checked)} />
                    <span className="text-sm">Show Legend</span>
                </label>
            </Section>

            <Section title="Unit Settings" icon={<Ruler size={18} />}>
                <div className="grid grid-cols-2 gap-2">
                    <div>
                        <label className="block text-xs text-slate-500 mb-1">Current</label>
                        <select
                            value={unitPrefs.current}
                            onChange={e => setUnitPrefs({ ...unitPrefs, current: e.target.value })}
                            className="w-full text-xs p-1 border rounded"
                        >
                            {UNITS.current.map(u => <option key={u} value={u}>{u}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs text-slate-500 mb-1">Travel</label>
                        <select
                            value={unitPrefs.travel}
                            onChange={e => setUnitPrefs({ ...unitPrefs, travel: e.target.value })}
                            className="w-full text-xs p-1 border rounded"
                        >
                            {UNITS.travel.map(u => <option key={u} value={u}>{u}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs text-slate-500 mb-1">Resistance</label>
                        <select
                            value={unitPrefs.resistance}
                            onChange={e => setUnitPrefs({ ...unitPrefs, resistance: e.target.value })}
                            className="w-full text-xs p-1 border rounded"
                        >
                            {UNITS.resistance.map(u => <option key={u} value={u}>{u}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs text-slate-500 mb-1">Time</label>
                        <select
                            value={unitPrefs.time}
                            onChange={e => setUnitPrefs({ ...unitPrefs, time: e.target.value })}
                            className="w-full text-xs p-1 border rounded"
                        >
                            {UNITS.time.map(u => <option key={u} value={u}>{u}</option>)}
                        </select>
                    </div>
                </div>
            </Section>

            <Section title="Data Range" icon={<Activity size={18} />}>
                <div className="flex flex-col gap-2">
                    <div className="flex justify-between text-xs text-slate-500">
                        <span>Start: {range[0]}</span>
                        <span>End: {range[1]}</span>
                    </div>
                    <input
                        type="range"
                        min={0}
                        max={Math.max((data?.time.length || 1) - 1, (data2?.time.length || 1) - 1)}
                        value={range[0]}
                        onChange={e => {
                            const val = parseInt(e.target.value);
                            if (val < range[1]) setRange([val, range[1]]);
                        }}
                        className="w-full"
                    />
                    <input
                        type="range"
                        min={0}
                        max={Math.max((data?.time.length || 1) - 1, (data2?.time.length || 1) - 1)}
                        value={range[1]}
                        onChange={e => {
                            const val = parseInt(e.target.value);
                            if (val > range[0]) setRange([range[0], val]);
                        }}
                        className="w-full"
                    />
                    <button
                        className="mt-2 text-xs text-blue-600 hover:underline"
                        onClick={() => setRange([0, Math.max((data?.time.length || 1) - 1, (data2?.time.length || 1) - 1)])}
                    >
                        Reset Range
                    </button>
                </div>
                <button
                    onClick={handleExportCSV}
                    className="mt-4 w-full flex items-center justify-center gap-2 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-sm transition-colors"
                >
                    <Download size={16} />
                    Export CSV
                </button>
            </Section>

            {/* File 1 Parameters */}
            {data && (
                <>
                    <div className="mb-2 p-2 bg-blue-50 rounded-md border border-blue-200">
                        <h3 className="text-sm font-bold text-blue-700">📘 {fileLabels.file1} Parameters</h3>
                    </div>

                    {data.groups.coilCurrents.length > 0 && (
                        <Section title="Coil Currents" icon={<Zap size={18} />}>
                            {data.groups.coilCurrents.map(key => renderCheckbox(key, true))}
                        </Section>
                    )}

                    {data.groups.contactTravel.length > 0 && (
                        <Section title="Contact Travel" icon={<Move size={18} />}>
                            {data.groups.contactTravel.map(key => renderCheckbox(key, true))}
                        </Section>
                    )}

                    {data.groups.dcrmResistance.length > 0 && (
                        <Section title="DCRM Resistance" icon={<Layers size={18} />}>
                            {data.groups.dcrmResistance.map(key => renderCheckbox(key, true))}
                        </Section>
                    )}

                    {data.groups.dcrmCurrent.length > 0 && (
                        <Section title="DCRM Current" icon={<Activity size={18} />}>
                            {data.groups.dcrmCurrent.map(key => renderCheckbox(key, true))}
                        </Section>
                    )}

                    {data.groups.others.length > 0 && (
                        <Section title="Other Channels" icon={<Activity size={18} />}>
                            {data.groups.others.map(key => renderCheckbox(key, true))}
                        </Section>
                    )}
                </>
            )}

            {/* File 2 Parameters */}
            {data2 && (
                <>
                    <div className="mb-2 p-2 bg-green-50 rounded-md border border-green-200 mt-4">
                        <h3 className="text-sm font-bold text-green-700">📗 {fileLabels.file2} Parameters</h3>
                    </div>

                    {data2.groups.coilCurrents.length > 0 && (
                        <Section title="Coil Currents" icon={<Zap size={18} />}>
                            {data2.groups.coilCurrents.map(key => renderCheckbox(key, false))}
                        </Section>
                    )}

                    {data2.groups.contactTravel.length > 0 && (
                        <Section title="Contact Travel" icon={<Move size={18} />}>
                            {data2.groups.contactTravel.map(key => renderCheckbox(key, false))}
                        </Section>
                    )}

                    {data2.groups.dcrmResistance.length > 0 && (
                        <Section title="DCRM Resistance" icon={<Layers size={18} />}>
                            {data2.groups.dcrmResistance.map(key => renderCheckbox(key, false))}
                        </Section>
                    )}

                    {data2.groups.dcrmCurrent.length > 0 && (
                        <Section title="DCRM Current" icon={<Activity size={18} />}>
                            {data2.groups.dcrmCurrent.map(key => renderCheckbox(key, false))}
                        </Section>
                    )}

                    {data2.groups.others.length > 0 && (
                        <Section title="Other Channels" icon={<Activity size={18} />}>
                            {data2.groups.others.map(key => renderCheckbox(key, false))}
                        </Section>
                    )}
                </>
            )}
        </div>
    );
};
