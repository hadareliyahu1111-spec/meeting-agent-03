import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file('token.json')
service = build('gmail', 'v1', credentials=creds)

emails = [
    ('היי הדר, אפשר לקבוע פגישת עדכון למחר ב-10:00 בבוקר?', 'פגישת עדכון'),
    ('הדר, בואי ניפגש ביום שלישי הקרוב ב-16:00 לדבר על הפרויקט.', 'פגישה על הפרויקט'),
    ('שלום, רציתי לשאול מה שלומך?', 'שאלה כללית'),
]

for body, subject in emails:
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['to'] = 'bdikahadar@gmail.com'
    msg['from'] = 'bdikahadar@gmail.com'
    msg['subject'] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()
    print(f'נשלח: {subject}')
