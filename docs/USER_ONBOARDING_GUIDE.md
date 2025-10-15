# M365 User Onboarding Automation - User Guide

## Overview

This automated onboarding system streamlines the creation of new Microsoft 365 users by handling:
- User account creation in Azure AD
- License assignment (E3/E5)
- Security and M365 group membership
- Mailbox configuration with timezone and quotas
- Comprehensive error handling and rollback capabilities

**Time Saved**: ~43 minutes per user (fully automated)

---

## Prerequisites

### 1. Azure AD App Registration Permissions

Ensure your app registration has the following **Application Permissions** (not Delegated):

- `User.ReadWrite.All` - Create and manage users
- `Group.ReadWrite.All` - Add users to groups
- `Directory.ReadWrite.All` - Manage directory objects
- `Organization.Read.All` - Read license SKU information

**Important**: After adding permissions, click "Grant admin consent" in Azure Portal.

### 2. Python Dependencies

Install required packages:
```bash
pip install -r requirements.txt
```

Required packages:
- `azure-identity`
- `msgraph-sdk`
- `msgraph-core`

### 3. Configuration

Authentication credentials are stored in `src/m365_automation/config.py`:
```python
TENANT_ID = "your-tenant-id"
CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
```

⚠️ **Security Note**: `config.py` is gitignored. Never commit credentials to version control.

---

## Quick Start

### Step 1: Prepare Your Input CSV

Copy the template and add your users:
```bash
cp templates/onboarding_template.csv input/users_to_onboard.csv
```

Edit `input/users_to_onboard.csv` with your user data:

```csv
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Jan,de Vries,Jan de Vries,jan.devries@solidsupport.nl,IT,System Administrator,manager@solidsupport.nl,E5,IT-Admins;All-Staff,
Lisa,van Dam,Lisa van Dam,lisa.vandam@solidsupport.nl,Sales,Account Manager,sales.manager@solidsupport.nl,E3,Sales-Team;All-Staff,
```

### Step 2: Run the Onboarding Script

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Run from project root (recommended)
python3 src/m365_automation/user_onboarding.py

# Or navigate to module directory first
cd src/m365_automation
python3 user_onboarding.py

