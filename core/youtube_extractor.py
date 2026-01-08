import logging
import json
from datetime import datetime
from pytubefix import YouTube
from pytubefix.cli import on_progress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeExtractor:
    def __init__(self):
        pass

    def get_video_info(self, url):
        """
        Extracts metadata from a YouTube video.
        """
        try:
            yt = YouTube(url, on_progress_callback=on_progress)
            
            # Force pre-fetching to ensure metadata is available
            yt.check_availability()
            
            metadata = {
                'title': yt.title,
                'thumbnail_url': yt.thumbnail_url,
                'duration': yt.length,
                'channel': yt.author,
                'views': yt.views,
                'video_id': yt.video_id,
                'description': yt.description
            }
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            raise e

    def get_streams(self, url):
        """
        Returns a structured list of available streams with file sizes.
        """
        try:
            yt = YouTube(url)
            yt.check_availability()
            
            streams = []
            
            # Filter for meaningful video streams (adaptive and progressive)
            # We prioritize mp4
            video_streams = yt.streams.filter(type='video').order_by('resolution').desc()
            audio_streams = yt.streams.filter(type='audio').order_by('abr').desc()
            
            seen_res = set()
            
            for s in video_streams:
                # We want unique resolutions, prioritizing higher quality/bitrate
                if s.resolution not in seen_res and s.resolution is not None:
                    seen_res.add(s.resolution)
                    
                    # Calculate size (filesize_approx or filesize)
                    size = s.filesize if s.filesize else s.filesize_approx
                    
                    stream_data = {
                        'itag': s.itag,
                        'resolution': s.resolution,
                        'mime_type': s.mime_type,
                        'filesize': size,
                        'formatted_size': self._format_size(size),
                        'fps': s.fps,
                        'type': 'video',
                        'is_progressive': s.is_progressive,
                        'has_audio': s.includes_audio_track,
                        'url': s.url
                    }
                    streams.append(stream_data)

            # Add best audio option
            if video_streams:
                best_audio = audio_streams.first()
                if best_audio:
                    size = best_audio.filesize if best_audio.filesize else best_audio.filesize_approx
                    streams.append({
                        'itag': best_audio.itag,
                        'resolution': 'Audio Only',
                        'mime_type': best_audio.mime_type,
                        'filesize': size,
                        'formatted_size': self._format_size(size),
                        'fps': None,
                        'type': 'audio',
                        'is_progressive': False,
                        'has_audio': True,
                        'url': best_audio.url
                    })
                    
            return streams

        except Exception as e:
            logger.error(f"Error fetching streams: {str(e)}")
            raise e

    def _format_size(self, bytes_size):
        if not bytes_size:
            return "Unknown"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"

# Helper for direct usage
def fetch_youtube_data(url):
    extractor = YouTubeExtractor()
    info = extractor.get_video_info(url)
    streams = extractor.get_streams(url)
    return {
        'info': info,
        'streams': streams
    }

if __name__ == "__main__":
    # Simple test
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Never gonna give you up
    try:
        print(f"Testing with: {test_url}")
        data = fetch_youtube_data(test_url)
        print("Metadata:", json.dumps(data['info'], indent=2))
        print("Streams found:", len(data['streams']))
        for s in data['streams']:
            print(f"- {s['resolution']} ({s['formatted_size']}) - Prog: {s['is_progressive']}")
    except Exception as e:
        print(f"Error: {e}")
