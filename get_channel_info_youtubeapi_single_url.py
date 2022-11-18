# pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
import logging
from time import sleep

import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import urllib.parse as p
import re
import os
import pickle

#https://developers.google.com/identity/protocols/oauth2/service-account
class youtube_wrapper(object):
    def __init__(self,):
        self.SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        # authenticate to YouTube API
        self.youtube = self.youtube_authenticate()
    def service_account(self):
        from google.oauth2 import service_account

        SCOPES = ['https://www.googleapis.com/auth/sqlservice.admin',"https://www.googleapis.com/auth/youtube.force-ssl"]
        SERVICE_ACCOUNT_FILE = './youtube_server_to_server.json'

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return credentials
    def youtube_authenticate(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "credentials.json"
        creds = None
        cred=self.service_account()
        return build(api_service_name, api_version, credentials=cred)
        # the file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
        # if there are no (valid) credentials availablle, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                   asda= creds.refresh(Request())
                except Exception as ex:
                    logging.error(f'an error in fetching youtube api: {ex}')
                    os.unlink('token.pickle')
                    sleep(0.5)
                    self.youtube_authenticate()
            else:
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, self.SCOPES)
                creds = flow.run_local_server(open_browser=False)
            # save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

        return build(api_service_name, api_version, credentials=creds)
    def get_video_id_by_url(self,url):
        """
        Return the Video ID from the video `url`
        """
        # split URL parts
        parsed_url = p.urlparse(url)
        # get the video ID by parsing the query of the URL
        video_id = p.parse_qs(parsed_url.query).get("v")
        if video_id:
            return {"video_id": video_id[0], "status": "success"}
        else:
            print((f"Wasn't able to parse video URL: {url}"))
            logging.warning("errorMessage Wasn't able to parse video URL")
            return {"errorMessage": "Wasn't able to parse video URL", "status": "failed"}

            # pass
            # raise Exception(f"Wasn't able to parse video URL: {url}")
    def get_video_details(self, **kwargs):
        return self.youtube.videos().list(
            part="snippet,contentDetails,statistics",
            **kwargs
        ).execute()
    def get_video_infos(self,video_response):
        try:
            items = video_response.get("items")[0]
            # get the snippet, statistics & content details from the video response
            snippet = items["snippet"]
            statistics = items["statistics"]
            content_details = items["contentDetails"]
            # get infos from the snippet
            channel_title = snippet["channelTitle"]
            title = snippet["title"]
            description = snippet["description"]
            publish_time = snippet["publishedAt"]
            # get stats infos
            comment_count = statistics["commentCount"]
            like_count = statistics["likeCount"]
            # dislike_count = statistics["dislikeCount"]
            view_count = statistics["viewCount"]
            # get duration from content details
            duration = content_details["duration"]
            # duration in the form of something like 'PT5H50M15S'
            # parsing it to be something like '5:50:15'
            parsed_duration = re.search(f"PT(\d+H)?(\d+M)?(\d+S)", duration)
            duration_str = ''
            if parsed_duration:
                parsed_duration = parsed_duration.groups()
                for d in parsed_duration:
                    if d:
                        duration_str += f"{d[:-1]}:"
                duration_str = duration_str.strip(":")
            youtube_info = {}
            youtube_info['Youtube_Title'] = title
            youtube_info['Youtube_Publish time'] = publish_time
            youtube_info['Youtube_Duration'] = duration_str
            youtube_info['Youtube_Number_Of_Comments'] = comment_count
            youtube_info['Youtube_Number_Of_Likes'] = like_count
            youtube_info['Youtube_Number_Of_Views'] = view_count
            youtube_info['Youtube_Description'] = description

            return youtube_info
        except Exception as ex:
            print("> Cannot get video infos: "+str(ex))
            logging.error("> Cannot get video infos: "+str(ex))
            ll = 0
    def get_url_dict(self,url):
        all_youtube_info = []
        counter = 0

        counter += 1
        if counter == 102:
            asdf = 0
        youtube_info_dict = {}
        try:
            if "https://youtu.be/" in url:
                url = url.replace("https://youtu.be/", "https://youtu.be/watch?v=")
            if url == ' ' or url == '':
                youtube_info_dict['Youtube_Title'] = ' '
                youtube_info_dict['Youtube_Description'] = ' '
                youtube_info_dict['Youtube_Publish time'] = ' '
                youtube_info_dict['Youtube_Duration'] = ' '
                youtube_info_dict['Youtube_Number_Of_Comments'] = ' '
                youtube_info_dict['Youtube_Number_Of_Likes'] = ' '
                youtube_info_dict['Youtube_Number_Of_Views'] = ' '
                youtube_info_dict["Youtube_status"] = "failed"
                youtube_info_dict["Youtube_errorMessage"] = "no link is given"
            elif "ok.ru" in url:
                youtube_info_dict['Youtube_Title'] = ' '
                youtube_info_dict['Youtube_Description'] = ' '
                youtube_info_dict['Youtube_Publish time'] = ' '
                youtube_info_dict['Youtube_Duration'] = ' '
                youtube_info_dict['Youtube_Number_Of_Comments'] = ' '
                youtube_info_dict['Youtube_Number_Of_Likes'] = ' '
                youtube_info_dict['Youtube_Number_Of_Views'] = ' '
                youtube_info_dict["Youtube_status"] = "failed"
                youtube_info_dict["Youtube_errorMessage"] = "this link is russian"
            else:

                video_url = url
                # parse video ID from URL
                video_obj = self.get_video_id_by_url(video_url)
                if video_obj['status'] == "success":
                    # make API call to get video info
                    response = self.get_video_details( id=video_obj["video_id"])
                    # print extracted video infos
                    youtube_info_dict = self.get_video_infos(response)
                    youtube_info_dict["Youtube_status"] = video_obj['status']
                    youtube_info_dict["Youtube_errorMessage"] = "none"
                elif video_obj['status'] == "failed":
                    youtube_info_dict['Youtube_Title'] = ' '
                    youtube_info_dict['Youtube_Description'] = ' '
                    youtube_info_dict['Youtube_Publish time'] = ' '
                    youtube_info_dict['Youtube_Duration'] = ' '
                    youtube_info_dict['Youtube_Number_Of_Comments'] = ' '
                    youtube_info_dict['Youtube_Number_Of_Likes'] = ' '
                    youtube_info_dict['Youtube_Number_Of_Views'] = ' '
                    youtube_info_dict["Youtube_status"] = video_obj['status']
                    youtube_info_dict["Youtube_errorMessage"] = video_obj['errorMessage']
            msg_status="failed"
            if youtube_info_dict["Youtube_status"]=="success":
                msg_status="success"
            return msg_status,youtube_info_dict
        except Exception as ex:
            logging.error("> get url dict error: " + str(ex))
            youtube_info_dict['Youtube_Title'] = ' '
            youtube_info_dict['Youtube_Description'] = ' '
            youtube_info_dict['Youtube_Publish time'] = ' '
            youtube_info_dict['Youtube_Duration'] = ' '
            youtube_info_dict['Youtube_Number_Of_Comments'] = ' '
            youtube_info_dict['Youtube_Number_Of_Likes'] = ' '
            youtube_info_dict['Youtube_Number_Of_Views'] = ' '
            youtube_info_dict["Youtube_status"] = "failed"
            youtube_info_dict["Youtube_errorMessage"] = str(ex)
            print(str(ex))
            return "failed",youtube_info_dict
