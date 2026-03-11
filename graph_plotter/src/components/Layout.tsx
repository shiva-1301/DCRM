import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit3 } from 'lucide-react';
import { ControlPanel } from './ControlPanel';
import { GraphViewer } from './GraphViewer';
import { DataGrid } from './DataGrid';
import { FileUpload } from './FileUpload';
import { StatsPanel } from './StatsPanel';
import { MetadataPanel } from './MetadataPanel';
import { useData } from '../context/DataContext';

export const Layout: React.FC = () => {
    const { data, data2, selectedY, selectedY2, fileLabels } = useData();
    const navigate = useNavigate();

    const hasAnyData = data !== null || data2 !== null;
    const hasAnySelection = selectedY.length > 0 || selectedY2.length > 0;

    return (
        <div className="flex h-screen w-screen bg-slate-100 overflow-hidden">
            {/* Sidebar */}
            <ControlPanel />

            {/* Main Content */}
            <div className="flex-1 flex flex-col h-full overflow-hidden">

                {/* Header / Top Bar */}
                <header className="h-14 bg-white border-b border-slate-200 flex items-center px-6 justify-between flex-shrink-0">
                    <h1 className="text-lg font-bold text-slate-800">DCRM Viewer - Comparison Mode</h1>
                    <div className="flex items-center gap-4">
                        {!hasAnyData && <div className="text-sm text-slate-500">No files loaded</div>}
                        {data && (
                            <div className="text-sm text-blue-600 font-medium">
                                📘 {fileLabels.file1} ({data.time.length} rows)
                            </div>
                        )}
                        {data2 && (
                            <div className="text-sm text-green-600 font-medium">
                                📗 {fileLabels.file2} ({data2.time.length} rows)
                            </div>
                        )}
                        {hasAnyData && hasAnySelection && (
                            <button
                                onClick={() => navigate('/edit')}
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
                            >
                                <Edit3 className="w-4 h-4" />
                                Edit Mode
                            </button>
                        )}
                    </div>
                </header>

                {/* Scrollable Content Area */}
                <div className="flex-1 overflow-y-auto p-4">
                    {!hasAnyData ? (
                        <div className="h-full flex flex-col items-center justify-center">
                            <FileUpload />
                        </div>
                    ) : (
                        <div className="flex flex-col h-full gap-4">
                            <MetadataPanel />
                            <StatsPanel />
                            <div className="flex-1 min-h-[400px]">
                                <GraphViewer />
                            </div>
                        </div>
                    )}
                </div>

                {/* Bottom Panel */}
                {hasAnyData && (
                    <div className="h-64 flex-shrink-0 border-t border-slate-200 bg-white">
                        <DataGrid />
                    </div>
                )}
            </div>
        </div>
    );
};

