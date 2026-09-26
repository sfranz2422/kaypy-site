/* Two small jobs, and nothing the page needs to be readable.
 *
 * The site is static HTML. If this file 404s or a school network blocks the
 * CDN above it, every page still reads correctly — the code is just grey and
 * the sidebar just does not follow you down the page. That is deliberate:
 * highlighting used to happen at build time, and the reason it can move into
 * the browser at all is that nothing depends on it.
 */
(function () {
  "use strict";

  // ------------------------------------------------- 1. colour the code
  //
  // hljs.highlightAll() is not used. It highlights EVERY <pre><code> on the
  // page, guessing the language for any block without a class — and a guess
  // on a three-line snippet is usually wrong, which looks like a bug in the
  // page rather than in the guesser. Only blocks that say what they are get
  // touched.
  if (window.hljs) {
    document.querySelectorAll("pre code[class*=language-]").forEach(function (el) {
      try {
        hljs.highlightElement(el);
      } catch (err) {
        // A missing language pack throws. Grey code is fine; a page that
        // stops running its script halfway is not.
        if (window.console) console.warn("highlight:", err);
      }
    });
  }

  // ------------------------------- 2. mark where you are in the sidebar
  //
  // The "On this page" list is plain links. This adds `.here` to the one you
  // are currently reading. IntersectionObserver rather than a scroll handler,
  // so nothing runs on every pixel of scrolling.
  var links = document.querySelectorAll(".toc-link");
  if (!links.length || !("IntersectionObserver" in window)) return;

  var byId = {};
  var headings = [];
  links.forEach(function (link) {
    var id = decodeURIComponent(link.getAttribute("href").slice(1));
    var heading = document.getElementById(id);
    // A sidebar link whose heading is gone is a dead anchor. Skipped rather
    // than crashing the observer on a null.
    if (!heading) return;
    byId[id] = link;
    headings.push(heading);
  });
  if (!headings.length) return;

  var seen = [];

  function paint() {
    var current = seen.length ? seen[seen.length - 1] : null;
    links.forEach(function (link) { link.classList.remove("here"); });
    if (current && byId[current]) byId[current].classList.add("here");
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      var id = entry.target.id;
      var at = seen.indexOf(id);
      if (entry.isIntersecting) {
        if (at === -1) seen.push(id);
      } else if (at !== -1) {
        seen.splice(at, 1);
      }
    });
    paint();
  }, {
    // The navbar is sticky and about 60px tall, so a heading is "reached"
    // when it clears that, not when it clears the top of the window.
    rootMargin: "-70px 0px -70% 0px",
  });

  headings.forEach(function (heading) { observer.observe(heading); });
})();
