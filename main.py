import requests
import json
import argparse
from dotenv import dotenv_values
import pandas as pd
import plotly.express as px

CONFIG = dotenv_values(".env.local")
API_KEY = CONFIG["YT_API"]
BASE_URL = "https://www.googleapis.com/youtube/v3/"
# CHN_ID = "UCsBjURrPoezykLs9EqgamOA"


def get_channel_id(command_query):
    channel_data = query_data("search", q=command_query, type="channel")
    try:
        return channel_data["items"][0]["id"]["channelId"]
    except (KeyError, IndexError):
        return None


def query_data(endpoint, **kwargs):
    """Query data from the YouTube API."""
    query = {**kwargs, "key": API_KEY}
    try:
        response = requests.get(BASE_URL + endpoint, params=query, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error querying YouTube API: {e}")
        return {}


# Get the playlist ID for a given channel.
def get_playlist_id(channel):
    """Get the playlist ID for a given channel."""
    print("inside get_playlist_id", channel)

    playlist_id = query_data("channels", part="contentDetails", id=channel)
    return (
        playlist_id["items"][0]
        ["contentDetails"]["relatedPlaylists"]
        ["uploads"]
    )


def get_playlist_items(playlist_id):
    """Get video items from a playlist."""
    print("inside get_playlist_items", playlist_id)
    playlist_items = query_data(
        "playlistItems",
        part="snippet",
        playlistId=playlist_id,
        maxResults=50
    )
    return playlist_items["items"]


def get_video_statistics(video_id):
    """Get view count of each video"""
    video = query_data("videos", id=video_id, part="statistics")
    return int(video['items'][0]['statistics']['viewCount'])


def save_json(video_list, search):
    with open(f"{search}_youtube_data.json", 'w', encoding='utf-8') as file:
        json.dump(video_list, file, ensure_ascii=False, indent=4)


def process_videos(channel_id):
    """Process videos from a YouTube channel."""
    playlist_id = get_playlist_id(channel_id)
    video_list = []

    # Process videos from a YouTube channel.
    for item in get_playlist_items(playlist_id):
        video_id = item['snippet']['resourceId']['videoId']
        statistics = get_video_statistics(video_id)
        video_data = {
            "id": video_id,
            "title": item['snippet']['title'],
            "count": statistics,
            "thumbnail": item['snippet']['thumbnails']['high']['url'],
            "date": item['snippet']['publishedAt']  # 2023-05-10T17:53:59Z
        }
        video_list.append(video_data)

    return video_list


def plotly_magic(search):
    json_file = pd.read_json(f"./{search}_youtube_data.json")
    video_df = pd.DataFrame(json_file)
    # Export to CSV for debugging
    # video_df.to_csv('youtube_data.csv', index=False)

    fig = px.bar(video_df, x='title', y='count',
                 hover_data=['id'],
                 labels={'count': 'View Count', 'title': 'Video Title'})

    fig.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get YouTube channel ID based on a search query or direct input.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--search', help="Search by channel name.")
    group.add_argument('--id', help="Use direct channel ID.")

    args = parser.parse_args()
    command_query = args.search if args.search else args.id

    channel_id = get_channel_id(command_query)
    videos = process_videos(channel_id)
    save_json(videos, command_query)
    plotly_magic(command_query)
