#!/usr/bin/env python3
"""
Azure Health Report Generator
Generates comprehensive HTML reports for Azure resource monitoring
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict


def generate_azure_health_report(
    vm_metrics: List[Dict],
    cost_analysis: Dict,
    security_alerts: List[Dict],
    output_path: Path,
    all_resources: List[Dict] = None
):
    """
    Generate an HTML health report for Azure resources
    """
    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate summary statistics
    total_vms = len([vm for vm in vm_metrics if 'error' not in vm])
    running_vms = len([vm for vm in vm_metrics if vm.get('power_state') == 'running'])
    vms_with_alerts = len([vm for vm in vm_metrics if vm.get('alerts')])
    
    # Security status
    active_security_alerts = len([a for a in security_alerts if a.get('status') == 'Active'])
    
    # Cost status
    cost_status = cost_analysis.get('status', 'Unknown')
    budget_percent = cost_analysis.get('budget_used_percent', 0)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Azure Health Report - {datetime.now().strftime("%Y-%m-%d")}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0078d4 0%, #00bcf2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #0078d4 0%, #00bcf2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }}

        .stat-number {{
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .stat-label {{
            font-size: 1.1em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .success {{ color: #28a745; }}
        .danger {{ color: #dc3545; }}
        .primary {{ color: #0078d4; }}
        .warning {{ color: #ffc107; }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #0078d4;
            color: #333;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}

        thead {{
            background: linear-gradient(135deg, #0078d4 0%, #00bcf2 100%);
            color: white;
        }}

        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}

        th {{
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.5px;
        }}

        tbody tr:hover {{
            background: #f8f9fa;
        }}

        tbody tr:last-child td {{
            border-bottom: none;
        }}

        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}

        .badge-danger {{
            background: #f8d7da;
            color: #721c24;
        }}

        .badge-warning {{
            background: #fff3cd;
            color: #856404;
        }}

        .badge-info {{
            background: #d1ecf1;
            color: #0c5460;
        }}

        .badge-running {{
            background: #d4edda;
            color: #155724;
        }}

        .badge-stopped {{
            background: #f8d7da;
            color: #721c24;
        }}

        .alert-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}

        .alert-box strong {{
            color: #856404;
        }}

        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }}

        .export-btn {{
            display: inline-block;
            background: linear-gradient(135deg, #0078d4 0%, #00bcf2 100%);
            color: white;
            padding: 12px 30px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 600;
            margin: 10px;
            transition: transform 0.3s ease;
        }}

        .export-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0, 120, 212, 0.4);
        }}

        .cost-meter {{
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}

        .cost-meter-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #ffc107 70%, #dc3545 100%);
            transition: width 0.5s ease;
        }}

        .metric-value {{
            font-size: 1.2em;
            font-weight: bold;
            color: #0078d4;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .export-btn {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ Azure Health Report</h1>
            <p>Generated on {report_time}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number primary">{total_vms}</div>
                <div class="stat-label">Total VMs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number success">{running_vms}</div>
                <div class="stat-label">Running</div>
            </div>
            <div class="stat-card">
                <div class="stat-number {'warning' if vms_with_alerts > 0 else 'success'}">{vms_with_alerts}</div>
                <div class="stat-label">Alerts</div>
            </div>
            <div class="stat-card">
                <div class="stat-number {'danger' if active_security_alerts > 0 else 'success'}">{active_security_alerts}</div>
                <div class="stat-label">Security Alerts</div>
            </div>
        </div>

        <div class="content">
            {generate_cost_section(cost_analysis)}

            {generate_vm_section(vm_metrics)}

            {generate_security_section(security_alerts)}

            {generate_resources_section(all_resources) if all_resources else ''}
        </div>

        <div class="footer">
            <p><strong>Supreme Automation</strong> - Azure Monitoring Suite</p>
            <p style="margin-top: 10px;">
                <a href="#" class="export-btn" onclick="window.print(); return false;">Print Report</a>
            </p>
        </div>
    </div>
</body>
</html>
"""

    # Write HTML report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ Azure health report generated: {output_path}")


