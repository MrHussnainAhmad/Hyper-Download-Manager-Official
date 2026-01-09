"""
Built-in Proxy Manager with embedded fallback proxies
"""

import requests
import random
import time
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker, QStandardPaths


# ═══════════════════════════════════════════════════════════════════════════════
#                    DEFAULT BEST PROXY (INSTANT FALLBACK)
# ═══════════════════════════════════════════════════════════════════════════════
# This is the FIRST proxy tried - no validation needed, instant fallback!
# Update this with a current working proxy from proxy-list.download or similar

# Test this regularly and update if dead - free proxies die fast!
# Last verified working with yt-dlp in this environment: 2026-01-09
DEFAULT_BEST_PROXY = "http://103.81.194.165:8080"
# Previous: "http://185.162.228.73:3128"


# ═══════════════════════════════════════════════════════════════════════════════
#                    EMBEDDED FALLBACK PROXIES
# ═══════════════════════════════════════════════════════════════════════════════
# These are checked/updated periodically - last resort if all sources fail

EMBEDDED_PROXIES = [
    # Format: (host:port, type)
    # HTTP Proxies (commonly working ones)
    # Prioritized (YouTube-tested recently; free proxies may die quickly)
    ("103.81.194.165:8080", "http"),
    ("103.81.194.120:8080", "http"),
    ("38.180.2.107:3128", "http"),
    ("103.81.194.124:8080", "http"),
    ("103.81.194.125:8080", "http"),
    ("140.238.184.182:3128", "http"),
    ("157.66.84.32:8181", "http"),
    ("49.229.100.235:8080", "http"),

    ("154.26.135.123:3128", "http"),
    ("45.77.147.46:3128", "http"),
    ("8.219.97.248:80", "http"),
    ("47.88.31.196:8080", "http"),
    ("47.251.70.179:80", "http"),
    ("20.206.106.192:8123", "http"),
    ("43.153.208.166:3128", "http"),
    ("47.243.166.133:18080", "http"),
    ("198.59.191.234:8080", "http"),
    ("103.152.112.162:80", "http"),
    ("185.217.136.67:1337", "http"),
    ("51.159.0.236:2222", "http"),
    ("38.180.27.23:8080", "http"),
    ("103.87.169.194:56642", "http"),
    ("185.82.98.73:9092", "http"),
    ("188.132.222.167:8080", "http"),
    ("31.186.239.244:8080", "http"),
    ("103.46.11.74:8080", "http"),
    ("103.160.207.49:32650", "http"),
    ("31.186.239.246:8080", "http"),
    # SOCKS5 Proxies
    ("51.158.123.35:8811", "socks5"),
    ("192.111.139.165:19404", "socks5"),
    ("72.210.252.134:46164", "socks5"),
    ("192.252.208.67:14287", "socks5"),
    ("72.195.114.169:4145", "socks5"),
    ("174.77.111.197:4145", "socks5"),
    ("72.221.164.34:60671", "socks5"),
    ("72.49.49.11:31034", "socks5"),
    ("184.178.172.14:4145", "socks5"),
    ("70.166.167.55:57745", "socks5"),
]


