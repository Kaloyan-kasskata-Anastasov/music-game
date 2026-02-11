const CACHE_NAME = "music-game-v1";
const ASSETS = [
  "./",
  "./index.html",
  "./scan.js",
  "./songs.json",
  "./manifest.json",
  "https://unpkg.com/html5-qrcode"
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
});

self.addEventListener("fetch", (e) => {
  e.respondWith(caches.match(e.request).then((response) => response || fetch(e.request)));
});