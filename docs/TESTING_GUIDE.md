# Testing Guide: User Onboarding Automation

## Pre-Testing Checklist

Before running tests, ensure:

1. ✅ **Azure AD App Registration** is configured with required permissions
2. ✅ **Admin consent** has been granted for all API permissions
3. ✅ **config.py** contains valid credentials
4. ✅ **Test groups** exist in Azure AD (or use existing groups)
5. ✅ **Test license** availability (at least 1 E3 or E5 license free)

---

## Test Scenarios

### Test 1: Single User Onboarding (Happy Path)

**Objective**: Verify complete workflow with valid data.

**Setup**:
```bash
# Create test input file
cat > input/users_to_onboard.csv << 'EOF'
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Test,User,Test User,test.user@solidsupport.nl,IT,Test Administrator,,E3,,
EOF
```

**Execute**:
```bash
python -m src.m365_automation.user_onboarding
```

**Expected Results**:
- ✅ User created in Azure AD
- ✅ E3 license assigned
- ✅ Temporary password generated
- ✅ `output/secure_credentials.csv` contains password
- ✅ `output/onboarding_report.html` shows 1 successful user
- ✅ No errors in `onboarding.log`

**Cleanup**:
```bash
# Delete test user via Azure Portal or:
# python -m src.m365_automation.delete_user test.user@solidsupport.nl
```

---

### Test 2: Validation Error Handling

**Objective**: Verify pre-flight validation catches errors.

**Setup**:
```bash
cat > input/users_to_onboard.csv << 'EOF'
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
,,Invalid User,invalid-email,IT,Test,,E99,,
EOF
```

**Execute**:
```bash
python -m src.m365_automation.user_onboarding
```

**Expected Results**:
- ❌ Validation fails with errors:
  - "Missing required field: first_name"
  - "Missing required field: last_name"
  - "Invalid UPN format: invalid-email"
  - "Invalid license type: E99"
- ✅ User NOT created in Azure AD
- ✅ Error details in `onboarding_report.html`
- ✅ No orphaned accounts

**Cleanup**: None needed (user not created)

---

### Test 3: Duplicate UPN Detection

**Objective**: Verify duplicate detection prevents conflicts.

**Setup**:
```bash
# First, create a user manually via Azure Portal OR run Test 1
# Then try to create the same user again:
cat > input/users_to_onboard.csv << 'EOF'
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Test,User,Test User,test.user@solidsupport.nl,IT,Test Administrator,,E3,,
EOF
```

**Execute**:
```bash
python -m src.m365_automation.user_onboarding
```

**Expected Results**:
- ❌ Validation fails: "User already exists: test.user@solidsupport.nl"
- ✅ No duplicate user created
- ✅ Error in report

**Cleanup**: Delete the first test user

---

### Test 4: Group Assignment (Existing Groups)

**Objective**: Verify group membership automation.

**Prerequisites**:
- Create test groups in Azure AD:
  - "Test-Group-1" (Security Group)
  - "Test-Group-2" (Microsoft 365 Group)

**Setup**:
```bash
cat > input/users_to_onboard.csv << 'EOF'
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Test,GroupUser,Test Group User,test.groupuser@solidsupport.nl,IT,Test,,E3,Test-Group-1;Test-Group-2,
EOF
```

**Execute**:
```bash
python -m src.m365_automation.user_onboarding
```

**Expected Results**:
- ✅ User created
- ✅ E3 license assigned
- ✅ Added to both groups
- ✅ Report shows group membership success
- ✅ Verify in Azure Portal: User appears in both groups

**Cleanup**: Delete test user and optionally test groups

---

### Test 5: Non-Existent Group (Graceful Degradation)

**Objective**: Verify system continues when group doesn't exist.

**Setup**:
```bash
cat > input/users_to_onboard.csv << 'EOF'
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Test,NoGroup,Test NoGroup User,test.nogroup@solidsupport.nl,IT,Test,,E3,NonExistentGroup123,
EOF
```

**Execute**:
```bash
python -m src.m365_automation.user_onboarding
```

