# -*-coding:utf-8-*-

import datetime
import requests
import json
import mail
import yaml

from jira import JIRA
from jinja2 import Environment, FileSystemLoader


with open("config.yaml") as f:
    try:
        config = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print exc


server = JIRA(server=config['jira']['server'],
              basic_auth=(config['jira']['auth']['username'],
                          config['jira']['auth']['password']))


def get_jira_issues(filters, fields=None):
    issues = server.search_issues(filters, fields=fields)

    cells = []
    
    for issue in issues:
        assignee = issue.fields.assignee.displayName if issue.fields.assignee else ""
        link = "https://service.ustack.com/browse/%s" % issue.key
        last_comment = issue.fields.comment.comments[-1].body[0:50]+"..." if issue.fields.comment.comments else ""
        org = issue.fields.customfield_10002[0].name if issue.fields.customfield_10002 else ""
        cell = dict(
            key = issue.key,
            link = link,
            org = org,
            summary = issue.fields.summary,
            status = issue.fields.status.name,
            reporter = issue.fields.reporter.displayName,
            assignee = assignee,
            created = issue.fields.created[0:10],
            last_comment = last_comment
        )

        cells.append(cell)

    cells.sort(key=lambda x: x['org'])

    return cells


updated_cells = get_jira_issues("project = 同方有云工单 AND updatedDate >= startOfDay() AND updatedDate  <= endOfDay() ",
                                fields="summary,comment,assignee,customfield_10002,status,reporter,created,updated")

non_updated_cells = get_jira_issues("project = 同方有云工单 AND updatedDate < startOfDay() AND status != Pending AND resolution = Unresolved",
                                    fields="summary,comment,assignee,customfield_10002,status,reporter,created,updated")


file_loader = FileSystemLoader('.')
env = Environment(loader=file_loader)
template = env.get_template('report.html')

#date_end = strtime(datetime.datetime.now(), "%Y-%m-%d")
#date_begin = strtime(datetime.datetime.now() - datetime.timedelta(days=7), "%Y-%m-%d")
#subject = u"[%s~%s]运维周报" % (date_begin, date_end)

date = datetime.date.today().strftime("%Y-%m-%d")
subject = u"运维日报"
mail_subject = u"[%s]%s" % (date, subject)

mail_result = template.render(subject=subject, date=date,
                              updated_cells=updated_cells,
                              non_updated_cells=non_updated_cells)
body = mail_result.encode(encoding='utf_8')

c = mail.EmailBackend(host=config['smtp']['host'],
                      port=config['smtp']['port'],
                      use_tls=config['smtp']['use_tls'],
                      use_ssl=config['smtp']['use_ssl'],
                      username=config['smtp']['username'],
                      password=config['smtp']['password'],
                      from_email=config['smtp']['from_email'])

c.send_message(config['recipients'], mail_subject, body)
