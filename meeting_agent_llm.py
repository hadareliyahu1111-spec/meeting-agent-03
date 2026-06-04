# -*- coding: utf-8 -*-
import base64, json, os
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from groq import Groq

creds = Credentials.from_authorized_user_file('token.json')
gmail = build('gmail', 'v1', credentials=creds)
calendar = build('calendar', 'v3', credentials=creds)
client = Groq(api_key=os.environ['GROQ_API_KEY'])

print('סורק מיילים...')
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
    emails_data.append({'id': msg['id'], 'from': headers.get('From',''), 'subject': headers.get('Subject',''), 'body': body[:300]})

print(f'נמצאו {len(emails_data)} מיילים')
today = datetime.now().strftime('%Y-%m-%d')
prompt = f'''Today is {today}. Analyze the following emails and identify meeting invitations.
Return ONLY valid JSON, no markdown, no backticks:
{{"meetings": [{{"email_id": "...", "from": "...", "date": "YYYY-MM-DD", "time": "HH:MM", "subject": "...", "is_meeting": true}}]}}
Emails: {json.dumps(emails_data, ensure_ascii=False)}'''

print('מזהה הזמנות עם LLM...')
response = client.chat.completions.create(
    model='llama-3.3-70b-versatile',
    messages=[{'role': 'user', 'content': prompt}],
    temperature=0
)
raw = response.choices[0].message.content.strip()
parsed = json.loads(raw[raw.find('{'):raw.rfind('}')+1])
meetings = [m for m in parsed['meetings'] if m.get('is_meeting')]
print(f'זוהו {len(meetings)} הזמנות לפגישה')

summary = []
for meeting in meetings:
    try:
        subj = meeting['subject']
        date = meeting['date']
        time = meeting['time']
        sender = meeting['from']
        dt_start = datetime.strptime(date + ' ' + time, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
        dt_end = dt_start + timedelta(hours=1)
        events = calendar.events().list(calendarId='primary', timeMin=dt_start.isoformat(), timeMax=dt_end.isoformat(), singleEvents=True).execute()
        if events.get('items'):
            msg = MIMEText('Hello, unfortunately the time ' + date + ' at ' + time + ' is already taken. Please suggest another time.', 'plain', 'utf-8')
            msg['to'] = sender
            msg['from'] = 'bdikahadar@gmail.com'
            msg['subject'] = 'Re: ' + subj
            gmail.users().messages().send(userId='me', body={'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}).execute()
            summary.append('תפוס - נשלחה תשובה: ' + subj)
        else:
            event = {'summary': subj, 'start': {'dateTime': dt_start.isoformat(), 'timeZone': 'UTC'}, 'end': {'dateTime': dt_end.isoformat(), 'timeZone': 'UTC'}}
            calendar.events().insert(calendarId='primary', body=event).execute()
            summary.append('נוסף ליומן: ' + subj + ' (' + date + ' ' + time + ')')
    except Exception as e:
        summary.append('שגיאה: ' + str(e))

print('\nסיכום פעולות הסוכן:')
for line in summary:
    print(line)

