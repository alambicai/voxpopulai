/**
 * Minimal hash-based router.
 */
const Router = {
  routes: {},

  register(path, handler) {
    this.routes[path] = handler;
  },

  navigate(path) {
    window.location.hash = "#" + path;
  },

  resolve() {
    const hash = window.location.hash.slice(1) || "/vote";
    const route = Object.keys(this.routes).find((r) => hash.startsWith(r));
    if (route && this.routes[route]) {
      document.querySelectorAll(".nav-links a").forEach((a) => {
        a.classList.toggle("active", a.dataset.route === route.slice(1));
      });
      this.routes[route]();
    }
  },

  init() {
    window.addEventListener("hashchange", () => this.resolve());
    this.resolve();
  },
};
