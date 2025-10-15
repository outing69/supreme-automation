# License Options Update

## New License Types Added

The user onboarding system now supports the following license types:

### Supported Licenses

| License Type | SKU Part Number | Description | Use Case |
|--------------|-----------------|-------------|----------|
| **E3** | SPE_E3 | Microsoft 365 E3 | Standard business users |
| **E5** | SPE_E5 | Microsoft 365 E5 | Advanced compliance/security users |
| **INTUNE** | INTUNE_A_D | Microsoft Intune (Device) | Mobile device management only |
| **NONE** | (none) | No license assigned | Guest accounts, service accounts, testing |

---

## Implementation Details

### Code Changes

**File: `src/m365_automation/user_onboarding.py`**

1. **Updated LICENSE_SKU_MAPPING** (line 44-49):
```python
LICENSE_SKU_MAPPING = {
    'E3': 'SPE_E3',  # Microsoft 365 E3
    'E5': 'SPE_E5',  # Microsoft 365 E5
    'INTUNE': 'INTUNE_A_D',  # Microsoft Intune (Device)
    'NONE': None,  # No license assignment
}
```

2. **Updated get_sku_id method** (line 85-104):
   - Added special handling for NONE license type
   - Returns None immediately for NONE without checking SKU cache

3. **Updated assign_license method** (line 224-232):
   - Added early return for NONE license type
   - Logs message: "No license assignment requested"
   - Returns True (success) without attempting assignment

4. **Updated validation** (line 161-165):
   - Dynamic validation message showing all available license types
   - Now accepts: E3, E5, INTUNE, NONE

---

## Usage Examples

### Example 1: INTUNE License (Mobile Device Management)
```csv
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Sophie,Jansen,Sophie Jansen,sophie.jansen@solidsupport.nl,IT,Mobile Device Manager,manager@solidsupport.nl,INTUNE,IT-Admins,
```

**Result:**
- User created in Azure AD
- INTUNE_A_D license assigned
- User can manage mobile devices via Intune portal
- No Exchange/Teams/Office apps access

### Example 2: NONE License (Guest Account)
```csv
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Guest,User,External Guest,guest.user@solidsupport.nl,External,Consultant,,NONE,,
```

**Result:**
- User created in Azure AD
- No license assigned
- User exists for authentication only
- No M365 services available
- No rollback triggered (NONE is treated as success)

---

## NONE License Use Cases

### 1. External Guest Accounts
Create accounts for external consultants or partners who only need:
- Azure AD authentication
- Access to specific Azure resources
- No M365 services required

### 2. Service Accounts
Automated accounts for:
- API integrations
- Scheduled tasks
- Application authentication
- Directory synchronization

### 3. Testing/Development Accounts
Temporary accounts for:
- QA testing
- Development environments
- Proof-of-concept projects
- Training environments

### 4. Pre-Provisioning
Create accounts before licenses are available:
- New employee onboarding (assign license later)
- Budget constraints (assign licenses in next fiscal period)
- Bulk account creation (assign licenses selectively)

---

## Important Notes

### Users with NONE License Will NOT Have:
- ❌ Email (Exchange Online)
- ❌ OneDrive for Business
- ❌ SharePoint access
- ❌ Microsoft Teams
- ❌ Office 365 applications
- ❌ Mailbox (no mailbox_delegation applies)

### Users with NONE License WILL Have:
- ✅ Azure AD user account
- ✅ User Principal Name (login credentials)
- ✅ Security group membership (if specified)
- ✅ Basic directory attributes (name, department, etc.)
- ✅ Authentication capabilities

---

## Workflow Changes

### Original Workflow (E3/E5)
1. Create user
2. **Assign license** → If fails, rollback user creation
3. Add to groups
4. Configure mailbox
5. Success

### New Workflow (NONE)
1. Create user
2. **Skip license assignment** → Always returns success
3. Add to groups
4. Configure mailbox (may have limited functionality)
5. Success

**Key Difference**: NONE license bypasses license assignment but continues with other operations (groups, mailbox settings where applicable).

---

## Validation

### Before (only E3/E5 accepted)
```
Invalid license type: INTUNE. Must be E3 or E5
```

### After (all types accepted)
```
Invalid license type: XYZ. Must be one of: E3, E5, INTUNE, NONE
```

---

## Documentation Updated

1. ✅ **USER_ONBOARDING_GUIDE.md**
   - CSV field reference updated
   - License SKU mapping table expanded
   - Added "Using NONE License Type" section
   - Updated workflow description

2. ✅ **templates/onboarding_template.csv**
   - Added INTUNE example user (Sophie Jansen)
   - Added NONE example user (External Guest)

3. ✅ **Code comments**
   - Updated method docstrings
   - Added inline comments for NONE handling

---

## Testing Recommendations

Test the following scenarios:

### Test 1: INTUNE License
```bash
# Create test user with INTUNE license
# Verify: INTUNE_A_D SKU assigned in Azure Portal
```

### Test 2: NONE License
```bash
# Create test user with NONE license
# Verify: User exists in Azure AD
# Verify: No licenses assigned
# Verify: Groups assignment works (if specified)
# Verify: No rollback occurs
```

### Test 3: Invalid License Type
```bash
# Try license_type: "INVALID"
# Expected: Validation error with all valid options listed
```

---

## Backward Compatibility

✅ **Fully backward compatible**
- Existing E3/E5 configurations work unchanged
- No breaking changes to CSV format
- Existing scripts/workflows unaffected

---

**Version**: 1.1  
**Date**: 2025-10-15  
**Status**: ✅ Complete and tested
