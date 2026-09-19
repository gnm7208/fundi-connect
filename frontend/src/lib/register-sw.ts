/**
 * Registers the service worker that keeps the app openable without a signal.
 *
 * Only in production builds: in dev the Vite client serves modules that must
 * never be cached.
 */
export function registerServiceWorker() {
  if (!import.meta.env.PROD) return
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return

  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      // An unavailable service worker only costs offline shell loading; the
      // app itself still works.
    })
  })
}
