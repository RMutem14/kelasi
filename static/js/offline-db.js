/**
 * Offline storage via IndexedDB — Huduma Platform
 *
 * Stocke les actions en attente (présences, paiements) quand le réseau
 * est indisponible, pour synchronisation ultérieure.
 */

const DB_NAME = "huduma-offline";
const DB_VERSION = 1;
const STORE_PENDING = "pending-actions";

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_PENDING)) {
        db.createObjectStore(STORE_PENDING, { keyPath: "id", autoIncrement: true });
      }
    };
  });
}

async function savePendingAction(action) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORE_PENDING], "readwrite");
    const store = tx.objectStore(STORE_PENDING);
    const request = store.add({
      ...action,
      timestamp: Date.now(),
    });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function getPendingActions() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORE_PENDING], "readonly");
    const store = tx.objectStore(STORE_PENDING);
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function clearPendingAction(id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORE_PENDING], "readwrite");
    const store = tx.objectStore(STORE_PENDING);
    const request = store.delete(id);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function clearAllPendingActions() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORE_PENDING], "readwrite");
    const store = tx.objectStore(STORE_PENDING);
    const request = store.clear();
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

// Export global
window.HudumaOffline = {
  savePendingAction,
  getPendingActions,
  clearPendingAction,
  clearAllPendingActions,
};
