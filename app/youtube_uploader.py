"""YouTube Uploader for Math Mishaps / Math Mayhem.

Handles OAuth2 authentication and video uploading to YouTube Shorts via YouTube Data API v3.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

CLIENT_SECRETS_FILE = Path("client_secret.json")
TOKEN_FILE = Path("token.json")
VERIFIER_FILE = Path("data/oauth_verifier.txt")
REDIRECT_URI = "http://localhost:8888/"


def get_authorization_url() -> str:
    """Generate the OAuth2 authorization URL for the user and persist PKCE verifier."""
    VERIFIER_FILE.parent.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRETS_FILE),
        scopes=SCOPES,
    )
    flow.redirect_uri = REDIRECT_URI
    auth_url, _ = flow.authorization_url(prompt="select_account consent", access_type="offline")
    VERIFIER_FILE.write_text(flow.code_verifier, encoding="utf-8")
    return auth_url


def exchange_code_for_token(code_or_url: str) -> Credentials:
    """Exchange authorization code or redirect URL for credentials and save to token.json."""
    code = code_or_url.strip()
    if "code=" in code:
        # Extract code from redirect URL
        import urllib.parse
        parsed = urllib.parse.urlparse(code)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            code = params["code"][0]

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRETS_FILE),
        scopes=SCOPES,
    )
    flow.redirect_uri = REDIRECT_URI
    if VERIFIER_FILE.exists():
        flow.code_verifier = VERIFIER_FILE.read_text(encoding="utf-8").strip()

    flow.fetch_token(code=code)
    creds = flow.credentials

    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    print(f"Credentials saved successfully to {TOKEN_FILE}")
    return creds


def get_credentials(interactive: bool = True) -> Optional[Credentials]:
    """Retrieve valid credentials, refreshing or initiating flow as needed."""
    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            print(f"Warning: could not parse {TOKEN_FILE}: {e}")

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            return creds
        except Exception as e:
            print(f"Failed to refresh token: {e}")

    if not interactive:
        return None

    # Run local server if on desktop
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRETS_FILE),
        scopes=SCOPES,
        autogenerate_code_verifier=False,
    )
    creds = flow.run_local_server(port=8080, prompt="consent")
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def upload_youtube_short(
    video_path: Path,
    title: str,
    description: str,
    tags: List[str],
    category_id: str = "27",  # Education
    privacy_status: str = "public",
    creds: Optional[Credentials] = None,
) -> Dict[str, Any]:
    """Upload a vertical video to YouTube Shorts with optimized metadata."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if creds is None:
        creds = get_credentials(interactive=False)
        if creds is None:
            raise RuntimeError(
                "No valid YouTube credentials found. Please authenticate first via get_authorization_url()."
            )

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 2,  # 2MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    print(f"Uploading {video_path.name} to YouTube...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    video_id = response.get("id")
    video_url = f"https://youtu.be/{video_id}"
    shorts_url = f"https://youtube.com/shorts/{video_id}"
    print(f"Upload complete! Video ID: {video_id}")
    print(f"Watch URL: {video_url}")
    print(f"Shorts URL: {shorts_url}")

    return {
        "id": video_id,
        "watch_url": video_url,
        "shorts_url": shorts_url,
        "title": title,
        "response": response,
    }


def add_pinned_comment(youtube: Resource, video_id: str, comment_text: str) -> Optional[str]:
    """Add a top-level pinned educational comment to the uploaded video."""
    try:
        response = youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": comment_text,
                        }
                    },
                }
            },
        ).execute()
        return response.get("id")
    except Exception as e:
        print(f"Notice: Could not post pinned comment automatically: {e}")
        return None
