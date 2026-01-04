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

chrome.downloads.onCreated.addListener((downloadItem) => {
  // Simple logic: if it has a URL, cancel browser download and send to FDM
  if (downloadItem.url && downloadItem.state !== "interrupted") {

    // Check if it's an image
    const isImage = /\.(png|jpg|jpeg|gif|webp|bmp|svg|ico|tiff)$/i.test(downloadItem.filename || downloadItem.url);
    const isImageMime = (downloadItem.mime && downloadItem.mime.startsWith("image/"));

    if (isImage || isImageMime) {
      console.log("Ignoring image download:", downloadItem.url);
      return; // Let browser handle it
    }

    chrome.downloads.cancel(downloadItem.id, () => {
      console.log("Cancelled browser download, sending to FDM:", downloadItem.url);
      sendToNativeHost(downloadItem.url);
    });
  }
});

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
