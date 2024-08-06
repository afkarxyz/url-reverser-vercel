from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
from urllib.parse import parse_qs, urlparse

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        url = request.form['url']
        result = reverse_url(url)
    return render_template('index.html', result=result)

def reverse_url(url):
    parsed_url = urlparse(url)
    
    if 'github.io' in url:
        parts = url.split('/')
        username = parts[2].split('.')[0]
        repo_name = '/'.join(parts[3:])
        return [f"https://github.com/{username}/{repo_name}"]
    
    elif 'drive.google.com' in url or 'drive.usercontent.google.com' in url:
        query_params = parse_qs(parsed_url.query)
        if 'id' in query_params:
            file_id = query_params['id'][0]
            return [f"https://drive.google.com/file/d/{file_id}/view"]
        elif parsed_url.path.startswith('/file/d/'):
            file_id = parsed_url.path.split('/')[3]
            return [f"https://drive.google.com/file/d/{file_id}/view"]
    
    elif 'youtube.com' in url or 'youtu.be' in url:
        try:
            if 'youtu.be' in url:
                video_id = url.split('/')[-1]
            elif 'watch' in url:
                query_params = parse_qs(parsed_url.query)
                video_id = query_params.get('v', [None])[0]
            else:
                # Handle channel URLs
                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                channel_id = None
                meta_channel = soup.find('meta', {'itemprop': 'channelId'})
                if meta_channel:
                    channel_id = meta_channel['content']
                if not channel_id:
                    channel_link = soup.find('link', {'rel': 'canonical', 'href': lambda x: x and '/channel/' in x})
                    if channel_link:
                        channel_id = channel_link['href'].split('/channel/')[-1]
                if not channel_id:
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if script.string and '"channelId":"' in script.string:
                            channel_id = script.string.split('"channelId":"')[1].split('"')[0]
                            break
                return [f"https://www.youtube.com/channel/{channel_id}"] if channel_id else ["Channel ID not found"]
            
            if not video_id:
                return ["Invalid YouTube URL"]
            
            api_url = f"https://www.youtube.com/watch?v={video_id}"
            response = requests.get(api_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find channel ID
            channel_id = None
            meta_channel = soup.find('meta', {'itemprop': 'channelId'})
            if meta_channel:
                channel_id = meta_channel['content']
            
            if not channel_id:
                channel_link = soup.find('link', {'rel': 'canonical', 'href': lambda x: x and '/channel/' in x})
                if channel_link:
                    channel_id = channel_link['href'].split('/channel/')[-1]
            
            if not channel_id:
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and '"channelId":"' in script.string:
                        channel_id = script.string.split('"channelId":"')[1].split('"')[0]
                        break
            
            channel_url = f"https://www.youtube.com/channel/{channel_id}" if channel_id else "Channel ID not found"
            
            # Generate thumbnail URLs
            maxres_thumbnail = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            sd_thumbnail = f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg"
            
            return [channel_url, maxres_thumbnail, sd_thumbnail]
        
        except requests.RequestException:
            return ["Error accessing YouTube URL"]
    
    return ["Invalid URL. Please enter a valid GitHub Pages, YouTube & Google Drive URL"]

if __name__ == '__main__':
    app.run()