**Expected Results**:
- ✅ User created successfully
- ✅ E3 license assigned
- ⚠️ Warning logged: "Group not found: NonExistentGroup123"
- ✅ Onboarding marked as successful (non-critical failure)
- ✅ Report shows failed group assignment

**Cleanup**: Delete test user

---

### Test 6: License Rollback on Failure

**Objective**: Verify user deletion if license assignment fails.

**Setup**:
This is difficult to test without intentionally breaking permissions or exhausting licenses.

**Simulated Test**:
1. Temporarily revoke `Organization.Read.All` permission
2. Run onboarding
3. User creation succeeds, but SKU fetch fails
4. Verify user is rolled back (deleted)

**Alternative**: Review rollback code logic in `user_onboarding.py:rollback_user_creation()`

---

### Test 7: Bulk Onboarding (3 Users)

**Objective**: Verify batch processing and rate limiting.

**Setup**:
```bash
cat > input/users_to_onboard.csv << 'EOF'
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Bulk,User1,Bulk User 1,bulk.user1@solidsupport.nl,IT,Test Admin,,E3,,
Bulk,User2,Bulk User 2,bulk.user2@solidsupport.nl,Sales,Test Sales,,E3,,
Bulk,User3,Bulk User 3,bulk.user3@solidsupport.nl,Finance,Test Finance,,E5,,
EOF
```

**Execute**:
```bash
python -m src.m365_automation.user_onboarding
```

**Expected Results**:
- ✅ All 3 users created
- ✅ Licenses assigned (2x E3, 1x E5)
- ✅ 1-second pause between users (check log timestamps)
- ✅ Report shows 3 successful onboardings
- ✅ Time saved: 129 minutes (3 × 43)

**Cleanup**: Delete all 3 test users

---

### Test 8: Manager Validation

**Objective**: Verify manager existence check.

**Setup**:
```bash
cat > input/users_to_onboard.csv << 'EOF'
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Test,Manager,Test Manager User,test.manager@solidsupport.nl,IT,Test,,E3,,nonexistent.manager@solidsupport.nl
EOF
```

**Execute**:
```bash
python -m src.m365_automation.user_onboarding
```

**Expected Results**:
- ❌ Validation fails: "Manager not found: nonexistent.manager@solidsupport.nl"
- ✅ User NOT created

**Cleanup**: None needed

---

### Test 9: E5 License Assignment

**Objective**: Verify E5-specific features.

**Prerequisites**: At least 1 E5 license available

**Setup**:
```bash
cat > input/users_to_onboard.csv << 'EOF'
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Test,E5User,Test E5 User,test.e5user@solidsupport.nl,IT,Test Admin,,E5,,
EOF
```

**Execute**:
```bash
python -m src.m365_automation.user_onboarding
```

**Expected Results**:
- ✅ User created
- ✅ E5 license assigned
- ✅ Log message: "ℹ E5 license detected - Litigation Hold should be enabled..."
- ✅ Mailbox configured with timezone

**Verification**:
```bash
# Check license in Azure Portal
# User → Licenses and apps → Should show "Microsoft 365 E5"
```

**Cleanup**: Delete test user

---

### Test 10: Custom CSV Path

**Objective**: Verify command-line argument support.

**Setup**:
```bash
mkdir -p /tmp/test-onboarding
cat > /tmp/test-onboarding/custom.csv << 'EOF'
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
Custom,Path,Custom Path User,custom.path@solidsupport.nl,IT,Test,,E3,,
EOF
```

**Execute**:
```bash
python -m src.m365_automation.user_onboarding --input /tmp/test-onboarding/custom.csv
```

**Expected Results**:
- ✅ Script reads from custom path
- ✅ User created successfully
- ✅ Outputs still go to `./output/`

**Cleanup**: Delete test user

---

## Automated Test Script (Optional)

Create a test runner script:

