---
description: Dashboard Redesign Implementation Plan
---

# Dashboard Redesign & Analysis Page Implementation Plan

## Overview
Transform the current system by:
1. Creating a new comprehensive Dashboard page (first page shown)
2. Renaming current Dashboard to "New Analysis" with enhanced CSV analysis capabilities

## Phase 1: Backend Updates (Flask - app.py)

### 1.1 Create New Dashboard Route
- Add `/dashboard` route with analytics data
- Aggregate statistics: total tests, average health, fault distribution
- Calculate health trends over time
- Prepare data for health vs spikes graph

### 1.2 Enhance Analysis Route
- Rename `/api/predict` to handle detailed CSV analysis
- Add `/api/analyze-csv` endpoint for comprehensive file analysis
- Extract time-series data: coil current, resistance, DCRM current, contact travel
- Return graph-ready data structures

### 1.3 Add Analytics Endpoints
- `/api/dashboard/stats` - Overall system statistics
- `/api/dashboard/health-trends` - Health score trends
- `/api/dashboard/fault-distribution` - Pie chart data
- `/api/dashboard/recent-tests` - Recent test summaries

## Phase 2: Frontend Updates (React)

### 2.1 Create New Dashboard Component
**File**: `src/components/Dashboard.jsx`
- Stats cards (total tests, avg health, etc.)
- Health vs Spikes line chart (using Chart.js or Recharts)
- Fault distribution pie chart
- Recent tests table
- Responsive grid layout

### 2.2 Create Analysis Component
**File**: `src/components/Analysis.jsx`
- CSV file upload section
- Multiple time-series graphs:
  - Coil Current vs Time
  - Resistance vs Time
  - DCRM Current vs Time
  - Contact Travel vs Time
- Prediction results display
- Download report functionality

### 2.3 Update Navigation
- Update App.jsx routing
- Change navigation labels
- Set Dashboard as default route

## Phase 3: Data Visualization

### 3.1 Install Chart Libraries
```bash
npm install recharts chart.js react-chartjs-2
```

### 3.2 Create Chart Components
- LineChart component (health trends, time-series)
- PieChart component (fault distribution)
- BarChart component (test statistics)

## Phase 4: Styling

### 4.1 Dashboard Styles
- Modern card-based layout
- Gradient backgrounds
- Responsive grid system
- Hover effects and animations

### 4.2 Analysis Page Styles
- Multi-graph layout
- Interactive tooltips
- Zoom/pan capabilities
- Export functionality

## Phase 5: Testing & Validation

### 5.1 Test Data Flow
- Upload sample CSV files
- Verify graph rendering
- Check data accuracy
- Test responsive behavior

### 5.2 Integration Testing
- Backend-frontend communication
- Real-time updates
- Error handling

## Implementation Order

1. ✅ Create implementation plan
2. Backend: Add analytics endpoints
3. Backend: Enhance CSV analysis
4. Frontend: Install chart libraries
5. Frontend: Create Dashboard component
6. Frontend: Create Analysis component
7. Frontend: Update routing
8. Styling: Dashboard CSS
9. Styling: Analysis CSS
10. Testing: End-to-end validation
