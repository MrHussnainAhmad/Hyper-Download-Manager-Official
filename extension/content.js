// YouTube Content Script for Hyper Download Manager

let currentVideoId = null;
let downloadPanel = null;
let triggerButton = null;

// Initialization
function init() {
    createPanel();
    // Use an observer to handle SPA navigation and dynamic loading
    const observer = new MutationObserver((mutations) => {
        if (window.location.href.includes('/watch?v=')) {
            checkAndInject();
        } else {
            hideUI();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    // Initial check
    if (window.location.href.includes('/watch?v=')) {
        setTimeout(checkAndInject, 1000); // Slight delay for safety
    }
}

function getVideoId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('v');
}

function createPanel() {
    if (document.getElementById('hdm-download-panel')) return;

    // Create the main panel hidden
    downloadPanel = document.createElement('div');
    downloadPanel.id = 'hdm-download-panel';
    downloadPanel.innerHTML = `
        <div class="hdm-header">
            <span>⬇️ Download Video</span>
            <span class="hdm-close-btn" id="hdm-close">&times;</span>
        </div>
        <div class="hdm-content" id="hdm-content">
            <div class="hdm-loading">Select video to load options...</div>
        </div>
        <div class="hdm-footer">
            <button class="hdm-btn hdm-download-btn" id="hdm-download-action" disabled>Download Now</button>
        </div>
    `;
    document.body.appendChild(downloadPanel);

    // Event listeners
    document.getElementById('hdm-close').addEventListener('click', () => {
        downloadPanel.classList.remove('visible');
    });

    document.getElementById('hdm-download-action').addEventListener('click', startDownload);
}

function checkAndInject() {
    const v = getVideoId();
    if (!v) return;

    if (currentVideoId !== v) {
        currentVideoId = v;
        resetPanel();
    }

    // Try to find the video player to attach the trigger button
    // We try multiple selectors to be robust
    const player = document.querySelector('#movie_player') || document.querySelector('.html5-video-player');

    if (player && !document.getElementById('hdm-floating-trigger')) {
        createTriggerButton(player);
    }
}

function createTriggerButton(playerContainer) {
    if (document.getElementById('hdm-floating-trigger')) return;

    triggerButton = document.createElement('button');
    triggerButton.id = 'hdm-floating-trigger';
    triggerButton.innerHTML = '<span>⬇️</span> Download Video';

    // Position: Absolute relative to player
    triggerButton.style.display = 'flex';

    triggerButton.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation(); // Critical: Prevent YouTube from catching the click
        showPanel();
    });

    playerContainer.appendChild(triggerButton);
}

function hideUI() {
    if (downloadPanel) downloadPanel.classList.remove('visible');
    const btn = document.getElementById('hdm-floating-trigger');
    if (btn) btn.remove();
}

function resetPanel() {
    const content = document.getElementById('hdm-content');
    if (content) content.innerHTML = '<div class="hdm-loading">Loading qualities...</div>';
    document.getElementById('hdm-download-action').disabled = true;
    downloadPanel.dataset.loadedId = '';
}

function showPanel() {
    if (!downloadPanel) createPanel();
    downloadPanel.classList.add('visible');

    // Only fetch if not already fetched for this video
    if (downloadPanel.dataset.loadedId !== currentVideoId) {
        fetchQualities();
    }
}

function fetchQualities() {
    const content = document.getElementById('hdm-content');
    content.innerHTML = `
        <div class="hdm-loading">
            <div class="hdm-spinner"></div>
            <span>Fetching qualities...</span>
        </div>
    `;

    // Disable download button while fetching
    document.getElementById('hdm-download-action').disabled = true;
    document.getElementById('hdm-download-action').innerText = 'Loading...';

    chrome.runtime.sendMessage({
        type: "FETCH_VARIANTS",
        url: window.location.href
    }, (response) => {
        if (response && response.success) {
            downloadPanel.dataset.loadedId = currentVideoId;
            // Store title for later use
            if (response.info && response.info.title) {
                downloadPanel.dataset.videoTitle = response.info.title;
            } else {
                downloadPanel.dataset.videoTitle = "video";
            }
            renderQualities(response.data);
            document.getElementById('hdm-download-action').innerText = 'Download Now';
        } else {
            content.innerHTML = `<div class="hdm-loading" style="color:#d9534f">Error: ${response ? response.error : 'Unknown error'}<br>Try refreshing.</div>`;
            document.getElementById('hdm-download-action').innerText = 'Error';
        }
    });
}

function renderQualities(streams) {
    const content = document.getElementById('hdm-content');
    content.innerHTML = '<ul class="hdm-quality-list"></ul>';
    const list = content.querySelector('ul');

    streams.forEach((stream, index) => {
        const li = document.createElement('li');
        li.className = 'hdm-quality-item';
        if (index === 0) li.classList.add('selected');

        li.dataset.index = index;

        li.innerHTML = `
            <div class="hdm-radio"></div>
            <div class="hdm-quality-info">
                <span class="hdm-res">${stream.resolution}</span>
                <span class="hdm-meta">${stream.mime_type.split('/')[1].toUpperCase()} ${stream.fps ? '@ ' + stream.fps + 'fps' : ''}</span>
            </div>
            <span class="hdm-quality-size">${stream.formatted_size}</span>
        `;

        // Single click selects
        li.addEventListener('click', () => {
            // Deselect all
            list.querySelectorAll('.hdm-quality-item').forEach(el => el.classList.remove('selected'));
            li.classList.add('selected');
        });

        // Double click downloads
        li.addEventListener('dblclick', () => {
            li.classList.add('selected');
            startDownload();
        });

        list.appendChild(li);
    });

    // Enable download button
    document.getElementById('hdm-download-action').disabled = false;

    // Store streams for download action
    downloadPanel.dataset.streams = JSON.stringify(streams);
}

function startDownload() {
    console.log("startDownload triggered");
    const dataStreams = downloadPanel.dataset.streams;
    if (!dataStreams) {
        console.error("No streams in dataset");
        alert("Error: No stream data found. Please refresh.");
        return;
    }

    const streams = JSON.parse(dataStreams);
    const selectedLi = document.querySelector('.hdm-quality-item.selected');

    if (selectedLi && streams[selectedLi.dataset.index]) {
        const stream = streams[selectedLi.dataset.index];
        const btn = document.getElementById('hdm-download-action');
        const title = downloadPanel.dataset.videoTitle || "video";

        console.log("Attempting to download stream:", stream);

        btn.innerText = 'Starting...';
        btn.disabled = true;

        // Send YouTube watch URL instead of direct stream URL
        // This allows the app to use pytubefix to bypass network blocks
        chrome.runtime.sendMessage({
            type: "DOWNLOAD_VARIANT",
            url: window.location.href,  // YouTube watch URL
            quality: stream.resolution,  // Selected quality
            itag: stream.itag,          // Stream identifier
            filename: title + ".mp4",
            filesize: stream.filesize
        }, (res) => {
            console.log("Background response:", res);
            if (chrome.runtime.lastError) {
                console.error("Runtime error:", chrome.runtime.lastError);
                alert("Error sending to background script: " + chrome.runtime.lastError.message);
            }

            downloadPanel.classList.remove('visible');
            btn.innerText = 'Download Now';
            btn.disabled = false;
        });
    } else {
        console.warn("No stream selected or invalid index");
        alert("Please select a quality first.");
    }
}

// Run init
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
