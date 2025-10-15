#!/usr/bin/env python3
"""
HTML Report Generator for User Onboarding
Generates comprehensive reports with statistics and error details
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def generate_html_report(successful_users: List[Dict], failed_users: List[Dict], output_path: Path):
    """
    Generate an HTML report showing onboarding results
    """
    total_users = len(successful_users) + len(failed_users)
    success_count = len(successful_users)
    failure_count = len(failed_users)
    success_rate = (success_count / total_users * 100) if total_users > 0 else 0
    time_saved = success_count * 43  # Minutes per user

    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M365 Onboarding Report - {datetime.now().strftime("%Y-%m-%d")}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
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
        .primary {{ color: #007bff; }}
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
            border-bottom: 3px solid #667eea;
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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

        .badge-info {{
            background: #d1ecf1;
            color: #0c5460;
        }}

        .error-details {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}

        .error-details strong {{
            color: #856404;
        }}

        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }}

        .empty-state svg {{
            width: 100px;
            height: 100px;
            margin-bottom: 20px;
            opacity: 0.5;
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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }}

        .time-saved {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
        }}

        .time-saved h3 {{
            font-size: 1.5em;
            margin-bottom: 10px;
        }}

        .time-saved p {{
            font-size: 2.5em;
            font-weight: bold;
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
            <h1>M365 User Onboarding Report</h1>
            <p>Generated on {report_time}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number primary">{total_users}</div>
                <div class="stat-label">Total Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number success">{success_count}</div>
                <div class="stat-label">Successful</div>
            </div>
            <div class="stat-card">
                <div class="stat-number danger">{failure_count}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number warning">{success_rate:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>

        <div class="content">
            {"" if time_saved == 0 else f'''
            <div class="time-saved">
                <h3>⏱ Time Saved Through Automation</h3>
                <p>{time_saved} minutes</p>
                <p style="font-size: 1.2em; margin-top: 10px;">({time_saved/60:.1f} hours @ 43 min/user)</p>
            </div>
            '''}

            <div class="section">
                <h2 class="section-title">✓ Successfully Onboarded Users</h2>
                {generate_success_table(successful_users) if successful_users else '<div class="empty-state"><p>No successful onboardings</p></div>'}
            </div>

            <div class="section">
                <h2 class="section-title">✗ Failed Onboardings</h2>
                {generate_failure_table(failed_users) if failed_users else '<div class="empty-state"><p>No failures - Perfect execution!</p></div>'}
            </div>
        </div>

        <div class="footer">
            <p><strong>Supreme Automation</strong> - M365 Management Suite</p>
            <p style="margin-top: 10px;">
                <a href="#" class="export-btn" onclick="window.print(); return false;">Print Report</a>
                <a href="secure_credentials.csv" class="export-btn">Download Credentials CSV</a>
            </p>
        </div>
    </div>
</body>
</html>
"""

    # Write HTML report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ HTML report generated: {output_path}")

    # Also export failed users to CSV for manual intervention
    if failed_users:
        failed_csv_path = output_path.parent / 'failed_onboardings.csv'
        export_failed_users_csv(failed_users, failed_csv_path)


def generate_success_table(successful_users: List[Dict]) -> str:
    """Generate HTML table for successful users"""
    if not successful_users:
        return ""

    rows = ""
    for user in successful_users:
        groups_text = ", ".join(user.get('groups_added', {}).keys()) or "None"
        mailbox_badge = '<span class="badge badge-success">✓</span>' if user.get('mailbox_configured') else '<span class="badge badge-danger">✗</span>'

        rows += f"""
        <tr>
            <td><strong>{user.get('upn', 'N/A')}</strong></td>
            <td>{user.get('display_name', 'N/A')}</td>
            <td>{user.get('department', 'N/A')}</td>
            <td>{user.get('job_title', 'N/A')}</td>
            <td><span class="badge badge-info">{user.get('license_type', 'N/A')}</span></td>
            <td>{groups_text}</td>
            <td>{mailbox_badge}</td>
        </tr>
        """

    return f"""
    <table>
        <thead>
            <tr>
                <th>User Principal Name</th>
                <th>Display Name</th>
                <th>Department</th>
                <th>Job Title</th>
                <th>License</th>
                <th>Groups</th>
                <th>Mailbox</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    """


def generate_failure_table(failed_users: List[Dict]) -> str:
    """Generate HTML table for failed users with error details"""
    if not failed_users:
        return ""

    rows = ""
    for user in failed_users:
        errors = user.get('errors', [])
        error_text = "<br>".join([f"• {err}" for err in errors]) if errors else "Unknown error"

        rows += f"""
        <tr>
            <td><strong>{user.get('upn', 'N/A')}</strong></td>
            <td>{user.get('display_name', 'N/A')}</td>
            <td><span class="badge badge-danger">Failed</span></td>
            <td>
                <div class="error-details">
                    <strong>Errors:</strong><br>
                    {error_text}
                </div>
            </td>
        </tr>
        """

    return f"""
    <table>
        <thead>
            <tr>
                <th>User Principal Name</th>
                <th>Display Name</th>
                <th>Status</th>
                <th>Error Details</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    """


def export_failed_users_csv(failed_users: List[Dict], output_path: Path):
    """Export failed users to CSV for manual intervention"""
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['upn', 'first_name', 'last_name', 'department', 'job_title',
                     'license_type', 'error_reasons']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for user in failed_users:
            error_reasons = "; ".join(user.get('errors', []))
            writer.writerow({
                'upn': user.get('upn', ''),
                'first_name': user.get('first_name', ''),
                'last_name': user.get('last_name', ''),
                'department': user.get('department', ''),
                'job_title': user.get('job_title', ''),
                'license_type': user.get('license_type', ''),
                'error_reasons': error_reasons
            })

    print(f"✓ Failed users CSV exported: {output_path}")