# Specify a custom input file
python3 src/m365_automation/user_onboarding.py --input /path/to/custom.csv
```

### Step 3: Review Outputs

After execution, check these files:

1. **`output/secure_credentials.csv`** - Temporary passwords for new users
2. **`output/onboarding_report.html`** - Visual report with statistics
3. **`onboarding.log`** - Detailed execution log
4. **`output/failed_onboardings.csv`** - Failed users (if any) for manual intervention

---

## CSV Field Reference

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `first_name` | ✅ Yes | User's first name | Jan |
| `last_name` | ✅ Yes | User's last name | de Vries |
| `display_name` | No | Full display name (auto-generated if empty) | Jan de Vries |
| `user_principal_name` | ✅ Yes | UPN/email address (must be unique) | jan.devries@domain.nl |
| `department` | No | Department name | IT |
| `job_title` | No | Job title | System Administrator |
| `manager_email` | No | Manager's UPN (validated if provided) | manager@domain.nl |
| `license_type` | ✅ Yes | License type: `E3`, `E5`, `INTUNE`, or `NONE` | E5 |
| `groups` | No | Semicolon-separated group names | IT-Admins;All-Staff |
| `mailbox_delegation` | No | Email of delegate for mailbox access | admin@domain.nl |

### Notes:
- **Usage Location** is automatically set to `NL` (Netherlands)
- **Password Policy**: 16-character complex passwords with forced change on first login
- **Groups**: Must exist before onboarding (script will log warnings for missing groups)

---

## Workflow Details

### 1. User Creation
- Creates Azure AD user account
- Sets `UsageLocation = "NL"` (required for licensing)
- Generates 16-character secure password
- Forces password change on first login
- Auto-generates mail nickname from UPN

### 2. License Assignment
- Maps E3/E5/INTUNE to tenant SKU IDs dynamically
- Supports NONE option for users without licenses (e.g., external guests)
- Implements exponential backoff retry (3 attempts)
- Validates license availability
- Rolls back user creation if licensing fails

### 3. Group Membership
- Handles both Security Groups and Microsoft 365 Groups
- Validates group existence before adding
- Continues on individual group failures
- Reports success/failure per group

### 4. Mailbox Configuration
- Sets timezone to `Europe/Amsterdam`
- Logs recommendations for:
  - E5: Enable Litigation Hold (via Exchange Admin Center)
  - Delegation: Configure via Exchange Admin Center (Graph API limitations)

### 5. Error Handling
- **Validation**: Pre-flight checks for data quality
- **Rollback**: Deletes user if critical operations fail
- **Logging**: Comprehensive logging to `onboarding.log`
- **Rate Limiting**: 1-second pause between users to respect API limits

---

## License SKU Mapping

The script automatically detects available SKUs in your tenant. Supported license types:

| License Type | SKU Part Number | Description | Use Case |
|--------------|-----------------|-------------|----------|
| E3 | SPE_E3 | Microsoft 365 E3 | Standard users |
| E5 | SPE_E5 | Microsoft 365 E5 | Advanced compliance users |
| INTUNE | INTUNE_A_D | Microsoft Intune (Device) | Mobile device management only |
| NONE | (none) | No license assigned | External guests, no-cost accounts |

**Custom SKUs**: To add more license types, edit the `LICENSE_SKU_MAPPING` dictionary in `user_onboarding.py`:

```python
LICENSE_SKU_MAPPING = {
    'E3': 'SPE_E3',
    'E5': 'SPE_E5',
    'INTUNE': 'INTUNE_A_D',
    'NONE': None,
    'BUSINESS_BASIC': 'O365_BUSINESS_ESSENTIALS',  # Add custom mappings
}
```

### Using NONE License Type

The `NONE` option is useful for:
- **External guest accounts** - Users who don't need M365 services
- **Service accounts** - Automated accounts that only need directory access
- **Testing accounts** - Temporary accounts for development/testing
- **Pre-provisioning** - Create accounts before licenses are available

**Important**: Users with `NONE` license will not have access to:
- Email (Exchange Online)
- OneDrive/SharePoint
- Teams
- Office applications

They will only exist in Azure AD for authentication purposes.

---

## Troubleshooting

### Common Issues

#### 1. "SKU not found in tenant subscriptions"
**Cause**: Your tenant doesn't have the requested license type.

**Solution**:
- Check available licenses in Microsoft 365 Admin Center
- Verify SKU name matches `LICENSE_SKU_MAPPING`
- Run with verbose logging to see available SKUs

#### 2. "User already exists"
**Cause**: Duplicate UPN in tenant.

**Solution**:
- Check existing users: `python -m src.m365_automation.list_users`
- Use a different UPN or remove existing user

#### 3. "Manager not found"
**Cause**: Manager email doesn't exist in Azure AD.

**Solution**:
- Verify manager's UPN is correct
- Ensure manager account exists before onboarding
- Leave `manager_email` blank to skip validation

#### 4. "Group not found"
**Cause**: Group doesn't exist in Azure AD.

**Solution**:
- Create groups before onboarding
- Check group names for typos (case-sensitive)
- Script will continue without adding to missing groups

#### 5. "Insufficient privileges to complete the operation"
**Cause**: Missing API permissions or admin consent.

**Solution**:
1. Go to Azure Portal → App Registrations → Your App
2. API Permissions → Add required permissions (see Prerequisites)
3. Click "Grant admin consent for [Tenant]"
4. Wait 5-10 minutes for permissions to propagate

---

## Security Best Practices

### Credential Management
- ✅ Store `output/secure_credentials.csv` in a secure location (SharePoint, password manager)
- ✅ Transmit passwords via secure channels (encrypted email, Teams)
- ✅ Delete credentials CSV after distribution
- ❌ Never email credentials in plain text
- ❌ Never commit `output/` folder to Git

### Input Data Protection
- ✅ Keep `input/users_to_onboard.csv` encrypted at rest
- ✅ Delete after onboarding completes
- ✅ Limit access to HR/IT personnel only

### API Credentials
- ✅ Rotate `CLIENT_SECRET` every 90 days
- ✅ Use Key Vault for production deployments
- ✅ Monitor app registration sign-ins

---

## Advanced Usage

### Batch Processing Large User Lists

For large batches (100+ users), consider:

1. **Split into smaller batches** (25 users per run):
```bash
split -l 26 input/users_to_onboard.csv batch_  # Keep header row
```

2. **Run during off-peak hours** to avoid API throttling

3. **Monitor API rate limits**:
   - Microsoft Graph: 2000 requests per 10 seconds
   - Script includes 1-second delays between users

### Custom Mailbox Configuration

For advanced mailbox settings (quotas, retention), use **Exchange Online PowerShell**:

```powershell
# Connect to Exchange Online
Connect-ExchangeOnline

