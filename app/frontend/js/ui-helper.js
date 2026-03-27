/**
 * UI dialog helpers — replaces native alert/confirm/prompt
 * with styled modals matching the app design system.
 */
(function () {
  var OVERLAY_ID = "ui-dialog-overlay";

  function _escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function _createOverlay() {
    var existing = document.getElementById(OVERLAY_ID);
    if (existing) existing.remove();

    var overlay = document.createElement("div");
    overlay.id = OVERLAY_ID;
    overlay.className = "modal-overlay";
    return overlay;
  }

  function _close(overlay, resolve, value) {
    overlay.remove();
    resolve(value);
  }

  /**
   * Show a styled alert modal (replaces window.alert).
   *
   * @param {string} message - Message to display
   * @param {object} [options]
   * @param {string} [options.title="Information"] - Modal title
   * @param {string} [options.type="info"] - "error" | "warning" | "info"
   * @returns {Promise<void>}
   */
  window.showAlert = function (message, options) {
    var opts = options || {};
    var title = opts.title || "Information";
    var type = opts.type || "info";
    var icon = type === "error" ? "&#10060; " : type === "warning" ? "&#9888;&#65039; " : "";

    return new Promise(function (resolve) {
      var overlay = _createOverlay();
      overlay.innerHTML =
        '<div class="modal" style="max-width:420px">' +
          '<div class="modal-header">' +
            '<span class="card-title">' + icon + _escapeHtml(title) + "</span>" +
            '<button class="btn-icon ui-dlg-close">&times;</button>' +
          "</div>" +
          '<div class="modal-body">' +
            '<p style="margin:0;white-space:pre-wrap">' + _escapeHtml(message) + "</p>" +
          "</div>" +
          '<div class="modal-footer">' +
            '<button class="btn btn-primary ui-dlg-ok">OK</button>' +
          "</div>" +
        "</div>";

      document.body.appendChild(overlay);

      var okBtn = overlay.querySelector(".ui-dlg-ok");
      okBtn.focus();

      okBtn.addEventListener("click", function () { _close(overlay, resolve); });
      overlay.querySelector(".ui-dlg-close").addEventListener("click", function () { _close(overlay, resolve); });
      overlay.addEventListener("click", function (e) {
        if (e.target === overlay) _close(overlay, resolve);
      });
      overlay.addEventListener("keydown", function (e) {
        if (e.key === "Escape") _close(overlay, resolve);
        if (e.key === "Enter") _close(overlay, resolve);
      });
    });
  };

  /**
   * Show a styled confirmation modal (replaces window.confirm).
   *
   * @param {string} message - Message to display
   * @param {object} [options]
   * @param {string} [options.title="Confirmation"] - Modal title
   * @param {string} [options.confirmText="Confirmer"] - Confirm button label
   * @param {string} [options.cancelText="Annuler"] - Cancel button label
   * @param {boolean} [options.danger=false] - Use red confirm button
   * @returns {Promise<boolean>}
   */
  window.showConfirm = function (message, options) {
    var opts = options || {};
    var title = opts.title || "Confirmation";
    var confirmText = opts.confirmText || "Confirmer";
    var cancelText = opts.cancelText || "Annuler";
    var btnClass = opts.danger ? "btn btn-danger" : "btn btn-primary";

    return new Promise(function (resolve) {
      var overlay = _createOverlay();
      overlay.innerHTML =
        '<div class="modal" style="max-width:420px">' +
          '<div class="modal-header">' +
            '<span class="card-title">' + _escapeHtml(title) + "</span>" +
            '<button class="btn-icon ui-dlg-close">&times;</button>' +
          "</div>" +
          '<div class="modal-body">' +
            '<p style="margin:0;white-space:pre-wrap">' + _escapeHtml(message) + "</p>" +
          "</div>" +
          '<div class="modal-footer">' +
            '<button class="btn btn-ghost ui-dlg-cancel">' + _escapeHtml(cancelText) + "</button>" +
            '<button class="' + btnClass + ' ui-dlg-confirm">' + _escapeHtml(confirmText) + "</button>" +
          "</div>" +
        "</div>";

      document.body.appendChild(overlay);

      var confirmBtn = overlay.querySelector(".ui-dlg-confirm");
      confirmBtn.focus();

      confirmBtn.addEventListener("click", function () { _close(overlay, resolve, true); });
      overlay.querySelector(".ui-dlg-cancel").addEventListener("click", function () { _close(overlay, resolve, false); });
      overlay.querySelector(".ui-dlg-close").addEventListener("click", function () { _close(overlay, resolve, false); });
      overlay.addEventListener("click", function (e) {
        if (e.target === overlay) _close(overlay, resolve, false);
      });
      overlay.addEventListener("keydown", function (e) {
        if (e.key === "Escape") _close(overlay, resolve, false);
      });
    });
  };

  /**
   * Show a styled prompt modal (replaces window.prompt).
   *
   * @param {string} message - Label / instruction
   * @param {object} [options]
   * @param {string} [options.title="Saisie"] - Modal title
   * @param {string} [options.placeholder=""] - Input placeholder
   * @param {string} [options.defaultValue=""] - Initial value
   * @returns {Promise<string|null>} value or null if cancelled
   */
  window.showPrompt = function (message, options) {
    var opts = options || {};
    var title = opts.title || "Saisie";
    var placeholder = opts.placeholder || "";
    var defaultValue = opts.defaultValue || "";

    return new Promise(function (resolve) {
      var overlay = _createOverlay();
      overlay.innerHTML =
        '<div class="modal" style="max-width:420px">' +
          '<div class="modal-header">' +
            '<span class="card-title">' + _escapeHtml(title) + "</span>" +
            '<button class="btn-icon ui-dlg-close">&times;</button>' +
          "</div>" +
          '<div class="modal-body">' +
            '<div class="form-label">' + _escapeHtml(message) + "</div>" +
            '<input type="text" class="form-control ui-dlg-input" placeholder="' + _escapeHtml(placeholder) + '" value="' + _escapeHtml(defaultValue) + '">' +
          "</div>" +
          '<div class="modal-footer">' +
            '<button class="btn btn-ghost ui-dlg-cancel">Annuler</button>' +
            '<button class="btn btn-primary ui-dlg-confirm">OK</button>' +
          "</div>" +
        "</div>";

      document.body.appendChild(overlay);

      var input = overlay.querySelector(".ui-dlg-input");
      input.focus();
      input.select();

      function submit() {
        _close(overlay, resolve, input.value);
      }
      function cancel() {
        _close(overlay, resolve, null);
      }

      overlay.querySelector(".ui-dlg-confirm").addEventListener("click", submit);
      overlay.querySelector(".ui-dlg-cancel").addEventListener("click", cancel);
      overlay.querySelector(".ui-dlg-close").addEventListener("click", cancel);
      overlay.addEventListener("click", function (e) {
        if (e.target === overlay) cancel();
      });
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") submit();
        if (e.key === "Escape") cancel();
      });
    });
  };
})();