class ProxyFetcher(QThread):
    """Background thread to fetch and validate proxies"""
    finished = Signal(list)
    progress = Signal(str)
    
    # Proxy API sources - FAST and frequently updated (prioritized at top)
    PROXY_SOURCES = [
        # FAST APIs - Try these first! (Updated every few minutes)
        "https://www.proxy-list.download/api/v1/get?type=http",
        "https://www.proxy-list.download/api/v1/get?type=https",
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=yes",
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all",
        "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&proxy_format=ipport&format=text",
        
        # GitHub hosted lists (reliable but slower updates)
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
        "https://raw.githubusercontent.com/ErcinDedeworken/Prox/main/http.txt",
        "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
        "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt",
        "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
        "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt",
        
        # Spys.me (usually accessible)
        "https://spys.me/proxy.txt",
    ]
    
    def __init__(self, test_url="https://www.youtube.com", max_valid=25):
        super().__init__()
        self.test_url = test_url
        self.max_valid = max_valid
        self._stop = False
    
    def stop(self):
        self._stop = True
    
    def run(self):
        try:
            self.progress.emit("Fetching proxy lists...")
            all_proxies = self._fetch_all_proxies()
            
            # Add embedded proxies as fallback
            for host, ptype in EMBEDDED_PROXIES:
                all_proxies.append({'host': host, 'type': ptype})
            
            if self._stop:
                self.finished.emit([])
                return
            
            if not all_proxies:
                self.progress.emit("No proxy sources reachable, using fallback...")
                # Use only embedded proxies
                all_proxies = [{'host': h, 'type': t} for h, t in EMBEDDED_PROXIES]
            
            self.progress.emit(f"Testing {len(all_proxies)} proxies...")
            valid_proxies = self._validate_proxies(all_proxies)
            
            self.progress.emit(f"Found {len(valid_proxies)} working proxies")
            self.finished.emit(valid_proxies)
        except Exception as e:
            print(f"ProxyFetcher error: {e}")
            import traceback
            traceback.print_exc()
            self.finished.emit([])
    
    def _fetch_all_proxies(self):
        """Fetch proxies from all sources"""
        all_proxies = []
        successful_sources = 0
        
        for source in self.PROXY_SOURCES:
            if self._stop:
                break
            try:
                # Shorter timeout for faster iteration
                response = requests.get(
                    source, 
                    timeout=6, 
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                
                if response.status_code == 200:
                    is_socks = 'socks' in source.lower()
                    text = response.text
                    
                    # Handle spys.me format (different format)
                    if 'spys.me' in source:
                        lines = text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if ':' in line and line[0].isdigit():
                                parts = line.split()
                                if parts:
                                    proxy_part = parts[0]
                                    if ':' in proxy_part:
                                        all_proxies.append({
                                            'host': proxy_part,
                                            'type': 'http'
                                        })
                    else:
                        # Standard format: IP:PORT per line
                        lines = text.strip().split('\n')
                        
                        for line in lines:
                            line = line.strip()
                            if not line or line.startswith('#'):
                                continue
                                
                            if ':' in line and len(line) < 50:
                                parts = line.split(':')
                                if len(parts) >= 2:
                                    try:
                                        ip = parts[0].strip()
                                        port = parts[1].split()[0].strip()
                                        
                                        # Validate IP format
                                        if ip[0].isdigit() and port.isdigit():
                                            port_num = int(port)
                                            if 1 <= port_num <= 65535:
                                                all_proxies.append({
                                                    'host': f"{ip}:{port}",
                                                    'type': 'socks5' if is_socks else 'http'
                                                })
                                    except:
                                        pass
                    
                    successful_sources += 1
                    print(f"✓ Source: {source[:50]}... ({len(all_proxies)} total)")
                    
            except Exception as e:
                error_msg = str(e)[:80]
                print(f"✗ Source failed: {source[:40]}... - {error_msg}")
        
        print(f"DEBUG: Fetched from {successful_sources} sources, {len(all_proxies)} proxies")
        
        # Remove duplicates and shuffle
        seen = set()
        unique = []
        for p in all_proxies:
            if p['host'] not in seen:
                seen.add(p['host'])
                unique.append(p)
        
        random.shuffle(unique)
        return unique
    
    def _validate_proxies(self, proxies):
        """Validate proxies in parallel"""
        valid = []
        tested = 0
        
        def test_proxy(proxy_info):
            if self._stop:
                return None
            
            host = proxy_info['host']
            ptype = proxy_info['type']
            proxy_url = f"{ptype}://{host}"
            
            try:
                proxies_dict = {"http": proxy_url, "https": proxy_url}
                
                start = time.time()
                response = requests.get(
                    self.test_url,
                    proxies=proxies_dict,
                    timeout=12,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    },
                    allow_redirects=True
                )
                elapsed = time.time() - start
                
                # Check if response is valid YouTube page (should be > 10KB)
                if response.status_code == 200 and len(response.content) > 10000:
                    content_lower = response.text[:2000].lower()
                    # Make sure it's actually YouTube
                    if 'youtube' in content_lower:
                        return {
                            'url': proxy_url,
                            'host': host,
                            'type': ptype,
                            'speed': elapsed
                        }
            except:
                pass
            return None
        
        # Test proxies in parallel - limit batch size for efficiency
        test_batch = proxies[:300]
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(test_proxy, p): p for p in test_batch}
            
            for future in as_completed(futures):
                if self._stop:
                    break
                
                tested += 1
                
                if len(valid) >= self.max_valid:
                    # Got enough, cancel remaining
                    for f in futures:
                        f.cancel()
                    break
                
                result = future.result()
                if result:
                    valid.append(result)
                    print(f"✓ Proxy #{len(valid)}: {result['host']} ({result['speed']:.1f}s)")
                
                # Progress update every 50 tests
                if tested % 50 == 0:
                    self.progress.emit(f"Tested {tested}/{len(test_batch)}, found {len(valid)} working...")
        
        # Sort by speed
        valid.sort(key=lambda x: x['speed'])
        return valid


