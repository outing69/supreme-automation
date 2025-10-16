"""
Azure Monitoring Configuration Template
Copy this file to monitor_config.py and fill in your Azure credentials
"""

# Azure Subscription Details
SUBSCRIPTION_ID = "your-subscription-id-here"
TENANT_ID = "your-tenant-id-here"

# Service Principal Credentials (Azure AD App Registration)
CLIENT_ID = "your-client-id-here"
CLIENT_SECRET = "your-client-secret-here"

# Resource Configuration
RESOURCE_GROUP = "your-resource-group-name"
LOG_ANALYTICS_WORKSPACE_ID = "your-log-analytics-workspace-id"

# Monitoring Settings
SCOPES = ['https://management.azure.com/.default']

# Cost Management Settings
BUDGET_AMOUNT = 1000.00  # Monthly budget in EUR/USD
CURRENCY = "EUR"

# Alert Thresholds
CPU_THRESHOLD = 80  # Percentage
MEMORY_THRESHOLD = 85  # Percentage
DISK_THRESHOLD = 90  # Percentage
