import numpy as np
import pandas as pd

def extract_features(df):
    """
    Extracts statistical features from a DCRM dataframe.
    Expects clean columns after normalization.
    """
    features = []
    
    # Define channels we care about for features
    channels = {
        'coil': ['coil', 'c1'],
        'travel': ['travel', 't1'],
        'res': ['res', 'ch1'],
        'current': ['current', 'ch1']
    }
    
    for key, keywords in channels.items():
        # Find matching column
        col = None
        for c in df.columns:
            c_low = c.lower()
            if all(k in c_low for k in keywords):
                col = c
                break
        
        if col is not None:
            series = df[col].fillna(0).values
            if len(series) > 0:
                # Basic Stats (5 features)
                features.append(np.mean(series))
                features.append(np.std(series))
                features.append(np.max(series))
                features.append(np.min(series))
                features.append(np.percentile(series, 75) - np.percentile(series, 25))
                
                # Signal Specifics (1 feature)
                if key == 'coil':
                    features.append(np.argmax(series)) # Peak time index
                elif key == 'res':
                    # Average resistance during 'closed' state
                    closed_vals = series[series < 7000]
                    features.append(np.mean(closed_vals) if len(closed_vals) > 0 else 8000)
                elif key == 'travel':
                    features.append(series[-1] - series[0]) # Total displacement
                else: # current
                    features.append(np.sum(series > 1)) # Duration of activity
            else:
                features.extend([0] * 6)
        else:
            features.extend([0] * 6)
            
    return np.array(features)