def generate_cost_section(cost_analysis: Dict) -> str:
    """Generate cost analysis section"""
    if 'error' in cost_analysis:
        return f"""
        <div class="section">
            <h2 class="section-title">💰 Cost Analysis</h2>
            <div class="alert-box">
                <strong>Note:</strong> {cost_analysis.get('note', 'Cost data unavailable')}
            </div>
        </div>
        """
    
    total = cost_analysis.get('total_cost', 0)
    budget = cost_analysis.get('budget', 0)
    percent = cost_analysis.get('budget_used_percent', 0)
    currency = cost_analysis.get('currency', 'EUR')
    remaining = cost_analysis.get('budget_remaining', 0)
    
    return f"""
    <div class="section">
        <h2 class="section-title">💰 Cost Analysis</h2>
        <div style="padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <h3>Period: {cost_analysis.get('period', 'N/A')}</h3>
            <p style="font-size: 1.5em; margin: 20px 0;">
                <strong>{total:.2f} {currency}</strong> of <strong>{budget:.2f} {currency}</strong>
            </p>
            <div class="cost-meter">
                <div class="cost-meter-fill" style="width: {min(percent, 100):.1f}%;"></div>
            </div>
            <p style="margin-top: 10px;">
                <span class="badge badge-{'success' if percent < 80 else 'warning' if percent < 100 else 'danger'}">
                    {percent:.1f}% of budget used
                </span>
                <strong style="margin-left: 20px;">Remaining: {remaining:.2f} {currency}</strong>
            </p>
            {f'<div class="alert-box" style="margin-top: 20px;"><strong>Note:</strong> {cost_analysis.get("note")}</div>' if cost_analysis.get('note') else ''}
        </div>
    </div>
    """


def generate_vm_section(vm_metrics: List[Dict]) -> str:
    """Generate VM metrics section"""
    if not vm_metrics:
        return """
        <div class="section">
            <h2 class="section-title">🖥️ Virtual Machines</h2>
            <div class="empty-state"><p>No VMs found</p></div>
        </div>
        """
    
    rows = ""
    for vm in vm_metrics:
        if 'error' in vm:
            rows += f"""
            <tr>
                <td><strong>{vm['name']}</strong></td>
                <td colspan="5"><span class="badge badge-danger">Error: {vm['error']}</span></td>
            </tr>
            """
            continue
        
        power_state_badge = f'<span class="badge badge-running">Running</span>' if vm.get('power_state') == 'running' else f'<span class="badge badge-stopped">{vm.get("power_state", "Unknown")}</span>'
        
        metrics = vm.get('metrics', {})
        cpu = metrics.get('cpu_percent')
        cpu_display = f"{cpu:.1f}%" if cpu is not None else "N/A"
        
        status_badge = f'<span class="badge badge-success">Healthy</span>' if vm.get('status') == 'Healthy' else f'<span class="badge badge-warning">Warning</span>'
        
        alerts_display = ""
        if vm.get('alerts'):
            alerts_display = "<br>".join([f"⚠️ {alert}" for alert in vm['alerts']])
        
        rows += f"""
        <tr>
            <td><strong>{vm['name']}</strong></td>
            <td>{power_state_badge}</td>
            <td>{vm.get('vm_size', 'N/A')}</td>
            <td>{vm.get('location', 'N/A')}</td>
            <td><span class="metric-value">{cpu_display}</span></td>
            <td>{status_badge}</td>
        </tr>
        {f'<tr><td colspan="6" class="alert-box">{alerts_display}</td></tr>' if alerts_display else ''}
        """
    
    return f"""
    <div class="section">
        <h2 class="section-title">🖥️ Virtual Machines</h2>
        <table>
            <thead>
                <tr>
                    <th>VM Name</th>
                    <th>Power State</th>
                    <th>Size</th>
                    <th>Location</th>
                    <th>CPU Usage</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """


