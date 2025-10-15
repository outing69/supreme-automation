# Quick Start: User Onboarding

## 60-Second Setup

### 1. Prepare Input CSV
```bash
cp templates/onboarding_template.csv input/users_to_onboard.csv
# Edit input/users_to_onboard.csv with your users
```

### 2. Run Onboarding
```bash
python -m src.m365_automation.user_onboarding
```

### 3. Retrieve Outputs
- **Passwords**: `output/secure_credentials.csv`
- **Report**: `output/onboarding_report.html`
- **Log**: `onboarding.log`

---

## CSV Format

```csv
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Jan,de Vries,Jan de Vries,jan.devries@domain.nl,IT,System Admin,manager@domain.nl,E5,IT-Admins;All-Staff,
```

**Required Fields**: `first_name`, `last_name`, `user_principal_name`, `license_type`

---

## License Types

- **E3**: Microsoft 365 E3 (standard)
- **E5**: Microsoft 365 E5 (advanced compliance)

---

## Common Issues

| Error | Solution |
|-------|----------|
| "SKU not found" | Verify license availability in M365 Admin Center |
| "User already exists" | Check for duplicate UPNs |
| "Group not found" | Create groups before onboarding |
| "Insufficient privileges" | Grant admin consent for API permissions |

---

## Security Checklist

- [ ] Store `secure_credentials.csv` securely (encrypted location)
- [ ] Transmit passwords via secure channel only
- [ ] Delete credentials CSV after distribution
- [ ] Remove input CSV after onboarding

---

**Full documentation**: See [USER_ONBOARDING_GUIDE.md](USER_ONBOARDING_GUIDE.md)
