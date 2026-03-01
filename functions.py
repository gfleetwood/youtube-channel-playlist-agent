'''
rec_create(DB, REC_TYPE, Id=3, Name="crypto_report", URL="https://...", Prompt="Find crypto news")
'''

import subprocess
import os
import json
import re
import ast
import resend
import base64
from config import FROM_EMAIL

def _run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()


def _parse(output):
    records = []
    for block in output.split('\n\n'):
        record = {}
        last_key = None
        for line in block.split('\n'):
            if line.startswith('+ '):
                if last_key:
                    record[last_key] += '\n' + line[2:]
            elif ':' in line:
                k, v = line.split(':', 1)
                last_key = k.strip()
                record[last_key] = v.strip()
        if record:
            records.append(record)
    return records


def rec_create(file, rec_type, **kwargs):
    """Insert a new record: rec_create('tasks.rec', 'Task', Name='x', URL='...')"""
    args = []
    for k, v in kwargs.items():
        args.extend(['-f', k, '-v', str(v)])
    _run(['recins', '-t', rec_type] + args + [file])

def rec_read(file, rec_type, query=None):
    """Read records as a list of dicts. Optional recsel expression."""
    cmd = ['recsel', '-t', rec_type]
    if query:
        cmd.extend(['-e', query])
    cmd.append(file)
    return _parse(_run(cmd))

def rec_update(file, rec_type, query, **kwargs):
    """Update fields matching a query: rec_update('tasks.rec', 'Task', "Name = 'x'", LastRun='2026-01-01')"""
    for k, v in kwargs.items():
        _run(['recset', '-t', rec_type, '-e', query, '-f', k, '-S', str(v), file])


def rec_delete(file, rec_type, query):
    """Delete records matching a query: rec_delete('tasks.rec', 'Task', "Name = 'x'")"""
    _run(['recdel', '-t', rec_type, '-e', query, file])

def build_html(body):
    """
    Converts a list of video dicts, a single video dict (with 'title' and 'url' keys),
    or a plain string into a formatted HTML string.
    """
    if isinstance(body, dict):
        body = [body]

    if isinstance(body, list):
        items = "".join(
            f'<li style="margin-bottom:10px;">'
            f'<a href="{v.get("url", "#")}" style="color:#1a73e8;text-decoration:none;font-weight:500;">'
            f'{v.get("title", "Untitled")}</a></li>'
            for v in body
        )
        return (
            '<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">'
            '<h2 style="color:#202124;">Latest Videos</h2>'
            f'<ul style="padding-left:20px;line-height:1.8;">{items}</ul>'
            '</div>'
        )
    return f"<p>{body}</p>"

def send_email(to_email, subject, body, pdf_file_path=None):

    html = body #build_html(body)

    if pdf_file_path is not None:
        with open(pdf_file_path, "rb") as f:
            encoded_pdf = base64.b64encode(f.read()).decode()

        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html,
            "attachments": [{"content": encoded_pdf, "filename": "your_file.pdf"}],
        }
    else:
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html,
        }

    email = resend.Emails.send(params)

    return True

def extract_and_parse_dict(raw_string):
    """
    Extracts a dictionary or list of dictionaries from a string containing
    other characters and converts it into a Python dict or list of dicts.

    # Example usage:
    log_entry = "TIMESTAMP: 2026-02-26 | DATA: {'id': 505, 'active': True} | STATUS: OK"
    result = extract_and_parse_dict(log_entry)
    print(f"Extracted ID: {result['id']}")

    list_entry = "Results: [{'id': 1}, {'id': 2}]"
    result = extract_and_parse_dict(list_entry)
    print(f"First ID: {result[0]['id']}")
    """

    # Find the outermost list '[...]' or dict '{...}', preferring whichever comes first
    list_match = re.search(r'\[.*\]', raw_string, re.DOTALL)
    dict_match = re.search(r'\{.*\}', raw_string, re.DOTALL)

    if list_match and dict_match:
        match = list_match if list_match.start() < dict_match.start() else dict_match
    else:
        match = list_match or dict_match

    if not match:
        return None

    extracted_str = match.group(0)

    try:
        return ast.literal_eval(extracted_str)
    except (ValueError, SyntaxError):
        try:
            return json.loads(extracted_str.replace("'", '"'))
        except json.JSONDecodeError:
            return "Error: Found brackets/braces but content is not a valid dict or list."