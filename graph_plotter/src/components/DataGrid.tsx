import React from 'react';
import { useData } from '../context/DataContext';
import { getUnitType, convertValue } from '../utils/unitConversion';

export const DataGrid: React.FC = () => {
    const { data, range, unitPrefs } = useData();

    if (!data) return null;

    const start = range[0];
    const end = Math.min(range[1] + 1, start + 100); // Show max 100 rows for performance
    const rows = [];

    for (let i = start; i < end; i++) {
        rows.push(i);
    }

    const headers = ['Time', ...Object.keys(data.series)];

    return (
        <div className="h-64 overflow-auto bg-white border-t border-slate-200">
            <table className="w-full text-xs text-left whitespace-nowrap">
                <thead className="bg-slate-50 sticky top-0 z-10">
                    <tr>
                        {headers.map(h => {
                            const type = getUnitType(h);
                            const unit = unitPrefs[type];
                            return (
                                <th key={h} className="p-2 font-semibold text-slate-600 border-b border-slate-200">
                                    {h.toUpperCase()} {unit && `(${unit})`}
                                </th>
                            );
                        })}
                    </tr>
                </thead>
                <tbody>
                    {rows.map(idx => (
                        <tr key={idx} className="hover:bg-slate-50 border-b border-slate-100">
                            <td className="p-2 font-mono text-slate-600">
                                {convertValue(data.time[idx], 'time', unitPrefs.time).toFixed(4)}
                            </td>
                            {Object.keys(data.series).map(key => {
                                const type = getUnitType(key);
                                const val = data.series[key][idx];
                                const converted = convertValue(val, type, unitPrefs[type]);
                                return (
                                    <td key={key} className="p-2 font-mono text-slate-600">
                                        {converted.toFixed(3)}
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>
            <div className="p-2 text-xs text-slate-400 text-center bg-slate-50 border-t border-slate-200">
                Showing rows {start} to {end - 1} (of {data.time.length})
            </div>
        </div>
    );
};
