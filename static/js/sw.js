/**
 * Service Worker — Huduma Platform
 *
 * Stratégies de cache:
 * - Static assets (CSS, JS, images): Cache First
 * - Pages HTML: Network First (fallback cache offline)
 * - API HTMX partials: Network First (fallback cache)
 * - Google Fonts / CDN: Stale While Revalidate
 */

const CACHE_VERSION = "huduma-v1";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const PAGE_CACHE = `${CACHE_VERSION}-pages`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;

const STATIC_ASSETS = [
  "/static/js/htmx.min.js",
  "https://cdn.tailwindcss.com",
  "https://unpkg.com/lucide@latest",
  "https://unpkg.com/alpinejs@3.13.5/dist/cdn.min.js",
  "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap",
];

// Assets à pré-cacher immédiatement
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {
        // Si un asset CDN échoue, on continue quand même
      });
    })
  );
  self.skipWaiting();
});

// Nettoyage des anciens caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name.startsWith("huduma-") && !name.startsWith(CACHE_VERSION))
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Stratégies de fetch
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorer les requêtes non-GET
  if (request.method !== "GET") return;

  // Ignorer les requêtes Django admin
  if (url.pathname.startsWith("/admin/")) return;

  // Stratégie: Cache First pour assets statiques
  if (
    url.origin === location.origin &&
    (url.pathname.startsWith("/static/") ||
      url.pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|ico|woff2?)$/))
  ) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }

  // Stratégie: Stale While Revalidate pour CDN (fonts, tailwind, lucide, alpine)
  if (
    url.origin === "https://cdn.tailwindcss.com" ||
    url.origin === "https://unpkg.com" ||
    url.origin === "https://fonts.googleapis.com" ||
    url.origin === "https://fonts.gstatic.com"
  ) {
    event.respondWith(staleWhileRevalidate(request, RUNTIME_CACHE));
    return;
  }

  // Stratégie: Network First pour pages HTML et HTMX
  if (request.mode === "navigate" || request.headers.get("HX-Request") === "true") {
    event.respondWith(networkFirst(request, PAGE_CACHE));
    return;
  }

  // Default: Network First avec cache runtime
  event.respondWith(networkFirst(request, RUNTIME_CACHE));
});

// === Stratégies de cache ===

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response("Hors ligne — ressource non disponible.", {
      status: 503,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }
}

async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    // Page offline personnalisée
    if (request.mode === "navigate") {
      const offlinePage = await caches.match("/offline/");
      if (offlinePage) return offlinePage;
    }
    return new Response("Hors ligne — page non disponible.", {
      status: 503,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const fetchPromise = fetch(request)
    .then((response) => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => cached);
  return cached || fetchPromise;
}

// Synchronisation en arrière-plan (pour soumission de présences offline)
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-attendance") {
    event.waitUntil(syncAttendance());
  }
});

async function syncAttendance() {
  // Récupère les présences en attente depuis IndexedDB
  // et les envoie au serveur
  const allClients = await clients.matchAll();
  allClients.forEach((client) => {
    client.postMessage({ type: "SYNC_ATTENDANCE" });
  });
}
