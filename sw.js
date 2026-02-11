const CACHE_NAME = "music-game-v1";
const ASSETS = [
  "./",
  "./index.html",
  "./scan.js",
  "./songs.json",
  "./manifest.json",
  "https://unpkg.com/html5-qrcode" 
];

// Install Event
self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
});

// Fetch Event (Offline Capability)
self.addEventListener("fetch", (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => {
      return response || fetch(e.request);
    })
  );
});