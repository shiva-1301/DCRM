import React from 'react';
import { useData } from '../context/DataContext';
import { Database } from 'lucide-react';

export const MetadataPanel: React.FC = () => {
    const { data, data2, fileLabels } = useData();

    if (!data && !data2) {
        return null;
    }

    if (!data?.metadata && !data2?.metadata) {
        return null;
    }

    if (Object.keys(data?.metadata || {}).length === 0 && Object.keys(data2?.metadata || {}).length === 0) {
        return null;
    }

    return (
        <div className="space-y-1">
            <div className="flex items-center gap-2 mb-3 px-1">
                <Database className="w-5 h-5 text-blue-600" />
                <h2 className="text-lg font-bold text-slate-800">Test Metadata</h2>
            </div>

            {/* File 1 Metadata */}
            {data && Object.keys(data.metadata).length > 0 && (
                <div className="border-2 border-blue-200 rounded-lg p-3 mb-4 bg-blue-50">
                    <h3 className="text-sm font-bold text-blue-700 mb-3">📘 {fileLabels.file1}</h3>
                    <div className="space-y-2">
                        {Object.entries(data.metadata).slice(0, 6).map(([key, value]) => (
                            <div key={key} className="flex justify-between text-xs">
                                <span className="text-slate-600 font-medium">{key}:</span>
                                <span className="text-slate-800">{value}</span>
                            </div>
                        ))}
                        {Object.keys(data.metadata).length > 6 && (
                            <div className="text-xs text-blue-600 italic">
                                + {Object.keys(data.metadata).length - 6} more fields
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* File 2 Metadata */}
            {data2 && Object.keys(data2.metadata).length > 0 && (
                <div className="border-2 border-green-200 rounded-lg p-3 bg-green-50">
                    <h3 className="text-sm font-bold text-green-700 mb-3">📗 {fileLabels.file2}</h3>
                    <div className="space-y-2">
                        {Object.entries(data2.metadata).slice(0, 6).map(([key, value]) => (
                            <div key={key} className="flex justify-between text-xs">
                                <span className="text-slate-600 font-medium">{key}:</span>
                                <span className="text-slate-800">{value}</span>
                            </div>
                        ))}
                        {Object.keys(data2.metadata).length > 6 && (
                            <div className="text-xs text-green-600 italic">
                                + {Object.keys(data2.metadata).length - 6} more fields
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

