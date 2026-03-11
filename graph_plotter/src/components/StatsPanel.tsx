import React from 'react';
import { useData } from '../context/DataContext';
import { getUnitType, convertValue } from '../utils/unitConversion';

export const StatsPanel: React.FC = () => {
    const { data, selectedY, range, unitPrefs } = useData();

    if (!data || selectedY.length === 0) return null;

    const start = range[0];
    const end = range[1] + 1;

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {selectedY.map(key => {
                const rawSeries = data.series[key]?.slice(start, end) || [];
                if (rawSeries.length === 0) return null;

                const type = getUnitType(key);
                const targetUnit = unitPrefs[type];
                const series = rawSeries.map(v => convertValue(v, type, targetUnit));

                const min = Math.min(...series);
                const max = Math.max(...series);
                const avg = series.reduce((a, b) => a + b, 0) / series.length;

                return (
                    <div key={key} className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                        <div className="text-xs text-slate-500 font-medium truncate mb-1" title={key}>
                            {key} {targetUnit && `(${targetUnit})`}
                        </div>
                        <div className="flex justify-between items-end">
                            <div>
                                <div className="text-xs text-slate-400">Max</div>
                                <div className="font-mono font-bold text-slate-700">{max.toFixed(2)}</div>
                            </div>
                            <div className="text-right">
                                <div className="text-xs text-slate-400">Min / Avg</div>
                                <div className="font-mono text-slate-600">
                                    {min.toFixed(2)} / <span className="text-slate-400">{avg.toFixed(2)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};
