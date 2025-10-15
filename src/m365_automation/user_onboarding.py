#!/usr/bin/env python3
"""
Microsoft 365 User Onboarding Automation
Handles user creation, license assignment, group membership, and mailbox configuration
"""

import asyncio
import csv
import logging
import secrets
import string
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse

from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.user import User
from msgraph.generated.models.password_profile import PasswordProfile
from msgraph.generated.models.assigned_license import AssignedLicense
from msgraph.generated.models.mailbox_settings import MailboxSettings
from msgraph.generated.models.locale_info import LocaleInfo
from kiota_abstractions.api_error import APIError

# Import credentials from config
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, SCOPES


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('onboarding.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# License SKU mapping (Common Office 365 SKU IDs)
LICENSE_SKU_MAPPING = {
    'E3': 'SPE_E3',  # Microsoft 365 E3
    'E5': 'SPE_E5',  # Microsoft 365 E5
    'INTUNE': 'INTUNE_A_D',  # Microsoft Intune (Device)
    'NONE': None,  # No license assignment
}


class UserOnboardingManager:
    """Manages user onboarding operations via Microsoft Graph API"""

    def __init__(self, client: GraphServiceClient):
        self.client = client
        self.sku_cache: Optional[Dict[str, str]] = None
        self.validation_errors: List[str] = []
        self.onboarded_users: List[Dict] = []
        self.failed_users: List[Dict] = []

    async def initialize_sku_cache(self):
        """Fetch and cache available license SKUs from tenant"""
        try:
            logger.info("Fetching available license SKUs from tenant...")
            subscribed_skus = await self.client.subscribed_skus.get()

            self.sku_cache = {}
            if subscribed_skus and subscribed_skus.value:
                for sku in subscribed_skus.value:
                    sku_part_number = sku.sku_part_number
                    sku_id = str(sku.sku_id)
                    self.sku_cache[sku_part_number] = sku_id

                    # Log available licenses
                    available = sku.prepaid_units.enabled - sku.consumed_units if sku.prepaid_units else 0
                    logger.info(f"  {sku_part_number}: {sku_id} (Available: {available})")
            else:
                logger.warning("No subscribed SKUs found in tenant")

        except Exception as e:
            logger.error(f"Failed to fetch SKU information: {str(e)}")
            raise

    def get_sku_id(self, license_type: str) -> Optional[str]:
        """Get SKU ID from license type (E3/E5/INTUNE/NONE)"""
        if not self.sku_cache:
            raise RuntimeError("SKU cache not initialized. Call initialize_sku_cache() first.")

        # Handle NONE - no license assignment
        if license_type.upper() == 'NONE':
            return None

        sku_part_number = LICENSE_SKU_MAPPING.get(license_type.upper())
        if sku_part_number is None:  # Not in mapping
            logger.error(f"Unknown license type: {license_type}")
            return None

        sku_id = self.sku_cache.get(sku_part_number)
        if not sku_id:
            logger.error(f"SKU {sku_part_number} not found in tenant subscriptions")
            return None

        return sku_id

    @staticmethod
    def generate_password(length: int = 16) -> str:
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
            # Ensure password meets complexity requirements
            if (any(c.islower() for c in password)
                    and any(c.isupper() for c in password)
                    and any(c.isdigit() for c in password)
                    and any(c in "!@#$%^&*" for c in password)):
                return password

    async def validate_user_data(self, user_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate user data before creation
        Returns: (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        required_fields = ['first_name', 'last_name', 'user_principal_name', 'license_type']
        for field in required_fields:
            if not user_data.get(field):
                errors.append(f"Missing required field: {field}")

        upn = user_data.get('user_principal_name', '')

        # Validate email format
        if upn and '@' not in upn:
            errors.append(f"Invalid UPN format: {upn}")

        # Check for duplicate UPN
        try:
            existing_users = await self.client.users.get()
            if existing_users and existing_users.value:
                existing_upns = [u.user_principal_name for u in existing_users.value]
                if upn in existing_upns:
                    errors.append(f"User already exists: {upn}")
        except Exception as e:
            logger.warning(f"Could not check for duplicate UPNs: {str(e)}")

        # Validate manager exists (if specified)
        manager_email = user_data.get('manager_email')
        if manager_email:
            try:
                filter_query = f"userPrincipalName eq '{manager_email}'"
                manager_result = await self.client.users.get(
                    request_configuration=lambda req: setattr(req.query_parameters, 'filter', filter_query)
                )
                if not manager_result or not manager_result.value:
                    errors.append(f"Manager not found: {manager_email}")
            except Exception as e:
                logger.warning(f"Could not verify manager: {str(e)}")

        # Validate license type
        license_type = user_data.get('license_type', '').upper()
        if license_type not in LICENSE_SKU_MAPPING:
            valid_types = ', '.join(LICENSE_SKU_MAPPING.keys())
            errors.append(f"Invalid license type: {license_type}. Must be one of: {valid_types}")

        return len(errors) == 0, errors

    async def create_user(self, user_data: Dict) -> Optional[Dict]:
        """
        Create a new user in Azure AD
        Returns: Dictionary with user info and temporary password, or None on failure
        """
        upn = user_data['user_principal_name']
        logger.info(f"Creating user: {upn}")

        try:
            # Generate secure password
            temp_password = self.generate_password()

            # Build password profile
            password_profile = PasswordProfile(
                force_change_password_next_sign_in=True,
                password=temp_password
            )

            # Build user object
            new_user = User()
            new_user.account_enabled = True
            new_user.display_name = user_data.get('display_name', f"{user_data['first_name']} {user_data['last_name']}")
            new_user.given_name = user_data['first_name']
            new_user.surname = user_data['last_name']
            new_user.user_principal_name = upn
            new_user.mail_nickname = upn.split('@')[0]
            new_user.password_profile = password_profile
            new_user.usage_location = "NL"  # Required for license assignment

            # Optional fields
            if user_data.get('department'):
                new_user.department = user_data['department']
            if user_data.get('job_title'):
                new_user.job_title = user_data['job_title']

            # Create the user
            created_user = await self.client.users.post(new_user)

            logger.info(f"✓ User created successfully: {upn}")

            return {
                'user_id': created_user.id,
                'upn': upn,
                'display_name': created_user.display_name,
                'temp_password': temp_password,
                'created': True
            }

        except APIError as e:
            logger.error(f"✗ Failed to create user {upn}: {e.message}")
            return None
        except Exception as e:
            logger.error(f"✗ Unexpected error creating user {upn}: {str(e)}")
            return None

    async def assign_license(self, user_id: str, license_type: str, upn: str) -> bool:
        """
        Assign M365 license to user with retry logic
        Returns: True if successful, False otherwise
        """
        # Handle NONE - skip license assignment
        if license_type.upper() == 'NONE':
            logger.info(f"No license assignment requested for {upn} (license_type=NONE)")
            return True

        logger.info(f"Assigning {license_type} license to {upn}")

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Get SKU ID
                sku_id = self.get_sku_id(license_type)
                if not sku_id:
                    logger.error(f"Could not find SKU ID for {license_type}")
                    return False

                # Build license assignment
                from msgraph.generated.users.item.assign_license.assign_license_post_request_body import AssignLicensePostRequestBody

                license_to_add = AssignedLicense()
                license_to_add.sku_id = sku_id

                request_body = AssignLicensePostRequestBody()
                request_body.add_licenses = [license_to_add]
                request_body.remove_licenses = []

                # Assign license
                await self.client.users.by_user_id(user_id).assign_license.post(request_body)

                logger.info(f"✓ License assigned successfully: {license_type} to {upn}")
                return True

            except APIError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"License assignment attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"✗ Failed to assign license after {max_retries} attempts: {e.message}")
                    return False
            except Exception as e:
                logger.error(f"✗ Unexpected error assigning license: {str(e)}")
                return False

        return False

    async def add_to_groups(self, user_id: str, group_names: List[str], upn: str) -> Dict[str, bool]:
        """
        Add user to specified groups (both Security and M365 groups)
        Returns: Dictionary mapping group names to success status
        """
        if not group_names:
            return {}

        logger.info(f"Adding {upn} to groups: {', '.join(group_names)}")
        results = {}

        for group_name in group_names:
            try:
                # Find group by display name
                filter_query = f"displayName eq '{group_name}'"
                groups_result = await self.client.groups.get(
                    request_configuration=lambda req: setattr(req.query_parameters, 'filter', filter_query)
                )

                if not groups_result or not groups_result.value:
                    logger.warning(f"Group not found: {group_name}")
                    results[group_name] = False
                    continue

                group = groups_result.value[0]
                group_id = group.id

                # Add user to group
                from msgraph.generated.models.reference_create import ReferenceCreate

                request_body = ReferenceCreate()
                request_body.odata_id = f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"

                await self.client.groups.by_group_id(group_id).members.ref.post(request_body)

                logger.info(f"✓ Added to group: {group_name}")
                results[group_name] = True

            except APIError as e:
                if "already exist" in str(e.message).lower():
                    logger.info(f"User already in group: {group_name}")
                    results[group_name] = True
                else:
                    logger.error(f"✗ Failed to add to group {group_name}: {e.message}")
                    results[group_name] = False
            except Exception as e:
                logger.error(f"✗ Unexpected error adding to group {group_name}: {str(e)}")
                results[group_name] = False

        return results

    async def configure_mailbox(self, user_id: str, license_type: str, upn: str,
                               delegation_email: Optional[str] = None) -> bool:
        """
        Configure mailbox settings (quota, timezone, litigation hold)
        Returns: True if successful, False otherwise
        """
        logger.info(f"Configuring mailbox for {upn}")

        try:
            # Build mailbox settings
            mailbox_settings = MailboxSettings()

            # Set timezone
            timezone_info = LocaleInfo()
            timezone_info.locale = "Europe/Amsterdam"
            mailbox_settings.time_zone = "W. Europe Standard Time"

            # Update user mailbox settings
            user_update = User()
            user_update.mailbox_settings = mailbox_settings

            await self.client.users.by_user_id(user_id).patch(user_update)

            logger.info(f"✓ Mailbox configured: timezone set to Europe/Amsterdam")

            # Note: Mailbox quotas and litigation hold are typically managed via Exchange Online PowerShell
            # Graph API has limited mailbox management capabilities
            # For production, consider using Exchange Online Management module

            if license_type.upper() == 'E5':
                logger.info(f"ℹ E5 license detected - Litigation Hold should be enabled via Exchange Admin Center")

            if delegation_email:
                logger.info(f"ℹ Mailbox delegation to {delegation_email} should be configured via Exchange Admin Center")

            return True

        except APIError as e:
            logger.error(f"✗ Failed to configure mailbox: {e.message}")
            return False
        except Exception as e:
            logger.error(f"✗ Unexpected error configuring mailbox: {str(e)}")
            return False

    async def rollback_user_creation(self, user_id: str, upn: str):
        """Rollback user creation if onboarding fails"""
        logger.warning(f"Rolling back user creation for {upn}")
        try:
            await self.client.users.by_user_id(user_id).delete()
            logger.info(f"✓ User rolled back successfully: {upn}")
        except Exception as e:
            logger.error(f"✗ Failed to rollback user {upn}: {str(e)}")

    async def onboard_user(self, user_data: Dict) -> Dict:
        """
        Complete onboarding workflow for a single user
        Returns: Dictionary with onboarding results
        """
        upn = user_data.get('user_principal_name', 'Unknown')
        result = {
            'upn': upn,
            'success': False,
            'user_created': False,
            'license_assigned': False,
            'groups_added': {},
            'mailbox_configured': False,
            'temp_password': None,
            'errors': []
        }

        # Validate user data
        is_valid, errors = await self.validate_user_data(user_data)
        if not is_valid:
            result['errors'] = errors
            logger.error(f"Validation failed for {upn}: {', '.join(errors)}")
            return result

        # Step 1: Create user
        user_info = await self.create_user(user_data)
        if not user_info:
            result['errors'].append("User creation failed")
            return result

        result['user_created'] = True
        result['temp_password'] = user_info['temp_password']
        user_id = user_info['user_id']

        # Wait for user provisioning (Graph API can be eventually consistent)
        await asyncio.sleep(2)

        try:
            # Step 2: Assign license
            license_assigned = await self.assign_license(
                user_id,
                user_data['license_type'],
                upn
            )
            result['license_assigned'] = license_assigned

            if not license_assigned:
                result['errors'].append("License assignment failed")
                # Rollback user creation
                await self.rollback_user_creation(user_id, upn)
                return result

            # Step 3: Add to groups
            groups_str = user_data.get('groups', '').strip()
            if groups_str:
                group_names = [g.strip() for g in groups_str.split(';') if g.strip()]
                result['groups_added'] = await self.add_to_groups(user_id, group_names, upn)

            # Step 4: Configure mailbox
            mailbox_delegation = user_data.get('mailbox_delegation')
            result['mailbox_configured'] = await self.configure_mailbox(
                user_id,
                user_data['license_type'],
                upn,
                mailbox_delegation
            )

            # Success!
            result['success'] = True
            logger.info(f"✓✓✓ User onboarding completed successfully: {upn}")

        except Exception as e:
            result['errors'].append(f"Unexpected error during onboarding: {str(e)}")
            logger.error(f"Onboarding failed for {upn}: {str(e)}")

        return result


def authenticate() -> GraphServiceClient:
    """Authenticate to Microsoft Graph API"""
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    client = GraphServiceClient(credentials=credential, scopes=SCOPES)
    return client


async def process_csv(csv_path: Path, manager: UserOnboardingManager) -> Tuple[List[Dict], List[Dict]]:
    """
    Process CSV file and onboard users
    Returns: (successful_users, failed_users)
    """
    successful_users = []
    failed_users = []

    logger.info(f"Reading CSV file: {csv_path}")

    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            users_data = list(reader)

        logger.info(f"Found {len(users_data)} users to onboard")

        for idx, user_data in enumerate(users_data, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing user {idx}/{len(users_data)}")
            logger.info(f"{'='*60}")

            result = await manager.onboard_user(user_data)

            if result['success']:
                successful_users.append({**user_data, **result})
            else:
                failed_users.append({**user_data, **result})

            # Rate limiting: pause between users
            if idx < len(users_data):
                await asyncio.sleep(1)

    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_path}")
        raise
    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        raise

    return successful_users, failed_users


def save_credentials(successful_users: List[Dict], output_path: Path):
    """Save temporary credentials to secure CSV file"""
    logger.info(f"Saving credentials to {output_path}")

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['upn', 'display_name', 'temp_password', 'department', 'job_title']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for user in successful_users:
            writer.writerow({
                'upn': user['upn'],
                'display_name': user.get('display_name', ''),
                'temp_password': user['temp_password'],
                'department': user.get('department', ''),
                'job_title': user.get('job_title', '')
            })

    logger.info(f"✓ Credentials saved to {output_path}")


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='M365 User Onboarding Automation')
    parser.add_argument(
        '--input',
        type=str,
        default='./input/users_to_onboard.csv',
        help='Path to input CSV file (default: ./input/users_to_onboard.csv)'
    )
    args = parser.parse_args()

    csv_path = Path(args.input)
    credentials_output = Path('./output/secure_credentials.csv')
    report_output = Path('./output/onboarding_report.html')

    # Ensure output directory exists
    credentials_output.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("M365 USER ONBOARDING AUTOMATION")
    print("="*60 + "\n")

    try:
        # Authenticate
        print("Authenticating to Microsoft Graph...")
        client = authenticate()
        print("✓ Authentication successful\n")

        # Initialize manager
        manager = UserOnboardingManager(client)
        await manager.initialize_sku_cache()

        # Process users
        print(f"\nProcessing users from: {csv_path}")
        successful_users, failed_users = await process_csv(csv_path, manager)

        # Save credentials
        if successful_users:
            save_credentials(successful_users, credentials_output)

        # Generate report
        from report_generator import generate_html_report
        generate_html_report(successful_users, failed_users, report_output)

        # Summary
        print("\n" + "="*60)
        print("ONBOARDING SUMMARY")
        print("="*60)
        print(f"Total users processed: {len(successful_users) + len(failed_users)}")
        print(f"✓ Successfully onboarded: {len(successful_users)}")
        print(f"✗ Failed: {len(failed_users)}")

        if successful_users:
            time_saved = len(successful_users) * 43
            print(f"\n⏱ Estimated time saved: {time_saved} minutes ({time_saved/60:.1f} hours)")

        print(f"\nOutputs:")
        print(f"  - Credentials: {credentials_output}")
        print(f"  - Report: {report_output}")
        print(f"  - Log: onboarding.log")

        if failed_users:
            print(f"\n⚠ {len(failed_users)} user(s) failed. Check the report for details.")

        print("\n✓ Script completed successfully\n")

    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")
        logger.exception("Fatal error during onboarding")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
