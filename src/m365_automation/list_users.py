#!/usr/bin/env python3
"""
Microsoft Graph API - List All Users
Demonstrates authentication and basic user querying
"""

import asyncio
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.users_request_builder import UsersRequestBuilder
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET

def authenticate():
    """
    Authenticate to Microsoft Graph using app credentials
    """
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    
    # Create Graph client with application permissions
    scopes = ['https://graph.microsoft.com/.default']
    client = GraphServiceClient(credentials=credential, scopes=scopes)
    
    return client

async def list_all_users(client):
    """
    Retrieve and display all users in the tenant with full properties
    """
    print("\n" + "="*60)
    print("MICROSOFT 365 USERS - SOLIDSUPPORT TENANT")
    print("="*60 + "\n")
    
    # Query configuration for the SDK version you have
    query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(
        select=['displayName', 'userPrincipalName', 'mail', 'accountEnabled', 
                'userType', 'jobTitle', 'department', 'officeLocation', 'createdDateTime']
    )
    
    request_config = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
        query_parameters=query_params
    )
    
    # Query all users with explicit properties
    users = await client.users.get(request_configuration=request_config)
    
    if not users or not users.value:
        print("No users found in tenant.")
        return
    
    print(f"Total users found: {len(users.value)}\n")
    
    for user in users.value:
        print(f"Display Name: {user.display_name}")
        print(f"UPN: {user.user_principal_name}")
        print(f"Email: {user.mail or 'No email configured'}")
        print(f"Account Enabled: {user.account_enabled}")
        print(f"User Type: {user.user_type}")
        print(f"Job Title: {user.job_title or 'Not specified'}")
        print(f"Department: {user.department or 'Not specified'}")
        print(f"Office: {user.office_location or 'Not specified'}")
        print(f"Created: {user.created_date_time}")
        print("-" * 60)

async def main():
    """
    Main execution
    """
    try:
        print("Authenticating to Microsoft Graph...")
        client = authenticate()
        print("✓ Authentication successful\n")
        
        await list_all_users(client)
        
        print("\n✓ Script completed successfully")
        
    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
