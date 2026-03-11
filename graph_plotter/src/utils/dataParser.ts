import Papa from 'papaparse';

export interface DCRMData {
    metadata: Record<string, string>;
    time: number[];
    series: Record<string, number[]>;
    groups: {
        coilCurrents: string[];
        contactTravel: string[];
        dcrmResistance: string[];
        dcrmCurrent: string[];
        others: string[];
    };
}

/**
 * Detects if the CSV has a metadata header block
 * Returns the row index where the data column headers start
 */
const findDataHeaderRow = (rows: string[][]): number => {
    for (let i = 0; i < Math.min(rows.length, 100); i++) {
        const row = rows[i];
        const rowText = row.join(',').toLowerCase();

        // Look for the characteristic data column headers
        if (rowText.includes('coil current') &&
            rowText.includes('contact travel') &&
            rowText.includes('dcrm')) {
            return i;
        }
    }
    return 0; // Default to first row if not found (old format)
};

/**
 * Extracts metadata from the header block
 */
const extractMetadata = (rows: string[][], headerRowIndex: number): Record<string, string> => {
    const metadata: Record<string, string> = {};

    for (let i = 0; i < headerRowIndex; i++) {
        const row = rows[i];

        // Parse key-value pairs from the header rows
        for (let j = 0; j < row.length; j += 2) {
            const key = row[j]?.trim();
            const value = row[j + 1]?.trim();

            if (key && value && key !== '' && value !== '') {
                // Clean up the key (remove trailing colons and extra spaces)
                const cleanKey = key.replace(/\s*:\s*$/, '').trim();
                if (cleanKey && !cleanKey.match(/^(HEADER|SETTINGS|Velocity Points|Travel Results)$/i)) {
                    metadata[cleanKey] = value;
                }
            }
        }
    }

    return metadata;
};

/**
 * Extract sampling speed from metadata
 * Returns sampling interval in seconds
 */
const getSamplingInterval = (metadata: Record<string, string>): number => {
    // Look for sampling speed in metadata
    const samplingKey = Object.keys(metadata).find(k =>
        k.toLowerCase().includes('sampling speed')
    );

    if (samplingKey) {
        const value = metadata[samplingKey];
        // Parse value like "10" from "Sampling Speed (kC) : 10"
        const match = value.match(/(\d+\.?\d*)/);
        if (match) {
            const samplingSpeedKHz = parseFloat(match[1]);
            // Convert kHz to Hz, then get interval in seconds
            return 1 / (samplingSpeedKHz * 1000);
        }
    }

    // Default: assume 10 kHz if not found
    return 0.0001; // 1/10000 seconds
};

export const parseDCRMFile = (file: File): Promise<DCRMData> => {
    return new Promise((resolve, reject) => {
        Papa.parse(file, {
            header: false,
            skipEmptyLines: 'greedy',
            complete: (results) => {
                try {
                    const rows = results.data as string[][];
                    if (rows.length < 2) {
                        reject(new Error("File is empty or invalid"));
                        return;
                    }

                    // Find where the data headers start
                    const headerRowIndex = findDataHeaderRow(rows);

                    // Extract metadata from rows before the data header
                    const metadata = extractMetadata(rows, headerRowIndex);

                    // Get the column headers
                    let headers = rows[headerRowIndex].map(h => h ? h.trim() : "");

                    // Get data rows (everything after the header row)
                    const dataRows = rows.slice(headerRowIndex + 1);

                    if (dataRows.length === 0) {
                        reject(new Error("No data found"));
                        return;
                    }

                    // Check if this is the new format (with metadata) or old format
                    const hasMetadata = Object.keys(metadata).length > 0;

                    let timeColIndex = -1;
                    let generateTime = false;

                    if (hasMetadata) {
                        // New format: NO time column, generate time from sampling rate
                        generateTime = true;
                    } else {
                        // Old format: check for time column
                        const firstColData = dataRows
                            .slice(0, Math.min(100, dataRows.length))
                            .map(r => parseFloat(r[0]))
                            .filter(n => !isNaN(n));

                        const isMonotonic = firstColData.every((val, i, arr) =>
                            i === 0 || val >= arr[i - 1]
                        );

                        if (headers[0].toLowerCase() === "time" || isMonotonic) {
                            timeColIndex = 0;
                        } else {
                            // Look for explicit "Time" column
                            const explicitTime = headers.findIndex(h =>
                                h.toLowerCase() === "time"
                            );
                            if (explicitTime !== -1) {
                                timeColIndex = explicitTime;
                            } else {
                                // Assume first column is time
                                timeColIndex = 0;
                            }
                        }
                    }

                    const series: Record<string, number[]> = {};
                    const time: number[] = [];

                    if (generateTime) {
                        // Generate time array based on sampling speed
                        const samplingInterval = getSamplingInterval(metadata);

                        for (let i = 0; i < dataRows.length; i++) {
                            time.push(i * samplingInterval);
                        }

                        // Parse all columns as data (no time column to skip)
                        for (let i = 0; i < dataRows.length; i++) {
                            const row = dataRows[i];

                            for (let j = 0; j < headers.length; j++) {
                                const headerName = headers[j];

                                // Skip empty headers
                                if (!headerName || headerName === '') continue;

                                const val = parseFloat(row[j]);
                                if (!series[headerName]) series[headerName] = [];
                                series[headerName].push(isNaN(val) ? 0 : val);
                            }
                        }
                    } else {
                        // Old format: parse with time column
                        for (let i = 0; i < dataRows.length; i++) {
                            const row = dataRows[i];
                            const t = parseFloat(row[timeColIndex]);

                            // Skip invalid rows
                            if (isNaN(t)) continue;

                            time.push(t);

                            // Parse each column except time
                            for (let j = 0; j < headers.length; j++) {
                                const headerName = headers[j];

                                // Skip empty headers and time column
                                if (!headerName || headerName === '') continue;
                                if (j === timeColIndex) continue;

                                const val = parseFloat(row[j]);
                                if (!series[headerName]) series[headerName] = [];
                                series[headerName].push(isNaN(val) ? 0 : val);
                            }
                        }
                    }

                    // Group series by type
                    const groups = {
                        coilCurrents: [] as string[],
                        contactTravel: [] as string[],
                        dcrmResistance: [] as string[],
                        dcrmCurrent: [] as string[],
                        others: [] as string[]
                    };

                    Object.keys(series).forEach(key => {
                        const k = key.toLowerCase();

                        if (k.includes("coil current") || /\bc\d\b/.test(k)) {
                            groups.coilCurrents.push(key);
                        } else if (k.includes("contact travel") || k.includes("travel") || /\bt\d\b/.test(k)) {
                            groups.contactTravel.push(key);
                        } else if (k.includes("dcrm res") || k.includes("resistance") || k.includes("res ch")) {
                            groups.dcrmResistance.push(key);
                        } else if (k.includes("dcrm current") || k.includes("current ch")) {
                            groups.dcrmCurrent.push(key);
                        } else {
                            groups.others.push(key);
                        }
                    });

                    resolve({
                        metadata,
                        time,
                        series,
                        groups
                    });

                } catch (err) {
                    reject(err);
                }
            },
            error: (err) => reject(err)
        });
    });
};
