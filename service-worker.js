// Service worker de retraite : l'ancienne PWA en avait un qui mettait la page en
// cache. Le supprimer du depot ne suffit pas -- il resterait installe sur les
// appareils qui ont deja visite le site et continuerait de servir l'ancienne
// version. Celui-ci vide les caches, se desinscrit, et recharge les onglets ouverts.
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const noms = await caches.keys();
    await Promise.all(noms.map((n) => caches.delete(n)));
    await self.registration.unregister();
    const clients = await self.clients.matchAll({ type: "window" });
    clients.forEach((c) => c.navigate(c.url));
  })());
});

// Plus aucune interception : tout passe directement au reseau.
