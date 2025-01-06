import requests
from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)

# API Key from Google Cloud
API_KEY = 'AIzaSyBZ3MAavX-cB4DC9J63Cd7LYIZvaxfJPZE'  # Replace with your API key
SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
VIDEOS_URL = 'https://www.googleapis.com/youtube/v3/videos'
CHANNELS_URL = 'https://www.googleapis.com/youtube/v3/channels'

# Function to fetch video details (including statistics)
def fetch_video_statistics(video_id):
    params = {
        'part': 'statistics,contentDetails',
        'id': video_id,
        'key': API_KEY
    }
    response = requests.get(VIDEOS_URL, params=params)
    return response.json()

# Function to fetch channel details (to get subscriber count)
def fetch_channel_statistics(channel_id):
    params = {
        'part': 'statistics',
        'id': channel_id,
        'key': API_KEY
    }
    response = requests.get(CHANNELS_URL, params=params)
    return response.json()

# Function to fetch videos based on search query
def fetch_videos(query, page_token=None):
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'key': API_KEY,
        'maxResults': 12,  # Load 12 videos per request (you can adjust this)
        'pageToken': page_token
    }
    response = requests.get(SEARCH_URL, params=params)
    return response.json()

# Utility function to round the ratio to specified decimal points
def round_ratio(ratio, decimals=2):
    """Rounds a ratio to the specified number of decimals."""
    if isinstance(ratio, (int, float)):
        return round(ratio, decimals)
    return ratio  # Return 'N/A' or other non-numeric values unchanged

# Function to convert ISO 8601 duration (e.g., PT17M8S) to HH:MM:SS format
def format_duration(duration):
    # Match durations like PT17M8S or PT1H2M3S
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    
    if not match:
        return '00:00:00'  # Return a default value if the match is not found
    
    hours = match.group(1) if match.group(1) else '00'
    minutes = match.group(2) if match.group(2) else '00'
    seconds = match.group(3) if match.group(3) else '00'
    
    # Ensure two digits for hours, minutes, and seconds
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = request.args.get('search', '')  # Default to empty string if no search query
    page_token = request.args.get('page_token')  # Get page token if any
    videos = []
    next_page_token = None
    
    if search_query:
        # Fetch videos based on search query and page token
        data = fetch_videos(search_query, page_token)
        video_items = data.get('items', [])
        
        for video in video_items:
            # Extract video ID and channel ID
            video_id = video['id']['videoId']
            channel_id = video['snippet']['channelId']
            
            # Fetch video statistics
            video_stats = fetch_video_statistics(video_id)
            video['statistics'] = video_stats['items'][0]['statistics'] if video_stats['items'] else {}
            video['contentDetails'] = video_stats['items'][0]['contentDetails'] if video_stats['items'] else {}
            
            # Fetch channel statistics (for subscriber count)
            channel_stats = fetch_channel_statistics(channel_id)
            video['channelStatistics'] = channel_stats['items'][0]['statistics'] if channel_stats['items'] else {}

            # Calculate the ratio of views to subscribers
            views = int(video['statistics'].get('viewCount', 0))
            subscribers = int(video['channelStatistics'].get('subscriberCount', 0))
            raw_ratio = views / subscribers if subscribers != 0 else 'N/A'
            video['views_to_subscribers_ratio'] = round_ratio(raw_ratio)
            
            # Get the publish date and duration, format the duration
            video['publishDate'] = video['snippet'].get('publishedAt', 'N/A')
            video['duration'] = format_duration(video['contentDetails'].get('duration', 'PT0S'))  # Default to 0S if no duration is provided

        videos = video_items
        next_page_token = data.get('nextPageToken', None)

    return render_template('index.html', videos=videos, search_query=search_query, next_page_token=next_page_token)

@app.route('/load_more', methods=['POST'])
def load_more():
    search_query = request.form.get('search')  # Get search query from form
    page_token = request.form.get('page_token')  # Get page token from button
    data = fetch_videos(search_query, page_token)  # Fetch next set of videos
    video_items = data.get('items', [])
    
    for video in video_items:
        # Extract video ID and channel ID
        video_id = video['id']['videoId']
        channel_id = video['snippet']['channelId']
        
        # Fetch video statistics
        video_stats = fetch_video_statistics(video_id)
        video['statistics'] = video_stats['items'][0]['statistics'] if video_stats['items'] else {}
        video['contentDetails'] = video_stats['items'][0]['contentDetails'] if video_stats['items'] else {}
        
        # Fetch channel statistics (for subscriber count)
        channel_stats = fetch_channel_statistics(channel_id)
        video['channelStatistics'] = channel_stats['items'][0]['statistics'] if channel_stats['items'] else {}

        # Calculate the ratio of views to subscribers
        views = int(video['statistics'].get('viewCount', 0))
        subscribers = int(video['channelStatistics'].get('subscriberCount', 0))
        raw_ratio = views / subscribers if subscribers != 0 else 'N/A'
        video['views_to_subscribers_ratio'] = round_ratio(raw_ratio)
        
        # Get the publish date and duration, format the duration
        video['publishDate'] = video['snippet'].get('publishedAt', 'N/A')
        video['duration'] = format_duration(video['contentDetails'].get('duration', 'PT0S'))  # Default to 0S if no duration is provided

    next_page_token = data.get('nextPageToken', None)
    return jsonify({'videos': video_items, 'next_page_token': next_page_token})

if __name__ == '__main__':
    app.run(debug=True)
