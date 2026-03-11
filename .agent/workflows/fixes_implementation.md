---
description: Implementation plan for multiple fixes
---

# IMPLEMENTATION PLAN - MULTIPLE FIXES

## Issues to Fix:

### 1. Report Download Not Working
- Fix the `/api/report/download/<report_id>` endpoint
- Ensure proper file generation and download

### 2. Admin Dashboard Cleanup
**Admin should ONLY see:**
- Number of users
- Average health of all users
- SOS requests
- User guide
- Admin panel (add/delete users)

**Remove from admin:**
- All user-specific features
- My History
- Reports
- New Analysis
- Field Advisor
- Interactions

### 3. Fix UI Alignment
- Separate admin and user parameters
- Ensure no overlap
- Top-notch UI design

### 4. SOS SMS Feature
**Requirements:**
- User enters admin's mobile number
- User selects problem type
- Send SMS to admin's phone
- Use SMS gateway (Twilio/similar)

---

## Implementation Order:

1. Fix report download (Quick fix)
2. Clean up admin dashboard navigation
3. Fix UI alignment issues
4. Implement SMS SOS feature

---

## Files to Modify:

1. `app.py` - Fix report download, add SMS
2. `templates/admin_dashboard.html` - Clean up navigation
3. `templates/sos.html` - Add SMS functionality
4. `database.py` - Update SOS schema for mobile number

---

## Next Steps:

Start with report download fix, then move to admin dashboard cleanup.
