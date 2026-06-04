# -*- coding: utf-8 -*-
import base64, json, os, re
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from groq import Groq

creds = Credentials.from_authorized_user_file('token.json')
gmail = build('gmail', 'v1', credentials=creds)
calendar = build('calendar', 'v3', credentials=creds)
client = Groq(api_key=os.environ['GROQ_API_KEY'])

print('���� ������...')
two_days_ago = int((datetime.now() - timedelta(days=2)).timestamp())
results = gmail.users().messages().list(userId='me', q=f'after:{two_days_ago}').execute()
emails_data = []
for msg in results.get('messages', [])[:10]:
    m = gmail.users().messages().get(userId='me', id=msg['id'], format='full').execute()
    headers = {h['name']: h['value'] for h in m['payload']['headers']}
    body = ''
    if 'parts' in m['payload']:
        for part in m['payload']['parts']:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
    else:
        data = m['payload']['body'].get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    raw_from = headers.get('From', '')
    match = re.search(r'[\w.\-+]+@[\w.\-]+', raw_from)
    email_from = match.group(0) if match else raw_from
    emails_data.append({'id': msg['id'], 'from': email_from, 'subject': headers.get('Subject',''), 'body': body[:300]})

print(f'����� {len(emails_data)} ������')
today = datetime.now().strftime('%Y-%m-%d')
prompt = f'''Today is {today}. Analyze the following emails and identify meeting invitations.
Return ONLY valid JSON, no markdown, no backticks:
{{"meetings": [{{"email_id": "...", "from": "...", "date": "YYYY-MM-DD", "time": "HH:MM", "subject": "...", "is_meeting": true}}]}}
Emails: {json.dumps(emails_data, ensure_ascii=False)}'''

print('���� ������ �� LLM...')
response = client.chat.completions.create(
    model='llama-3.3-70b-versatile',
    messages=[{'role': 'user', 'content': prompt}],
    temperature=0
)
raw = response.choices[0].message.content.strip()
parsed = json.loads(raw[raw.find('{'):raw.rfind('}')+1])
meetings = [m for m in parsed['meetings'] if m.get('is_meeting')]
print(f'���� {len(meetings)} ������ ������')

summary = []
for meeting in meetings:
    try:
        subj = meeting['subject']
        date = meeting['date']
        time = meeting['time']
        sender = meeting['from']
        if not sender or '@' not in sender:
            sender = 'bdikahadar@gmail.com'
        dt_start = datetime.strptime(date + ' ' + time.strip(), '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
        dt_end = dt_start + timedelta(hours=1)
        events = calendar.events().list(calendarId='primary', timeMin=dt_start.isoformat(), timeMax=dt_end.isoformat(), singleEvents=True).execute()
        if events.get('items'):
            reply = MIMEText('����, ����� ����� ' + date + ' ���� ' + time + ' ����. ���� ���� ���� ���.', 'plain', 'utf-8')
            reply['to'] = sender
            reply['from'] = 'bdikahadar@gmail.com'
            reply['subject'] = 'Re: ' + subj
            gmail.users().messages().send(userId='me', body={'raw': base64.urlsafe_b64encode(reply.as_bytes()).decode()}).execute()
            summary.append('���� - ����� ����� �-' + sender + ': ' + subj)
        else:
            event = {'summary': subj, 'start': {'dateTime': dt_start.isoformat(), 'timeZone': 'UTC'}, 'end': {'dateTime': dt_end.isoformat(), 'timeZone': 'UTC'}}
            calendar.events().insert(calendarId='primary', body=event).execute()
            summary.append('���� �����: ' + subj + ' (' + date + ' ' + time + ')')
    except Exception as e:
        summary.append('�����: ' + str(e))

print('\n����� ������ �����:')
for line in summary:
    print(line)

