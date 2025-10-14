# Supreme Automation - Microsoft 365 & Azure DevOps Portfolio

Enterprise-grade automation for Microsoft cloud platforms, demonstrating infrastructure-as-code and platform automation capabilities.

## Overview

This repository showcases DevOps automation expertise across:
- **Microsoft 365 Platform Automation** (User provisioning, license management, security compliance)
- **Azure Infrastructure Automation** (Resource management, cost optimization, security enforcement)
- **Integrated Cloud Operations** (End-to-end automation connecting M365 and Azure)

## Current Capabilities

### M365 Automation (Python + Microsoft Graph API)
- User management and provisioning
- License optimization and reporting
- Security compliance auditing
- Automated mailbox configuration

## Technology Stack

- **Languages:** Python 3.10
- **APIs:** Microsoft Graph API
- **Authentication:** Azure AD Application Credentials
- **Dependencies:** See requirements.txt

## Repository Structure
```
supreme-automation/
├── src/
│   └── m365_automation/        # M365 automation scripts
│       └── list_users.py       # User enumeration and reporting
├── docs/                       # Documentation
├── examples/                   # Usage examples
├── requirements.txt            # Python dependencies
└── README.md                   # This file
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

1. Register Azure AD application with Microsoft Graph permissions
2. Configure application credentials (see config_template.py)
3. Update script configuration with your tenant details

## Use Cases

- **Enterprise IT Operations:** Automate user lifecycle management
- **Cost Optimization:** Identify and eliminate wasted M365 licenses
- **Security Compliance:** Automated auditing and enforcement
- **Operational Efficiency:** Reduce manual administrative tasks from 45 minutes to 2 minutes

## Roadmap

- [ ] Automated user onboarding system
- [ ] License optimization analyzer
- [ ] Mailbox security compliance enforcer
- [ ] Azure resource management integration
- [ ] CI/CD pipeline for automation deployment

## Author

Alex de Vries - DevOps Engineer specializing in Microsoft Cloud automation

## License

This project is for automation practicing
