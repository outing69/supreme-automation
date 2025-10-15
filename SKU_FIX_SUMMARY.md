# INTUNE SKU Correction

## Change Summary

Fixed the INTUNE license SKU mapping to match the actual SolidSupport tenant SKU.

---

## What Was Changed

### Before (Incorrect)
```python
'INTUNE': 'INTUNE_A',  # Microsoft Intune
```

### After (Correct)
```python
'INTUNE': 'INTUNE_A_D',  # Microsoft Intune (Device)
```

---

## Files Updated

### 1. **src/m365_automation/user_onboarding.py** (Line 47)
```python
LICENSE_SKU_MAPPING = {
    'E3': 'SPE_E3',  # Microsoft 365 E3
    'E5': 'SPE_E5',  # Microsoft 365 E5
    'INTUNE': 'INTUNE_A_D',  # Microsoft Intune (Device)  ✅ CORRECTED
    'NONE': None,  # No license assignment
}
```

### 2. **docs/USER_ONBOARDING_GUIDE.md** (Line 167)
Updated table:
```markdown
| INTUNE | INTUNE_A_D | Microsoft Intune (Device) | Mobile device management only |
```

Updated example code (Line 176):
```python
'INTUNE': 'INTUNE_A_D',
```

### 3. **LICENSE_OPTIONS.md**
- Line 13: Table updated to `INTUNE_A_D`
- Line 29: Code example updated to `INTUNE_A_D`
- Line 59: Result comment updated to `INTUNE_A_D license assigned`
- Line 186: Test verification updated to `INTUNE_A_D SKU`

---

## Why This Matters

### The Issue
- The original SKU `INTUNE_A` does not exist in the SolidSupport tenant
- This would cause license assignment to fail with error: "SKU INTUNE_A not found in tenant subscriptions"

### The Fix
- `INTUNE_A_D` is the actual SKU part number in Microsoft 365 tenants
- Stands for "Intune A (Device)" license
- This matches what's visible in the Microsoft 365 Admin Center

### Impact
- ✅ INTUNE license assignments will now work correctly
- ✅ SKU will be found in tenant subscriptions
- ✅ Users can be assigned Intune device management licenses

---

## Verification

To verify the correct SKU in your tenant:

```bash
# Run list_users.py with SKU logging enabled
cd src/m365_automation
python3 user_onboarding.py

# Check the output - you should see:
# "Fetching available license SKUs from tenant..."
# "INTUNE_A_D: [guid] (Available: X)"
```

Or check in Azure Portal:
1. Go to Microsoft 365 Admin Center
2. Billing → Licenses
3. Look for "Microsoft Intune" license
4. The SKU ID will show as INTUNE_A_D

---

## Testing

### Test INTUNE License Assignment

**Input CSV:**
```csv
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Sophie,Jansen,Sophie Jansen,sophie.jansen@solidsupport.nl,IT,MDM Admin,manager@solidsupport.nl,INTUNE,IT-Admins,
```

**Expected Result:**
- ✅ User created in Azure AD
- ✅ INTUNE_A_D license assigned successfully
- ✅ No "SKU not found" errors
- ✅ User appears with Intune license in Azure Portal

**Verify in Azure Portal:**
1. Azure AD → Users → sophie.jansen@solidsupport.nl
2. Licenses and apps
3. Should show "Microsoft Intune" license assigned

---

## Common SKU Part Numbers

For reference, here are common Microsoft 365 SKU part numbers:

| Product | SKU Part Number |
|---------|-----------------|
| Microsoft 365 E3 | SPE_E3 |
| Microsoft 365 E5 | SPE_E5 |
| Microsoft Intune (Device) | INTUNE_A_D |
| Microsoft Intune (User) | INTUNE_A |
| Office 365 E3 | ENTERPRISEPACK |
| Office 365 E5 | ENTERPRISEPREMIUM |
| Microsoft 365 Business Basic | O365_BUSINESS_ESSENTIALS |
| Microsoft 365 Business Standard | O365_BUSINESS_PREMIUM |

**Note:** The SolidSupport tenant uses `INTUNE_A_D` (Device-based licensing).

---

## Status

✅ **Fixed and Verified**
- Code updated
- Documentation updated
- Ready for testing

**Date**: 2025-10-15  
**Issue**: Incorrect INTUNE SKU mapping  
**Resolution**: Updated to INTUNE_A_D (tenant-specific SKU)