def generate_security_section(security_alerts: List[Dict]) -> str:
    """Generate security alerts section"""
    if not security_alerts:
        return """
        <div class="section">
            <h2 class="section-title">🛡️ Security Alerts</h2>
            <div class="empty-state"><p>No security data available</p></div>
        </div>
        """
    
    # Check if Security Center is unavailable
    if security_alerts[0].get('status') in ['Unavailable', 'Error']:
        return f"""
        <div class="section">
            <h2 class="section-title">🛡️ Security Alerts</h2>
            <div class="alert-box">
                <strong>Note:</strong> {security_alerts[0].get('note', 'Security Center data unavailable')}
            </div>
        </div>
        """
    
    # Check if no alerts
    if security_alerts[0].get('status') == 'No active alerts':
        return """
        <div class="section">
            <h2 class="section-title">🛡️ Security Alerts</h2>
            <div style="padding: 30px; text-align: center; background: #d4edda; border-radius: 8px;">
                <h3 style="color: #155724;">✓ No Active Security Alerts</h3>
                <p style="color: #155724; margin-top: 10px;">All systems secure</p>
            </div>
        </div>
        """
    
    # Active alerts
    rows = ""
    for alert in security_alerts:
        severity_class = {
            'High': 'danger',
            'Medium': 'warning',
            'Low': 'info'
        }.get(alert.get('severity', 'Medium'), 'info')
        
        rows += f"""
        <tr>
            <td><strong>{alert.get('name', 'Unknown')}</strong></td>
            <td><span class="badge badge-{severity_class}">{alert.get('severity', 'Unknown')}</span></td>
            <td>{alert.get('status', 'Unknown')}</td>
            <td>{alert.get('description', 'No description available')}</td>
            <td>{alert.get('detected_time', 'N/A')}</td>
        </tr>
        """
    
    return f"""
    <div class="section">
        <h2 class="section-title">🛡️ Security Alerts</h2>
        <table>
            <thead>
                <tr>
                    <th>Alert Name</th>
                    <th>Severity</th>
                    <th>Status</th>
                    <th>Description</th>
                    <th>Detected</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """


def generate_resources_section(all_resources: List[Dict]) -> str:
    """Generate all resources section"""
    if not all_resources:
        return """
        <div class="section">
            <h2 class="section-title">📦 All Resources</h2>
            <div class="empty-state"><p>No resources found</p></div>
        </div>
        """

    # Group resources by type
    resources_by_type = {}
    for resource in all_resources:
        res_type = resource.get('type', 'Unknown')
        if res_type not in resources_by_type:
            resources_by_type[res_type] = []
        resources_by_type[res_type].append(resource)

    # Generate summary cards
    total_resources = len(all_resources)
    total_types = len(resources_by_type)
    resource_groups = len(set(r.get('resource_group', 'Unknown') for r in all_resources))

    summary_html = f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
        <div class="stat-card">
            <div class="stat-number primary">{total_resources}</div>
            <div class="stat-label">Total Resources</div>
        </div>
        <div class="stat-card">
            <div class="stat-number success">{total_types}</div>
            <div class="stat-label">Resource Types</div>
        </div>
        <div class="stat-card">
            <div class="stat-number info">{resource_groups}</div>
            <div class="stat-label">Resource Groups</div>
        </div>
    </div>
    """

    # Generate table rows grouped by type
    rows = ""
    for res_type, resources in sorted(resources_by_type.items(), key=lambda x: len(x[1]), reverse=True):
        # Add type header row
        rows += f"""
        <tr style="background: #e3f2fd;">
            <td colspan="4"><strong>{res_type}</strong> ({len(resources)} resources)</td>
        </tr>
        """

        # Add resource rows
        for resource in resources[:20]:  # Limit to first 20 per type to avoid huge tables
            tags_display = ", ".join([f"{k}={v}" for k, v in resource.get('tags', {}).items()][:3]) or "None"
            rows += f"""
            <tr>
                <td style="padding-left: 30px;">{resource.get('name', 'N/A')}</td>
                <td>{resource.get('resource_group', 'N/A')}</td>
                <td>{resource.get('location', 'N/A')}</td>
                <td style="font-size: 0.85em;">{tags_display}</td>
            </tr>
            """

        if len(resources) > 20:
            rows += f"""
            <tr>
                <td colspan="4" style="text-align: center; font-style: italic; color: #666;">
                    ... and {len(resources) - 20} more {res_type} resources
                </td>
            </tr>
            """

    return f"""
    <div class="section">
        <h2 class="section-title">📦 All Resources</h2>
        {summary_html}
        <table>
            <thead>
                <tr>
                    <th>Resource Name</th>
                    <th>Resource Group</th>
                    <th>Location</th>
                    <th>Tags</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """
