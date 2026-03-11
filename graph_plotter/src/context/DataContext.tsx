import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type { DCRMData } from '../utils/dataParser';

interface DataContextType {
    // File 1 data
    data: DCRMData | null;
    setData: (data: DCRMData | null) => void;
    // File 2 data
    data2: DCRMData | null;
    setData2: (data: DCRMData | null) => void;
    // File labels
    fileLabels: { file1: string; file2: string };
    setFileLabels: (labels: { file1: string; file2: string }) => void;
    // X-axis selection
    selectedX: string;
    setSelectedX: (x: string) => void;
    xAxisSource: 'file1' | 'file2';
    setXAxisSource: (source: 'file1' | 'file2') => void;
    // Y-axis selections from both files
    selectedY: string[];
    setSelectedY: (y: string[]) => void;
    selectedY2: string[];
    setSelectedY2: (y: string[]) => void;
    // Shared settings
    range: [number, number]; // Row indices
    setRange: (range: [number, number]) => void;
    showGrid: boolean;
    setShowGrid: (show: boolean) => void;
    showLegend: boolean;
    setShowLegend: (show: boolean) => void;
    unitPrefs: Record<string, string>;
    setUnitPrefs: (prefs: Record<string, string>) => void;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [data, setData] = useState<DCRMData | null>(null);
    const [data2, setData2] = useState<DCRMData | null>(null);
    const [fileLabels, setFileLabels] = useState<{ file1: string; file2: string }>({
        file1: 'File 1',
        file2: 'File 2'
    });
    const [selectedX, setSelectedX] = useState<string>('Time');
    const [xAxisSource, setXAxisSource] = useState<'file1' | 'file2'>('file1');
    const [selectedY, setSelectedY] = useState<string[]>([]);
    const [selectedY2, setSelectedY2] = useState<string[]>([]);
    const [range, setRange] = useState<[number, number]>([0, 0]);
    const [showGrid, setShowGrid] = useState(true);
    const [showLegend, setShowLegend] = useState(true);
    const [unitPrefs, setUnitPrefs] = useState<Record<string, string>>({
        current: 'A',
        travel: 'mm',
        resistance: 'uOhm',
        time: 'ms'
    });

    return (
        <DataContext.Provider value={{
            data, setData,
            data2, setData2,
            fileLabels, setFileLabels,
            selectedX, setSelectedX,
            xAxisSource, setXAxisSource,
            selectedY, setSelectedY,
            selectedY2, setSelectedY2,
            range, setRange,
            showGrid, setShowGrid,
            showLegend, setShowLegend,
            unitPrefs, setUnitPrefs
        }}>
            {children}
        </DataContext.Provider>
    );
};

export const useData = () => {
    const context = useContext(DataContext);
    if (!context) {
        throw new Error('useData must be used within a DataProvider');
    }
    return context;
};
