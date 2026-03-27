/**
 * VoxPopulAI — main app entry point.
 */
(function () {
  Router.register("/vote", renderVote);
  Router.register("/personas", renderPersonas);
  Router.register("/history", renderHistory);
  Router.register("/settings", renderSettings);
  Router.init();
})();
