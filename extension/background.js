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

  // Check if it's an image
  const isImage = /\.(png|jpg|jpeg|gif|webp|bmp|svg|ico|tiff)$/i.test(downloadItem.filename || "");
  const isImageMime = (downloadItem.mime && downloadItem.mime.startsWith("image/"));

  if (isImage || isImageMime) {
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

function sendToNativeHost(url) {
  const hostName = "com.hussnain.fdm";
  chrome.runtime.sendNativeMessage(hostName, { text: "download_url", url: url }, (response) => {
    if (chrome.runtime.lastError) {
      console.error("Error communicating with native host:", chrome.runtime.lastError.message);
    } else {
      console.log("Received response from native host:", response);
    }
  });
}
