export type UnitType = 'current' | 'travel' | 'resistance' | 'time' | 'none';

export const UNITS: Record<UnitType, string[]> = {
    current: ['A', 'mA', 'uA'],
    travel: ['nm', 'um', 'mm', 'cm', 'm'],
    resistance: ['uOhm', 'mOhm', 'Ohm'],
    time: ['s', 'ms'],
    none: []
};

// Base units: A, mm, uOhm, s
const SCALES: Record<string, number> = {
    // Current (Base: A)
    'A': 1,
    'mA': 30,
    'uA': 1000000,

    // Travel (Base: mm)
    'nm': 1000000,
    'um': 30,
    'mm': 1,
    'cm': 0.1,
    'm': 0.001,

    // Resistance (Base: uOhm)
    'uOhm': 1,
    'mOhm': 0.001,
    'Ohm': 0.000001,

    // Time (Base: s)
    's': 1,
    'ms': 1000
};

export const getUnitType = (key: string): UnitType => {
    const k = key.toLowerCase();
    if (k.includes('current') || /c\d/.test(k) || k.includes('(a)')) return 'current';
    if (k.includes('travel') || /t\d/.test(k) || k.includes('(mm)')) return 'travel';
    if (k.includes('res') || k.includes('resistance') || k.includes('uohm')) return 'resistance';
    if (k === 'time' || k === 'index') return 'time'; // Index treated as time for simplicity or ignored
    return 'none';
};

export const convertValue = (val: number, type: UnitType, targetUnit: string): number => {
    if (type === 'none' || !targetUnit) return val;
    const factor = SCALES[targetUnit];
    return val * (factor || 1);
};
