# Meeting Agent - Assignment 03

## Group Code
**biu-he01**

## Project Overview
An autonomous AI agent that bridges Gmail and Google Calendar.
The agent scans incoming emails, detects meeting invitations written in natural language,
checks calendar availability, and acts accordingly - all without human intervention.

## Features
- Scans Gmail inbox for the last 48 hours
- Detects meeting invitations using keyword and time pattern matching
- Filters non-meeting emails automatically
- Checks Google Calendar for conflicts
- Creates a new calendar event if the time slot is free
- Sends a decline email if the time slot is busy
- Prints a full action summary at the end

## Tech Stack
- Python 3.14
- Gmail API (google-api-python-client)
- Google Calendar API
- Google OAuth 2.0

## Project Structure
- oauth_setup.py - OAuth2 authentication and token generation
- send_test_emails.py - Sends 3 test emails (2 invitations + 1 non-invitation)
- meeting_agent_simple.py - Core autonomous agent logic
- PRD.md - Product Requirements Document
- PLAN.md - Development plan
- TODO.md - Task checklist
- .gitignore - Excludes credentials and tokens from version control

## Setup Instructions
1. Place your credentials.json from Google Cloud Console in the project folder
2. Install dependencies:
   python -m pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
3. Authenticate:
   python oauth_setup.py
4. Send test emails:
   python send_test_emails.py
5. Run the agent:
   python meeting_agent_simple.py

## Test Results
- 3 emails sent to bdikahadar@gmail.com
- 2 meeting invitations detected and processed
- 1 non-meeting email correctly filtered out
- 2 events successfully created in Google Calendar

## Submission
- Course: AI Agents - Bar Ilan University
- Assignment: 03
- Due date: June 10, 2026
- GitHub: https://github.com/hadareliyahu1111-spec/meeting-agent-03
