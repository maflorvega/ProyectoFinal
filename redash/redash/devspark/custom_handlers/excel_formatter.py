import json
from flask import request, make_response
from flask_login import login_required
from redash.wsgi import app
from redash.devspark import excel_reports
from redash.devspark.custom_tasks import report_tasks


@app.route('/api/dashboard/generate_excel', methods=['POST'])
def generate_excel():
    """
    Handler for simple Excel reports.
    """
    data = request.json

    report = excel_reports.ExcelReport()
    report.add_cover(
        data['filters'],  # Filters used
        [sheet['meta']['name'] for sheet in data['sheets']]  # Sheet names
    )

    for sheet in data['sheets']:
        report.add_sheet(
            sheet['meta']['name'],
            [{
                'name': sheet['meta']['name'],               # Sheet name
                'columns': sheet['meta']['columnNames'],     # Column names
                'rows': sheet['rows'],                       # Data rows
                'description': sheet['meta']['description'], # Sheet description
                'autofilter': sheet['meta']['autofilter']    # Autofilter
            }]
        )

    output = make_response(report.finish().getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=pp.xlsx"

    return output


@app.route('/api/reports/excel_by_month', methods=['POST'])
def excel_by_month():
    """
    Generate MoM report.
    """
    data = request.json
    app.logger.debug(json.dumps(data))
    report_tasks.report_by_month_task.delay(
        data['selectedMonths'],
        'p_startdate',
        'p_enddate',
        data['widgets'],
        data['searchParams'],
        data['email'],
        ftp="",
        autoreport=0
    )

    return '{"status": "Task queued"}', 200


@app.route('/api/reports/autoreport', methods=['POST'])
def autoreport():
    """
    Generate the autoreport for example for MG_Summary Dashboard.
    Generate the report for Listglobally and store in FTP.
    """
    data = request.json
    app.logger.debug(json.dumps(data))
    report_tasks.report_by_month_task.delay(
        data['selectedMonths'],
        'p_startdate',
        'p_enddate',
        data['widgets'],
        data['searchParams'],
        data['email'],
        data['ftp'],
        autoreport=1
    )

    return '{"status": "Task queued"}', 200