class ProxyManager:
    """Singleton manager for built-in proxy rotation"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._proxies = []
        self._current_index = 0
        self._failed_proxies = set()
        self._last_refresh = 0
        self._refresh_interval = 1800  # 30 minutes
        self._mutex = QMutex()
        self._fetcher = None
        self._fetch_callbacks = []
        
        # Cache file
        try:
            config_dir = os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.AppDataLocation),
                "HyperDownloadManager"
            )
            os.makedirs(config_dir, exist_ok=True)
            self._cache_file = os.path.join(config_dir, "proxy_cache.json")
        except:
            self._cache_file = None
        
        self._load_cache()
    
    def _load_cache(self):
        """Load proxies from cache"""
        if not self._cache_file:
            return
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r') as f:
                    data = json.load(f)
                    self._proxies = data.get('proxies', [])
                    self._last_refresh = data.get('timestamp', 0)
                    
                    # Check if cache is still valid (24 hours for cached proxies)
                    cache_age = time.time() - self._last_refresh
                    if cache_age > 86400:  # 24 hours
                        print("Proxy cache expired (>24h)")
                        self._proxies = []
                    elif cache_age > self._refresh_interval:
                        print(f"Proxy cache stale ({cache_age/60:.0f}m old)")
                    else:
                        print(f"Loaded {len(self._proxies)} cached proxies ({cache_age/60:.0f}m old)")
        except Exception as e:
            print(f"Cache load error: {e}")
    
    def _save_cache(self):
        """Save proxies to cache"""
        if not self._cache_file:
            return
        try:
            with open(self._cache_file, 'w') as f:
                json.dump({
                    'proxies': self._proxies[:30],  # Save top 30
                    'timestamp': time.time()
                }, f, indent=2)
        except:
            pass
    
    def needs_refresh(self):
        """Check if proxies need refresh"""
        if not self._proxies:
            return True
        if time.time() - self._last_refresh > self._refresh_interval:
            return True
        # If more than 70% failed, refresh
        if self._proxies and len(self._failed_proxies) >= len(self._proxies) * 0.7:
            return True
        return False
    
    def refresh_proxies(self, callback=None):
        """Start background proxy refresh"""
        with QMutexLocker(self._mutex):
            if callback:
                self._fetch_callbacks.append(callback)
            
            if self._fetcher and self._fetcher.isRunning():
                print("DEBUG: Proxy fetch already in progress")
                return
            
            print("DEBUG: Starting proxy fetch...")
            self._fetcher = ProxyFetcher()
            self._fetcher.progress.connect(self._on_progress)
            self._fetcher.finished.connect(self._on_proxies_fetched)
            self._fetcher.start()
    
    def _on_progress(self, msg):
        """Handle progress updates"""
        print(f"ProxyManager: {msg}")
    
    def _on_proxies_fetched(self, proxies):
        """Handle fetched proxies"""
        with QMutexLocker(self._mutex):
            if proxies:
                self._proxies = proxies
                self._last_refresh = time.time()
                self._failed_proxies.clear()
                self._current_index = 0
                self._save_cache()
                print(f"ProxyManager: Stored {len(proxies)} working proxies")
            else:
                print("ProxyManager: No proxies found")
                # Try embedded proxies as last resort (without validation)
                self._use_embedded_fallback()
            
            callbacks = self._fetch_callbacks.copy()
            self._fetch_callbacks.clear()
        
        for cb in callbacks:
            try:
                cb(bool(self._proxies))
            except:
                pass
    
    def _use_embedded_fallback(self):
        """Use embedded proxies without validation as last resort"""
        print("ProxyManager: Using embedded fallback proxies")
        self._proxies = []
        for host, ptype in EMBEDDED_PROXIES[:15]:  # Use first 15
            self._proxies.append({
                'url': f"{ptype}://{host}",
                'host': host,
                'type': ptype,
                'speed': 999  # Unknown speed
            })
        if self._proxies:
            self._last_refresh = time.time()
    
    def get_default_proxy(self):
        """Get instant default proxy (no validation needed)"""
        return DEFAULT_BEST_PROXY
    
    def get_proxy(self):
        """Get next available proxy URL"""
        with QMutexLocker(self._mutex):
            if not self._proxies:
                # Try embedded fallback
                self._use_embedded_fallback()
            
            if not self._proxies:
                return None
            
            # Find non-failed proxy
            attempts = 0
            while attempts < len(self._proxies):
                proxy = self._proxies[self._current_index]
                self._current_index = (self._current_index + 1) % len(self._proxies)
                
                if proxy['url'] not in self._failed_proxies:
                    return proxy['url']
                
                attempts += 1
            
            # All failed, clear failures and return first
            print("ProxyManager: All proxies failed, resetting...")
            self._failed_proxies.clear()
            return self._proxies[0]['url'] if self._proxies else None
    
    def mark_proxy_failed(self, proxy_url):
        """Mark proxy as failed"""
        with QMutexLocker(self._mutex):
            self._failed_proxies.add(proxy_url)
            failed_count = len(self._failed_proxies)
            total = len(self._proxies)
            print(f"Proxy failed: {proxy_url[:40]}... ({failed_count}/{total} failed)")
    
    def mark_proxy_success(self, proxy_url):
        """Mark proxy as successful"""
        with QMutexLocker(self._mutex):
            self._failed_proxies.discard(proxy_url)
            # Move to front
            for i, p in enumerate(self._proxies):
                if p['url'] == proxy_url:
                    self._proxies.insert(0, self._proxies.pop(i))
                    self._save_cache()
                    print(f"Proxy success: {proxy_url[:40]}...")
                    break
    
    def get_proxy_count(self):
        """Get total proxy count"""
        with QMutexLocker(self._mutex):
            return len(self._proxies)
    
    def get_working_count(self):
        """Get non-failed proxy count"""
        with QMutexLocker(self._mutex):
            return len(self._proxies) - len(self._failed_proxies)
    
    def is_fetching(self):
        """Check if currently fetching"""
        return self._fetcher and self._fetcher.isRunning()
    
    def clear_cache(self):
        """Clear all cached proxies"""
        with QMutexLocker(self._mutex):
            self._proxies = []
            self._failed_proxies.clear()
            self._last_refresh = 0
            try:
                if self._cache_file and os.path.exists(self._cache_file):
                    os.remove(self._cache_file)
            except:
                pass


# Global instance
proxy_manager = ProxyManager()