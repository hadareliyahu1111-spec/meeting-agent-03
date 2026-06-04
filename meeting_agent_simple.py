import base64, json
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import re

creds = Credentials.from_authorized_user_file('token.json')
gmail = build('gmail', 'v1', credentials=creds)
calendar = build('calendar', 'v3', credentials=creds)

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
    emails_data.append({'id': msg['id'], 'from': headers.get('From',''), 'subject': headers.get('Subject',''), 'body': body})

print(f'נמצאו {len(emails_data)} מיילים')

keywords = ['פגישה', 'ניפגש', 'לקבוע', 'להיפגש', 'meeting', 'schedule']
time_pattern = re.compile(r'(\d{1,2}):(\d{2})')
day_map = {'ראשון':0,'שני':1,'שלישי':2,'רביעי':3,'חמישי':4,'שישי':5,'שבת':6}
today = datetime.now()

summary = []
for email in emails_data:
    text = email['subject'] + ' ' + email['body']
    if not any(k in text for k in keywords):
        continue
    
    time_match = time_pattern.search(text)
    if not time_match:
        continue
    hour = int(time_match.group(1))
    minute = int(time_match.group(2))
    
    meeting_date = today + timedelta(days=1)
    for day_name, day_num in day_map.items():
        if day_name in text:
            days_ahead = (day_num - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            meeting_date = today + timedelta(days=days_ahead)
            break
    if 'מחר' in text:
        meeting_date = today + timedelta(days=1)
    
    dt_start = meeting_date.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=timezone.utc)
    dt_end = dt_start + timedelta(hours=1)
    subj = email['subject']
    sender = email['from']
    
    events = calendar.events().list(calendarId='primary', timeMin=dt_start.isoformat(), timeMax=dt_end.isoformat(), singleEvents=True).execute()
    if events.get('items'):
        msg = MIMEText('שלום, לצערי המועד ' + dt_start.strftime('%Y-%m-%d') + ' בשעה ' + dt_start.strftime('%H:%M') + ' תפוס.', 'plain', 'utf-8')
        msg['to'] = sender
        msg['from'] = 'bdikahadar@gmail.com'
        msg['subject'] = 'Re: ' + subj
        gmail.users().messages().send(userId='me', body={'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}).execute()
        summary.append('תפוס - נשלחה תשובה: ' + subj)
    else:
        event = {'summary': subj, 'start': {'dateTime': dt_start.isoformat(), 'timeZone': 'UTC'}, 'end': {'dateTime': dt_end.isoformat(), 'timeZone': 'UTC'}}
        calendar.events().insert(calendarId='primary', body=event).execute()
        summary.append('נוסף ליומן: ' + subj + ' (' + dt_start.strftime('%Y-%m-%d %H:%M') + ')')

print('\nסיכום פעולות הסוכן:')
if summary:
    for line in summary:
        print(line)
else:
    print('לא נמצאו הזמנות לפגישה')
