"""
Google API Authentication Utils
-------------------------------
Handles OAuth 2.0 flow for Google Tasks and other services.
"""

import os.path
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/gmail.send'
]

def get_google_service(service_name: str, version: str):
    """ Authenticate and return the requested Google service. """
    creds = None
    
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # If refresh fails, re-authenticate from scratch
                creds = None
        
        if not creds:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError("Your credentials.json file is missing. Please download it from the Google Cloud Console.")
            
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            # Run local server on a fixed port if possible, or 0 for any
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build(service_name, version, credentials=creds)