# Set mailbox quota
Set-Mailbox -Identity "user@domain.nl" -ProhibitSendQuota 50GB -IssueWarningQuota 49GB

# Enable litigation hold (E5)
Set-Mailbox -Identity "user@domain.nl" -LitigationHoldEnabled $true
```

### Automated Scheduling

Schedule onboarding with `cron` (Linux) or Task Scheduler (Windows):

```bash
# Cron example: Run every Monday at 9 AM
0 9 * * 1 cd /path/to/supreme-automation && /path/to/venv/bin/python -m src.m365_automation.user_onboarding
```

---

## Output Report Interpretation

### HTML Report Sections

1. **Statistics Dashboard**
   - Total users processed
   - Success/failure counts
   - Success rate percentage
   - Time saved calculation

2. **Successful Onboardings Table**
   - UPN, display name, department, job title
   - Assigned license type
   - Groups added
   - Mailbox configuration status

3. **Failed Onboardings Table**
   - User details
   - Specific error messages
   - Recommended remediation actions

### Time Saved Calculation

Based on manual onboarding benchmark:
- Manual process: ~43 minutes per user
- Automated: ~30 seconds per user
- **Time saved = (Successful users × 43 minutes)**

Example: 10 successful users = 430 minutes (7.2 hours) saved

---

## Support & Troubleshooting

### Logs Location
- **`onboarding.log`** - Detailed execution log with timestamps
- Check this file first when debugging issues

### Verbose Logging
All Graph API calls are logged. Example log entry:
```
2025-10-15 14:23:45 - __main__ - INFO - Creating user: jan.devries@solidsupport.nl
2025-10-15 14:23:47 - __main__ - INFO - ✓ User created successfully: jan.devries@solidsupport.nl
2025-10-15 14:23:48 - __main__ - INFO - Assigning E5 license to jan.devries@solidsupport.nl
```

### Getting Help
1. Check `onboarding.log` for detailed error messages
2. Review this guide's Troubleshooting section
3. Verify Azure AD permissions in portal
4. Test with a single user before bulk operations

---

## Appendix: Script Architecture

### Key Components

#### `UserOnboardingManager` Class
- **`validate_user_data()`** - Pre-flight validation
- **`create_user()`** - Azure AD user creation
- **`assign_license()`** - License assignment with retry
- **`add_to_groups()`** - Group membership management
- **`configure_mailbox()`** - Mailbox settings
- **`onboard_user()`** - Complete workflow orchestration

#### `report_generator.py`
- **`generate_html_report()`** - Create visual HTML report
- **`export_failed_users_csv()`** - Export failures for manual processing

### Error Recovery Flow
```
User Creation Success
  ↓
License Assignment → FAIL → Rollback User Creation → Log Error
  ↓ SUCCESS
Group Addition → PARTIAL FAIL → Continue (log warnings)
  ↓
Mailbox Config → FAIL → Continue (log warnings)
  ↓
Mark as Successful
```

---

## Changelog

### Version 1.0 (2025-10-15)
- Initial release
- Support for E3/E5 license assignment
- Group membership management
- Mailbox timezone configuration
- Comprehensive error handling
- HTML report generation
- CSV credential export

---

**For questions or issues, check the main project README.md or contact your IT administrator.**
