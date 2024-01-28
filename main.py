import datetime
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


def next_sunday():
    today = datetime.date.today()
    next_sunday = today + datetime.timedelta((6 - today.weekday()) % 7)
    return next_sunday


def authenticate_youtube():
    credentials = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            credentials = pickle.load(token)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secrets.json",
                scopes=["https://www.googleapis.com/auth/youtube.force-ssl"],
            )
            credentials = flow.run_local_server(port=0)
            with open("token.pickle", "wb") as token:
                pickle.dump(credentials, token)
    youtube = build("youtube", "v3", credentials=credentials)
    return youtube


def create_livestream(youtube):
    next_sunday_date = next_sunday()
    title = f"PCC Worship Service - {next_sunday_date.strftime('%m/%d/%Y')}"
    description = """Worship service of the Presbyterian Church of Coventry - Coventry, CT
All hymns used with permission: CCLI License #2848460
Visit us online at: www.coventrypca.church"""
    insert_broadcast_response = (
        youtube.liveBroadcasts()
        .insert(
            part="snippet,status",
            body=dict(
                snippet=dict(
                    title=title,
                    scheduledStartTime=next_sunday_date.strftime("%Y-%m-%dT10:30:00Z"),
                    description=description,
                ),
                status=dict(privacyStatus="public"),
            ),
        )
        .execute()
    )
    broadcast_id = insert_broadcast_response["id"]
    insert_stream_response = (
        youtube.liveStreams()
        .insert(
            part="snippet,cdn",
            body=dict(
                snippet=dict(title=title),
                cdn=dict(format="1080p", ingestionType="rtmp"),
            ),
        )
        .execute()
    )
    stream_id = insert_stream_response["id"]
    youtube.liveBroadcasts().bind(
        part="id,contentDetails", id=broadcast_id, streamId=stream_id
    ).execute()


if __name__ == "__main__":
    youtube = authenticate_youtube()
    create_livestream(youtube)
