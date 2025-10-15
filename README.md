# Supreme Automation - Microsoft 365 & Azure DevOps Portfolio

Enterprise-grade automation for Microsoft cloud platforms, demonstrating infrastructure-as-code and platform automation capabilities.

## Overview

This repository showcases DevOps automation expertise across:
- **Microsoft 365 Platform Automation** (User provisioning, license management, security compliance)
- **Azure Infrastructure Automation** (Resource management, cost optimization, security enforcement)
- **Integrated Cloud Operations** (End-to-end automation connecting M365 and Azure)

## Current Capabilities

### M365 Automation (Python + Microsoft Graph API)
- ✅ **User Onboarding Automation** - Complete end-to-end user provisioning
  - Azure AD user creation with validation
  - Automated license assignment (E3/E5)
  - Security group management
  - Mailbox configuration with timezone/quota settings
  - Comprehensive error handling and rollback
  - HTML reporting with time-saved metrics
  - Secure credential management
- ✅ **User Management** - List and query Azure AD users
- 🚧 **License Optimization** - Analyze and optimize license usage
- 🚧 **Security Compliance** - Automated security auditing

## Technology Stack

- **Languages:** Python 3.10
- **APIs:** Microsoft Graph API
- **Authentication:** Azure AD Application Credentials
- **Dependencies:** See requirements.txt

## Repository Structure
```
supreme-automation/
├── src/
│   └── m365_automation/           # M365 automation scripts
│       ├── user_onboarding.py     # Automated user onboarding system
│       ├── report_generator.py    # HTML/CSV report generation
│       ├── list_users.py          # User enumeration
│       └── config.py              # Authentication configuration
├── input/                         # Input CSV files for bulk operations
│   └── users_to_onboard.csv       # User onboarding data
├── output/                        # Generated reports and credentials
│   ├── secure_credentials.csv     # Temporary passwords (secure)
│   ├── onboarding_report.html     # Visual onboarding report
│   └── failed_onboardings.csv     # Failed operations log
├── templates/                     # CSV templates
│   └── onboarding_template.csv    # User onboarding template
├── docs/                          # Documentation
│   ├── USER_ONBOARDING_GUIDE.md   # Complete onboarding guide
│   └── ONBOARDING_QUICK_START.md  # Quick reference
├── requirements.txt               # Python dependencies
├── onboarding.log                 # Execution logs
└── README.md                      # This file
```

## Getting Started

### Prerequisites
- Python 3.10+
- Azure AD tenant with Global Administrator access
- Registered Azure AD application with Graph API permissions

### Installation
```bash
# Clone repository
git clone https://github.com/outing69/supreme-automation.git
cd supreme-automation

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **Register Azure AD Application** with Microsoft Graph permissions:
   - `User.ReadWrite.All`
   - `Group.ReadWrite.All`
   - `Directory.ReadWrite.All`
   - `Organization.Read.All`

2. **Grant Admin Consent** for all permissions in Azure Portal

3. **Configure Credentials** in `src/m365_automation/config.py`:
   ```python
   TENANT_ID = "your-tenant-id"
   CLIENT_ID = "your-client-id"
   CLIENT_SECRET = "your-client-secret"
   ```

### Quick Start: User Onboarding

```bash
# 1. Prepare input CSV
cp templates/onboarding_template.csv input/users_to_onboard.csv
# Edit with your user data

# 2. Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate (Windows)

# 3. Navigate to module directory and run
cd src/m365_automation
python3 user_onboarding.py

# Or run from project root with full path
python3 src/m365_automation/user_onboarding.py

# 4. Check outputs (from project root)
# - Passwords: output/secure_credentials.csv
# - Report: output/onboarding_report.html
# - Log: onboarding.log
```

**Documentation**: See [docs/USER_ONBOARDING_GUIDE.md](docs/USER_ONBOARDING_GUIDE.md) for complete instructions.

## Use Cases

### User Onboarding Automation
- **Time Savings**: 43 minutes → 30 seconds per user (~98% reduction)
- **Enterprise Scale**: Onboard 50+ users in minutes instead of days
- **Error Reduction**: Automated validation prevents common mistakes
- **Compliance**: Consistent security group assignments and mailbox configurations
- **Audit Trail**: Comprehensive logging and HTML reports

### Additional Capabilities (Roadmap)
- **Cost Optimization:** Identify and eliminate wasted M365 licenses
- **Security Compliance:** Automated auditing and enforcement
- **License Management:** Real-time license allocation optimization

## Roadmap

- [x] **Automated user onboarding system** (✅ Complete)
  - CSV-based bulk onboarding
  - License assignment (E3/E5)
  - Group membership automation
  - Mailbox configuration
  - HTML reporting with metrics
- [ ] **User offboarding automation**
  - License reclamation
  - Group membership cleanup
  - Mailbox archival
  - Access revocation
- [ ] **License optimization analyzer**
  - Unused license detection
  - Cost optimization recommendations
  - Usage analytics dashboard
- [ ] **Mailbox security compliance enforcer**
  - Retention policy automation
  - DLP policy application
  - External sharing audits
- [ ] **Azure resource management integration**
  - VM lifecycle automation
  - Cost anomaly detection
  - Resource tagging enforcement
- [ ] **CI/CD pipeline for automation deployment**
  - GitHub Actions workflow
  - Automated testing
  - Version management

## Author

Alex de Vries - DevOps Engineer specializing in Microsoft Cloud automation

## License

This project is for automation practicing
