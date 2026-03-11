import React, { useCallback, useState } from 'react';
import { UploadCloud, X, FileCheck, ArrowRight } from 'lucide-react';
import { parseDCRMFile } from '../utils/dataParser';
import { useData } from '../context/DataContext';
import type { DCRMData } from '../utils/dataParser';

interface FileSlot {
    file: File | null;
    data: DCRMData | null;
    name: string;
}

export const FileUpload: React.FC = () => {
    const { setData, setData2, setSelectedY, setSelectedY2, setRange, setFileLabels } = useData();
    const [file1, setFile1] = useState<FileSlot>({ file: null, data: null, name: '' });
    const [file2, setFile2] = useState<FileSlot>({ file: null, data: null, name: '' });
    const [isProcessing, setIsProcessing] = useState(false);

    const handleFile = async (file: File, slot: 1 | 2) => {
        try {
            const parsedData = await parseDCRMFile(file);

            if (slot === 1) {
                setFile1({ file, data: parsedData, name: file.name });
            } else {
                setFile2({ file, data: parsedData, name: file.name });
            }
        } catch (err) {
            console.error(`Error parsing file ${slot}:`, err);
            alert(`Failed to parse File ${slot}. Please check the format.`);
        }
    };

    const handleContinue = () => {
        if (!file1.data && !file2.data) {
            alert('Please upload at least one file to continue.');
            return;
        }

        setIsProcessing(true);

        // Apply File 1
        if (file1.data) {
            setData(file1.data);
            setFileLabels(prev => ({ ...prev, file1: file1.name }));
            const defaultY = file1.data.groups.coilCurrents.length > 0
                ? [file1.data.groups.coilCurrents[0]]
                : [Object.keys(file1.data.series)[0]];
            setSelectedY(defaultY);
            setRange([0, file1.data.time.length - 1]);
        } else {
            setData(null);
            setSelectedY([]);
        }

        // Apply File 2
        if (file2.data) {
            setData2(file2.data);
            setFileLabels(prev => ({ ...prev, file2: file2.name }));
            const defaultY = file2.data.groups.coilCurrents.length > 0
                ? [file2.data.groups.coilCurrents[0]]
                : [Object.keys(file2.data.series)[0]];
            setSelectedY2(defaultY);
        } else {
            setData2(null);
            setSelectedY2([]);
        }

        setIsProcessing(false);
    };

    const clearFile = (slot: 1 | 2) => {
        if (slot === 1) {
            setFile1({ file: null, data: null, name: '' });
        } else {
            setFile2({ file: null, data: null, name: '' });
        }
    };

    const FileUploadSlot: React.FC<{
        slot: 1 | 2;
        fileSlot: FileSlot;
        onFileSelect: (file: File) => void;
        onClear: () => void;
    }> = ({ slot, fileSlot, onFileSelect, onClear }) => {
        const bgColor = slot === 1 ? 'bg-blue-50 border-blue-300' : 'bg-green-50 border-green-300';
        const textColor = slot === 1 ? 'text-blue-700' : 'text-green-700';
        const buttonColor = slot === 1 ? 'bg-blue-600 hover:bg-blue-700' : 'bg-green-600 hover:bg-green-700';
        const icon = slot === 1 ? '📘' : '📗';

        const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
            if (e.target.files && e.target.files[0]) {
                onFileSelect(e.target.files[0]);
            }
        };

        const onDrop = (e: React.DragEvent) => {
            e.preventDefault();
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                onFileSelect(e.dataTransfer.files[0]);
            }
        };

        return (
            <div
                className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl transition-colors ${bgColor}`}
                onDrop={onDrop}
                onDragOver={(e) => e.preventDefault()}
            >
                {fileSlot.data && (
                    <button
                        onClick={onClear}
                        className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
                        title="Clear file"
                    >
                        <X size={16} />
                    </button>
                )}

                {fileSlot.data ? (
                    <>
                        <FileCheck className={`w-10 h-10 mb-3 ${textColor}`} />
                        <p className={`text-sm font-bold ${textColor} mb-2`}>{icon} File {slot} Loaded</p>
                        <p className="text-xs text-slate-700 text-center px-2 break-all font-medium">{fileSlot.name}</p>
                        <p className="text-xs text-slate-500 mt-1">{fileSlot.data.time.length} data points</p>
                    </>
                ) : (
                    <>
                        <UploadCloud className="w-10 h-10 text-slate-400 mb-3" />
                        <p className={`text-base font-bold ${textColor} mb-1`}>{icon} File {slot}</p>
                        <p className="text-sm text-slate-500 mb-3">Drag & drop CSV here</p>
                        <input
                            type="file"
                            accept=".csv,.xlsx,.xls"
                            className="hidden"
                            id={`file-upload-${slot}`}
                            onChange={onChange}
                        />
                        <label
                            htmlFor={`file-upload-${slot}`}
                            className={`px-4 py-2 ${buttonColor} text-white rounded-md transition-colors cursor-pointer text-sm font-medium`}
                        >
                            Choose File
                        </label>
                    </>
                )}
            </div>
        );
    };

    return (
        <div className="w-full max-w-4xl space-y-6">
            <div className="text-center">
                <h2 className="text-2xl font-bold text-slate-800 mb-2">Upload Files for Comparison</h2>
                <p className="text-sm text-slate-600">Upload up to 2 CSV files to compare their data</p>
            </div>

            {/* File Upload Slots */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <FileUploadSlot
                    slot={1}
                    fileSlot={file1}
                    onFileSelect={(file) => handleFile(file, 1)}
                    onClear={() => clearFile(1)}
                />
                <FileUploadSlot
                    slot={2}
                    fileSlot={file2}
                    onFileSelect={(file) => handleFile(file, 2)}
                    onClear={() => clearFile(2)}
                />
            </div>

            {/* Continue Button */}
            {(file1.data || file2.data) && (
                <div className="flex justify-center">
                    <button
                        onClick={handleContinue}
                        disabled={isProcessing}
                        className="flex items-center gap-3 px-8 py-3 bg-gradient-to-r from-blue-600 to-green-600 text-white rounded-lg hover:from-blue-700 hover:to-green-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed font-bold text-lg"
                    >
                        {isProcessing ? (
                            <>Processing...</>
                        ) : (
                            <>
                                Continue to Analysis
                                <ArrowRight className="w-5 h-5" />
                            </>
                        )}
                    </button>
                </div>
            )}

            {/* Helper Text */}
            {!file1.data && !file2.data && (
                <p className="text-center text-sm text-slate-500 italic">
                    Upload at least one file to begin
                </p>
            )}
        </div>
    );
};