```bash
#!/bin/bash
# test_onboarding.sh

echo "M365 Onboarding Automation - Test Suite"
echo "========================================"

# Test 1: Single user
echo -e "\n[TEST 1] Single User Onboarding"
cat > input/users_to_onboard.csv << 'EOF'
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
AutoTest,User1,AutoTest User1,autotest.user1@solidsupport.nl,IT,Test,,E3,,
EOF
python -m src.m365_automation.user_onboarding
echo "✓ Test 1 complete - Check onboarding_report.html"
read -p "Press Enter to continue..."

# Test 2: Validation errors
echo -e "\n[TEST 2] Validation Error Handling"
cat > input/users_to_onboard.csv << 'EOF'
first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation
,,Invalid,invalid-email,IT,Test,,E99,,
EOF
python -m src.m365_automation.user_onboarding
echo "✓ Test 2 complete - Errors should be logged"
read -p "Press Enter to continue..."

# Add more tests...

echo -e "\n========================================"
echo "Test suite complete!"
echo "Review onboarding_report.html for results"
```

---

## Monitoring During Tests

### Real-Time Log Monitoring
```bash
# In separate terminal, watch log file:
tail -f onboarding.log
```

### Expected Log Entries
```
2025-10-15 14:23:45 - __main__ - INFO - Authenticating to Microsoft Graph...
2025-10-15 14:23:46 - __main__ - INFO - ✓ Authentication successful
2025-10-15 14:23:47 - __main__ - INFO - Fetching available license SKUs...
2025-10-15 14:23:48 - __main__ - INFO -   SPE_E3: [SKU-ID] (Available: 10)
2025-10-15 14:23:48 - __main__ - INFO - Creating user: test.user@solidsupport.nl
2025-10-15 14:23:50 - __main__ - INFO - ✓ User created successfully
2025-10-15 14:23:51 - __main__ - INFO - Assigning E3 license...
2025-10-15 14:23:52 - __main__ - INFO - ✓ License assigned successfully
```

---

## Troubleshooting Test Failures

### "Insufficient privileges to complete the operation"
- **Cause**: Missing API permissions or admin consent
- **Fix**:
  1. Go to Azure Portal → App Registrations → Your App
  2. API Permissions → Verify all permissions are granted
  3. Click "Grant admin consent"
  4. Wait 5-10 minutes

### "SKU not found in tenant subscriptions"
- **Cause**: No E3/E5 licenses in tenant
- **Fix**: Purchase licenses via M365 Admin Center

### "Rate limit exceeded"
- **Cause**: Too many API calls too quickly
- **Fix**: Script has built-in delays; wait and retry

### "User already exists"
- **Cause**: Leftover test user from previous run
- **Fix**: Delete manually or change UPN in CSV

---

## Post-Testing Cleanup

After completing all tests:

```bash
# 1. Delete all test users
# Via Azure Portal: Azure AD → Users → Delete test users

# 2. Clean output directory
rm -rf output/*

# 3. Clean logs
rm onboarding.log

# 4. Reset input CSV
> input/users_to_onboard.csv
echo "first_name,last_name,display_name,user_principal_name,department,job_title,manager_email,license_type,groups,mailbox_delegation" > input/users_to_onboard.csv

# 5. Delete test groups (if created)
# Via Azure Portal: Azure AD → Groups → Delete test groups
```

---

## Performance Benchmarking

Run this to measure performance:

```bash
# Create 10 test users
for i in {1..10}; do
  echo "Perf,User$i,Perf User $i,perf.user$i@solidsupport.nl,IT,Test,,E3,," >> input/users_to_onboard.csv
done

# Time execution
time python -m src.m365_automation.user_onboarding

# Expected: ~2-3 minutes for 10 users
# Manual equivalent: ~430 minutes (7+ hours)
```

---

## Production Readiness Checklist

Before deploying to production:

- [ ] All 10 test scenarios pass
- [ ] Performance benchmarking completed
- [ ] Error handling verified
- [ ] Rollback mechanism tested
- [ ] Report generation validated
- [ ] Security best practices implemented
- [ ] Documentation reviewed
- [ ] Backup plan created
- [ ] Stakeholders notified
- [ ] Monitoring configured

---

**Last Updated**: 2025-10-15
