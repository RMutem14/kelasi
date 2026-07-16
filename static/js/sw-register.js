/**
 * Enregistrement du Service Worker et gestion offline.
 */
(function () {
  "use strict";

  if (!("serviceWorker" in navigator)) return;

  // Enregistrer le SW seulement en HTTPS ou localhost
  if (location.protocol !== "https:" && location.hostname !== "localhost" && location.hostname !== "127.0.0.1") {
    return;
  }

  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/static/js/sw.js")
      .then((reg) => {
      })
      .catch((err) => {
        console.warn("[Huduma] SW registration failed:", err);
      });

    // Écouter les changements de connectivité
    window.addEventListener("online", () => {
      document.body.classList.remove("huduma-offline");
      document.body.classList.add("huduma-online");
      // Déclencher la synchronisation
      if ("serviceWorker" in navigator && "SyncManager" in window) {
        navigator.serviceWorker.ready.then((reg) => {
          return reg.sync.register("sync-attendance");
        });
      }
    });

    window.addEventListener("offline", () => {
      document.body.classList.remove("huduma-online");
      document.body.classList.add("huduma-offline");
    });

    // État initial
    if (navigator.onLine) {
      document.body.classList.add("huduma-online");
    } else {
      document.body.classList.add("huduma-offline");
    }

    // Écouter les messages du SW
    navigator.serviceWorker.addEventListener("message", (event) => {
      if (event.data && event.data.type === "SYNC_ATTENDANCE") {
        window.dispatchEvent(new CustomEvent("huduma:sync-attendance"));
      }
    });
  });
})();
