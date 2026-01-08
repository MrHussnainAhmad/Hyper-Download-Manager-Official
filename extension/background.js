chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "download-with-fdm",
    title: "Download with FDM",
    contexts: ["link", "video", "audio"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "download-with-fdm") {
    const url = info.linkUrl || info.srcUrl;
    if (url) {
      sendToNativeHost(url);
    }
  }
});

// Main interception logic
chrome.downloads.onDeterminingFilename.addListener((downloadItem, suggest) => {
  if (shouldHandleDownload(downloadItem)) {
    // Cancel browser download immediately to prevent "Save As" popup
    chrome.downloads.cancel(downloadItem.id, () => {
      if (chrome.runtime.lastError) {
        console.error("Cancel error:", chrome.runtime.lastError.message);
      } else {
        console.log("Cancelled browser download (onDeterminingFilename), sending to FDM:", downloadItem.url);
        sendToNativeHost(downloadItem.url);
      }
    });
    // We don't call suggest() because we cancelled the download. 
    // Calling it on a dead download id might cause an error or be ignored.
  } else {
    // Pass through to browser default behavior
    suggest();
  }
});

function shouldHandleDownload(downloadItem) {
  if (!downloadItem.url || downloadItem.state === "interrupted") {
    return false;
  }

  // Protocol check
  if (!downloadItem.url.startsWith("http")) {
    return false;
  }

  // Ignore YouTube video pages (we handle them via the extension panel)
  if (downloadItem.url.includes("youtube.com/watch") || downloadItem.url.includes("youtu.be/")) {
    console.log("Ignoring YouTube page download (handled by panel):", downloadItem.url);
    return false;
  }

  // Check if it's an image
  const imageExts = /\.(png|jpg|jpeg|gif|webp|bmp|svg|ico|tiff|avif|heic|heif)$/i;
  const isImageFile = imageExts.test(downloadItem.filename || "");
  const isImageMime = (downloadItem.mime && downloadItem.mime.startsWith("image/"));

  // Check URL as fallback (in case filename is empty or misleading)
  const cleanUrl = downloadItem.url.split('?')[0];
  const isImageUrl = imageExts.test(cleanUrl);

  if (isImageFile || isImageMime || isImageUrl) {
    console.log("Ignoring image download:", downloadItem.url);
    return false;
  }

  // Check for "garbage" files (web pages, scripts, data)
  const ignoredExtensions = [
    'html', 'htm', 'xml', 'json', 'js', 'css', 'map', 'txt', 'md'
  ];

  const ignoredMimes = [
    'text/html', 'text/xml', 'application/json', 'text/css',
    'text/javascript', 'application/javascript'
  ];

  const ext = (downloadItem.filename || "").split('.').pop().toLowerCase();
  if (ignoredExtensions.includes(ext)) {
    console.log("Ignoring extension:", ext, downloadItem.url);
    return false;
  }

  if (downloadItem.mime && ignoredMimes.includes(downloadItem.mime)) {
    console.log("Ignoring mime:", downloadItem.mime, downloadItem.url);
    return false;
  }

  return true;
}

// Connection to Native Host
const HOST_NAME = "com.hussnain.fdm";

// Handle messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "FETCH_VARIANTS") {
    sendNativeMessage({ text: "fetch_variants", url: message.url }, sendResponse);
    return true; // Keep channel open for async response
  }
  if (message.type === "DOWNLOAD_VARIANT") {
    // Pass ALL fields including quality, itag, and filesize
    sendNativeMessage({
      text: "download_variant",
      url: message.url,
      filename: message.filename,
      quality: message.quality,      // CRITICAL: Pass quality
      itag: message.itag,            // CRITICAL: Pass itag
      filesize: message.filesize     // CRITICAL: Pass filesize
    }, sendResponse);
    return true;
  }
});

function sendNativeMessage(message, callback) {
  chrome.runtime.sendNativeMessage(HOST_NAME, message, (response) => {
    if (chrome.runtime.lastError) {
      console.error("Error communicating with native host:", chrome.runtime.lastError.message);
      if (callback) callback({ success: false, error: chrome.runtime.lastError.message });
    } else {
      console.log("Received response from native host:", response);
      if (callback) callback(response);
    }
  });
}

function sendToNativeHost(url) {
  sendNativeMessage({ text: "download_url", url: url }, (response) => {
    // Log handled in sendNativeMessage
  });
}
