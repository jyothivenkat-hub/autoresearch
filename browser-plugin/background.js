// Background service worker - keeps extension alive during API calls
chrome.runtime.onInstalled.addListener(() => {
  console.log("X Reply Generator installed");
});
