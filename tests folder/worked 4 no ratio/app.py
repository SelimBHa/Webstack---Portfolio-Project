import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# Your API Key from Google Cloud
API_KEY = 'YOUR_API_KEY'
SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
VIDEOS_URL = 'https://www.googleapis.com/youtube/v3/videos'
CHANNELS_URL = 'https://www.googleapis.com/youtube/v3/channels'

# Function to fetch video details (including statistics)
def fetch_video_statistics(video_id):
    params = {
        'part': 'snippet,contentDetails,statistics',
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
        'maxResults': 10,  # Limit to 10 results
        'pageToken': page_token
    }
    response = requests.get(SEARCH_URL, params=params)
    return response.json()

@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = None
    videos = []
    next_page_token = None
    
    if request.method == 'POST':  # Only process form if it's a POST request
        search_query = request.form.get('search')  # Get search query from form
        if search_query:
            data = fetch_videos(search_query)
            video_items = data.get('items', [])
            for video in video_items:
                video_id = video['id']['videoId']
                channel_id = video['snippet']['channelId']
                
                # Fetch video statistics
                video_stats = fetch_video_statistics(video_id)
                video['statistics'] = video_stats['items'][0]['statistics'] if video_stats['items'] else {}
                video['contentDetails'] = video_stats['items'][0]['contentDetails'] if video_stats['items'] else {}
                
                # Fetch channel statistics (for subscriber count)
                channel_stats = fetch_channel_statistics(channel_id)
                video['channelStatistics'] = channel_stats['items'][0]['statistics'] if channel_stats['items'] else {}
                
                # Calculate Views/Subscribers ratio
                views = int(video['statistics'].get('viewCount', 0))
                subscribers = int(video['channelStatistics'].get('subscriberCount', 0))
                video['ratio'] = views / subscribers if subscribers > 0 else 0

                # Add the duration in a readable format
                duration = video['contentDetails'].get('duration', '')
                video['duration'] = duration

                # Format the published date
                published_at = video['snippet'].get('publishedAt', '')
                video['published_at'] = published_at

                # Extract video thumbnail
                video['thumbnail'] = video['snippet'].get('thumbnails', {}).get('high', {}).get('url', '')

            videos = video_items
            next_page_token = data.get('nextPageToken', None)

    return render_template('index.html', videos=videos, search_query=search_query, next_page_token=next_page_token)

if __name__ == '__main__':
    app.run(debug=True)
