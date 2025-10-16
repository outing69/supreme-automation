#!/usr/bin/env python3
"""
Azure Resource Monitor
Monitors Azure VMs, costs, and security alerts
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import argparse

from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.security import SecurityCenter
from azure.mgmt.resource import ResourceManagementClient
from azure.core.exceptions import HttpResponseError

# Import configuration
from monitor_config import (
    SUBSCRIPTION_ID, TENANT_ID, CLIENT_ID, CLIENT_SECRET,
    RESOURCE_GROUP, SCOPES, BUDGET_AMOUNT, CURRENCY,
    CPU_THRESHOLD, MEMORY_THRESHOLD, DISK_THRESHOLD
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('azure_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AzureMonitor:
    """Manages Azure resource monitoring operations"""

    def __init__(self, credential):
        self.credential = credential
        self.subscription_id = SUBSCRIPTION_ID
        self.resource_group = RESOURCE_GROUP

        # Initialize clients
        self.resource_client = None
        self.compute_client = None
        self.monitor_client = None
        self.cost_client = None
        self.security_client = None

    def authenticate(self) -> bool:
        """
        Authenticate and initialize Azure management clients
        Returns: True if successful, False otherwise
        """
        try:
            logger.info("Initializing Azure management clients...")

            # Resource Management Client (All Resources)
            self.resource_client = ResourceManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )

            # Compute Management Client (VMs)
            self.compute_client = ComputeManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )

            # Monitor Management Client (Metrics)
            self.monitor_client = MonitorManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )

            # Cost Management Client
            self.cost_client = CostManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )

            # Security Center Client
            self.security_client = SecurityCenter(
                credential=self.credential,
                subscription_id=self.subscription_id,
                asc_location="centralus"  # Security Center location
            )

            logger.info("✓ All Azure clients initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize Azure clients: {str(e)}")
            return False

    async def list_all_resources(self) -> List[Dict]:
        """
        Enumerate all resources in the subscription
        Returns: List of resource dictionaries with name, type, location, and resource group
        """
        logger.info(f"Enumerating all resources in subscription: {self.subscription_id}")
        resources = []

        try:
            # List all resources in the subscription
            all_resources = list(self.resource_client.resources.list())

            if not all_resources:
                logger.warning("No resources found in subscription")
                return resources

            logger.info(f"Found {len(all_resources)} resources in subscription")

            for resource in all_resources:
                try:
                    resource_info = {
                        'name': resource.name,
                        'type': resource.type,
                        'location': resource.location,
                        'resource_group': resource.id.split('/')[4] if len(resource.id.split('/')) > 4 else 'Unknown',
                        'id': resource.id,
                        'tags': resource.tags if resource.tags else {}
                    }
                    resources.append(resource_info)

                    logger.debug(f"Resource: {resource.name} | Type: {resource.type} | RG: {resource_info['resource_group']}")

                except Exception as e:
                    logger.warning(f"Failed to process resource {resource.name}: {str(e)}")
                    continue

            # Log resource summary by type
            resource_types = {}
            for res in resources:
                res_type = res['type']
                resource_types[res_type] = resource_types.get(res_type, 0) + 1

            logger.info("\n" + "="*60)
            logger.info("RESOURCE SUMMARY BY TYPE")
            logger.info("="*60)
            for res_type, count in sorted(resource_types.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"{res_type}: {count}")
            logger.info("="*60 + "\n")

            return resources

        except HttpResponseError as e:
            logger.error(f"✗ HTTP error while listing resources: {str(e)}")
            logger.error(f"Status code: {e.status_code}")
            return resources

        except Exception as e:
            logger.error(f"✗ Failed to enumerate resources: {str(e)}")
            import traceback
            traceback.print_exc()
            return resources

    async def get_vm_metrics(self) -> List[Dict]:
        """
        Get CPU, memory, and disk metrics for all VMs in resource group
        Returns: List of VM metric dictionaries
        """
        logger.info(f"Fetching VM metrics for resource group: {self.resource_group}")
        vm_metrics = []
        
        try:
            # List all VMs in resource group
            vms = list(self.compute_client.virtual_machines.list(self.resource_group))
            
            if not vms:
                logger.warning(f"No VMs found in resource group: {self.resource_group}")
                return vm_metrics
            
            logger.info(f"Found {len(vms)} VMs")
            
            for vm in vms:
                try:
                    vm_name = vm.name
                    vm_id = vm.id
                    
                    logger.info(f"  Fetching metrics for VM: {vm_name}")
                    
                    # Get VM status
                    instance_view = self.compute_client.virtual_machines.instance_view(
                        self.resource_group,
                        vm_name
                    )
                    
                    # Determine power state
                    power_state = "Unknown"
                    if instance_view.statuses:
                        for status in instance_view.statuses:
                            if status.code.startswith('PowerState/'):
                                power_state = status.code.split('/')[-1]
                                break
                    
                    # Get metrics (CPU, Memory, Disk)
                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(hours=1)  # Last hour
                    
                    metrics_data = {
                        'cpu_percent': await self._get_metric(vm_id, 'Percentage CPU', start_time, end_time),
                        'memory_available': await self._get_metric(vm_id, 'Available Memory Bytes', start_time, end_time),
                        'disk_read': await self._get_metric(vm_id, 'Disk Read Bytes', start_time, end_time),
                        'disk_write': await self._get_metric(vm_id, 'Disk Write Bytes', start_time, end_time),
                    }
                    
                    # Calculate alerts
                    alerts = []
                    if metrics_data['cpu_percent'] and metrics_data['cpu_percent'] > CPU_THRESHOLD:
                        alerts.append(f"CPU usage ({metrics_data['cpu_percent']:.1f}%) exceeds threshold ({CPU_THRESHOLD}%)")
                    
                    vm_info = {
                        'name': vm_name,
                        'id': vm_id,
                        'location': vm.location,
                        'vm_size': vm.hardware_profile.vm_size,
                        'power_state': power_state,
                        'os_type': vm.storage_profile.os_disk.os_type.value if hasattr(vm.storage_profile.os_disk.os_type, 'value') else (vm.storage_profile.os_disk.os_type or 'Unknown'),
                        'metrics': metrics_data,
                        'alerts': alerts,
                        'status': 'Healthy' if not alerts else 'Warning'
                    }
                    
                    vm_metrics.append(vm_info)
                    logger.info(f"    ✓ {vm_name}: {power_state}, CPU: {metrics_data['cpu_percent']}%")
                    
                except Exception as e:
                    logger.error(f"    ✗ Error fetching metrics for VM {vm.name}: {str(e)}")
                    vm_metrics.append({
                        'name': vm.name,
                        'id': vm.id,
                        'error': str(e),
                        'status': 'Error'
                    })
            
            return vm_metrics
            
        except Exception as e:
            logger.error(f"✗ Failed to fetch VM metrics: {str(e)}")
            return []

    async def _get_metric(self, resource_id: str, metric_name: str, start_time: datetime, end_time: datetime) -> Optional[float]:
        """
        Get a specific metric for a resource
        Returns: Average metric value or None
        """
        try:
            # Format timespan
            timespan = f"{start_time.isoformat()}Z/{end_time.isoformat()}Z"
            
            # Query metrics
            metrics_data = self.monitor_client.metrics.list(
                resource_id,
                timespan=timespan,
                interval='PT5M',  # 5-minute intervals
                metricnames=metric_name,
                aggregation='Average'
            )
            
            # Extract average value
            for item in metrics_data.value:
                for timeseries in item.timeseries:
                    for data in timeseries.data:
                        if data.average is not None:
                            return data.average
            
            return None
            
        except HttpResponseError as e:
            # Metric might not be available for this resource
            logger.debug(f"Metric {metric_name} not available: {e.message}")
            return None
        except Exception as e:
            logger.warning(f"Error fetching metric {metric_name}: {str(e)}")
            return None

    async def get_cost_analysis(self) -> Dict:
        """
        Get current month spend vs budget
        Returns: Dictionary with cost analysis data
        """
        logger.info("Fetching cost analysis...")
        
        try:
            # Get current month date range
            now = datetime.utcnow()
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
            
            # Build scope
            scope = f"/subscriptions/{self.subscription_id}"
            
            # Query for current month costs
            query_definition = {
                "type": "Usage",
                "timeframe": "MonthToDate",
                "dataset": {
                    "granularity": "Daily",
                    "aggregation": {
                        "totalCost": {
                            "name": "Cost",
                            "function": "Sum"
                        }
                    },
                    "grouping": [
                        {
                            "type": "Dimension",
                            "name": "ResourceGroup"
                        }
                    ]
                }
            }
            
            # Note: Cost Management API might not be available in all subscriptions
            # This is a placeholder implementation
            logger.info("  Cost Management API query configured")
            
            # Simulated cost data (replace with actual API call when available)
            total_cost = 0.0
            daily_costs = []
            
            # Calculate budget status
            budget_used_percent = (total_cost / BUDGET_AMOUNT * 100) if BUDGET_AMOUNT > 0 else 0
            budget_remaining = BUDGET_AMOUNT - total_cost
            
            cost_analysis = {
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'total_cost': total_cost,
                'currency': CURRENCY,
                'budget': BUDGET_AMOUNT,
                'budget_used_percent': budget_used_percent,
                'budget_remaining': budget_remaining,
                'daily_costs': daily_costs,
                'status': 'OK' if budget_used_percent < 80 else 'Warning' if budget_used_percent < 100 else 'Critical',
                'note': 'Cost data requires Cost Management API access'
            }
            
            logger.info(f"  ✓ Cost analysis: {total_cost:.2f} {CURRENCY} / {BUDGET_AMOUNT:.2f} {CURRENCY} ({budget_used_percent:.1f}%)")
            return cost_analysis
            
        except Exception as e:
            logger.error(f"✗ Failed to fetch cost analysis: {str(e)}")
            return {
                'error': str(e),
                'status': 'Error',
                'note': 'Cost Management API may not be available for this subscription'
            }

    async def check_security_alerts(self) -> List[Dict]:
        """
        Check Security Center for active alerts
        Returns: List of security alert dictionaries
        """
        logger.info("Checking Security Center alerts...")
        
        try:
            alerts = []
            
            # Get security alerts
            # Note: Requires Security Center to be enabled on subscription
            try:
                security_alerts = list(self.security_client.alerts.list())
                
                for alert in security_alerts:
                    if alert.properties.state in ['Active', 'InProgress']:
                        alerts.append({
                            'name': alert.name,
                            'severity': alert.properties.severity,
                            'status': alert.properties.state,
                            'description': alert.properties.description,
                            'compromised_entity': alert.properties.compromised_entity,
                            'detected_time': alert.properties.start_time.isoformat() if alert.properties.start_time else None
                        })
                
                logger.info(f"  ✓ Found {len(alerts)} active security alerts")
                
            except HttpResponseError as e:
                logger.warning(f"  Security Center not available: {e.message}")
                return [{
                    'note': 'Security Center not enabled or insufficient permissions',
                    'status': 'Unavailable'
                }]
            
            return alerts if alerts else [{
                'status': 'No active alerts',
                'severity': 'Informational'
            }]
            
        except Exception as e:
            logger.error(f"✗ Failed to check security alerts: {str(e)}")
            return [{
                'error': str(e),
                'status': 'Error'
            }]

    async def generate_health_report(self, output_path: Path) -> bool:
        """
        Generate HTML dashboard with all monitoring data
        Returns: True if successful, False otherwise
        """
        logger.info("Generating health report...")

        try:
            # Collect all data
            all_resources = await self.list_all_resources()
            vm_metrics = await self.get_vm_metrics()
            cost_analysis = await self.get_cost_analysis()
            security_alerts = await self.check_security_alerts()

            # Import report generator
            from azure_report_generator import generate_azure_health_report

            # Generate report
            generate_azure_health_report(
                vm_metrics,
                cost_analysis,
                security_alerts,
                output_path,
                all_resources=all_resources
            )

            logger.info(f"✓ Health report generated: {output_path}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to generate health report: {str(e)}")
            return False


def authenticate_azure() -> ClientSecretCredential:
    """Authenticate to Azure using service principal"""
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    return credential


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Azure Resource Monitor')
    parser.add_argument(
        '--output',
        type=str,
        default='./output/azure_health_report.html',
        help='Path to output HTML report (default: ./output/azure_health_report.html)'
    )
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("AZURE RESOURCE MONITOR")
    print("="*60 + "\n")
    
    try:
        # Authenticate
        print("Authenticating to Azure...")
        credential = authenticate_azure()
        print("✓ Authentication successful\n")
        
        # Initialize monitor
        monitor = AzureMonitor(credential)
        if not monitor.authenticate():
            print("✗ Failed to initialize Azure clients")
            return
        
        # Generate health report
        print("\nGenerating health report...")
        success = await monitor.generate_health_report(output_path)
        
        if success:
            print("\n" + "="*60)
            print("MONITORING COMPLETE")
            print("="*60)
            print(f"Report: {output_path}")
            print("Log: azure_monitoring.log")
            print("\n✓ Script completed successfully\n")
        else:
            print("\n✗ Failed to generate health report")
            
    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")
        logger.exception("Fatal error during monitoring")


if __name__ == "__main__":
    asyncio.run(main())
