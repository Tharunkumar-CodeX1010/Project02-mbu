/* MovieScope interactions: filters, live search, modals and small UX helpers. */
(function () {
  "use strict";

  /* ---------------------------------------------------------------------
     Auto-submit filter selects (genre, year, sort)
     --------------------------------------------------------------------- */
  document.querySelectorAll(".js-auto-submit").forEach(function (select) {
    select.addEventListener("change", function () {
      if (select.form) {
        select.form.submit();
      }
    });
  });

  /* ---------------------------------------------------------------------
     Global search suggestions
     --------------------------------------------------------------------- */
  var searchForm = document.querySelector(".global-search");
  var searchInput = document.getElementById("globalSearch");
  var suggestionBox = document.getElementById("searchSuggestions");
  var searchTimer = null;
  var activeIndex = -1;
  var currentResults = [];

  function hideSuggestions() {
    if (!suggestionBox) return;
    suggestionBox.hidden = true;
    suggestionBox.innerHTML = "";
    activeIndex = -1;
    currentResults = [];
    searchInput.setAttribute("aria-expanded", "false");
  }

  function renderSuggestions(results) {
    suggestionBox.innerHTML = "";
    currentResults = results;

    if (!results.length) {
      var empty = document.createElement("div");
      empty.className = "search-empty";
      empty.textContent = "No movies found for that title.";
      suggestionBox.appendChild(empty);
      suggestionBox.hidden = false;
      searchInput.setAttribute("aria-expanded", "true");
      return;
    }

    results.forEach(function (movie, index) {
      var link = document.createElement("a");
      link.className = "search-suggestion";
      link.href = "/movies/" + movie.id;
      link.setAttribute("role", "option");
      link.dataset.index = index;

      var icon = document.createElement("span");
      icon.className = "suggestion-icon";
      icon.innerHTML = '<i class="bi bi-film"></i>';

      var copy = document.createElement("span");
      var title = document.createElement("span");
      title.className = "suggestion-title";
      title.textContent = movie.title;
      var meta = document.createElement("span");
      meta.className = "suggestion-meta";
      meta.textContent = movie.year + " · " + movie.genre;
      copy.appendChild(title);
      copy.appendChild(meta);

      link.appendChild(icon);
      link.appendChild(copy);
      suggestionBox.appendChild(link);
    });

    suggestionBox.hidden = false;
    searchInput.setAttribute("aria-expanded", "true");
  }

  function fetchSuggestions(term) {
    if (!searchForm || !suggestionBox) return;
    var endpoint = searchForm.dataset.searchEndpoint || "/api/search";
    fetch(endpoint + "?q=" + encodeURIComponent(term), {
      headers: { Accept: "application/json" },
    })
      .then(function (response) {
        if (!response.ok) throw new Error("Search request failed");
        return response.json();
      })
      .then(renderSuggestions)
      .catch(function () {
        hideSuggestions();
      });
  }

  function highlightSuggestion(index) {
    var items = suggestionBox.querySelectorAll(".search-suggestion");
    items.forEach(function (item) {
      item.classList.toggle("is-active", Number(item.dataset.index) === index);
    });
    activeIndex = index;
  }

  if (searchInput && suggestionBox) {
    searchInput.addEventListener("input", function () {
      window.clearTimeout(searchTimer);
      var term = searchInput.value.trim();
      if (term.length < 2) {
        hideSuggestions();
        return;
      }
      searchTimer = window.setTimeout(function () {
        fetchSuggestions(term);
      }, 220);
    });

    searchInput.addEventListener("keydown", function (event) {
      if (suggestionBox.hidden) return;
      var items = suggestionBox.querySelectorAll(".search-suggestion");
      if (!items.length) return;

      if (event.key === "ArrowDown") {
        event.preventDefault();
        highlightSuggestion(Math.min(activeIndex + 1, items.length - 1));
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        highlightSuggestion(Math.max(activeIndex - 1, 0));
      } else if (event.key === "Enter" && items.length) {
        // Enter follows the highlighted result, or the first result if none is highlighted.
        event.preventDefault();
        var target = items[activeIndex >= 0 ? activeIndex : 0];
        window.location.href = target.href;
      } else if (event.key === "Escape") {
        hideSuggestions();
      }
    });

    document.addEventListener("click", function (event) {
      if (!searchForm.contains(event.target)) {
        hideSuggestions();
      }
    });

    searchInput.addEventListener("focus", function () {
      if (searchInput.value.trim().length >= 2 && !suggestionBox.innerHTML) {
        fetchSuggestions(searchInput.value.trim());
      }
    });
  }

  /* ---------------------------------------------------------------------
     Manage movies: add / edit modal
     --------------------------------------------------------------------- */
  var movieModal = document.getElementById("movieModal");
  if (movieModal) {
    movieModal.addEventListener("show.bs.modal", function (event) {
      var trigger = event.relatedTarget;
      var form = document.getElementById("movieForm");
      var title = document.getElementById("movieModalLabel");
      var titleInput = document.getElementById("movieTitle");
      var yearInput = document.getElementById("movieYear");
      var genreInput = document.getElementById("movieGenre");
      var posterInput = document.getElementById("moviePoster");
      var submitButton = document.getElementById("movieSubmitButton");

      if (!trigger || trigger.dataset.mode !== "edit") {
        form.reset();
        form.setAttribute("action", form.dataset.addUrl);
        title.textContent = "Add a movie";
        submitButton.innerHTML = '<i class="bi bi-check-lg"></i> Save movie';
        return;
      }

      form.setAttribute(
        "action",
        form.dataset.editUrl.replace("/0/edit", "/" + trigger.dataset.id + "/edit")
      );
      title.textContent = "Edit movie";
      titleInput.value = trigger.dataset.title || "";
      yearInput.value = trigger.dataset.year || "";
      genreInput.value = trigger.dataset.genre || "";
      posterInput.value = trigger.dataset.poster || "";
      submitButton.innerHTML = '<i class="bi bi-check-lg"></i> Save changes';
    });
  }

  /* ---------------------------------------------------------------------
     Manage movies: delete confirmation
     --------------------------------------------------------------------- */
  var deleteModal = document.getElementById("deleteModal");
  if (deleteModal) {
    deleteModal.addEventListener("show.bs.modal", function (event) {
      var trigger = event.relatedTarget;
      if (!trigger) return;
      var form = document.getElementById("deleteForm");
      var title = document.getElementById("deleteMovieTitle");
      form.setAttribute(
        "action",
        form.dataset.deleteUrl.replace("/0/delete", "/" + trigger.dataset.id + "/delete")
      );
      title.textContent = trigger.dataset.title || "this movie";
    });
  }

  /* ---------------------------------------------------------------------
     Dismiss success/info flashes after a few seconds
     --------------------------------------------------------------------- */
  document.querySelectorAll(".app-alert.alert-success, .app-alert.alert-info").forEach(function (alert) {
    window.setTimeout(function () {
      if (!alert.classList.contains("show")) return;
      alert.classList.remove("show");
      window.setTimeout(function () {
        if (alert.parentNode) alert.parentNode.removeChild(alert);
      }, 200);
    }, 6000);
  });

  /* ---------------------------------------------------------------------
     Poster resilience
     ---------------------------------------------------------------------
     Images ship with an inline onerror fallback. This adds a timed fallback
     for visible posters when a remote host is slow or offline, so the grid
     never shows an empty frame during a demo.
     --------------------------------------------------------------------- */
  function armPosterFallback(image) {
    if (image.dataset.fallbackArmed === "1") return;
    if (image.complete && image.naturalWidth > 0) return;
    image.dataset.fallbackArmed = "1";

    var timer = window.setTimeout(function () {
      if (!image.complete || image.naturalWidth === 0) {
        image.dataset.stage = "1";
        image.src = image.dataset.fallback;
      }
    }, 5000);

    function clear() {
      window.clearTimeout(timer);
    }
    image.addEventListener("load", clear, { once: true });
    image.addEventListener("error", clear, { once: true });
  }

  var fallbackImages = document.querySelectorAll("img[data-fallback]");
  if ("IntersectionObserver" in window) {
    var posterObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            armPosterFallback(entry.target);
            posterObserver.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "200px" }
    );
    fallbackImages.forEach(function (image) {
      posterObserver.observe(image);
    });
  } else {
    fallbackImages.forEach(armPosterFallback);
  }

  /* ---------------------------------------------------------------------
     Highlight changed rating selects in My Ratings
     --------------------------------------------------------------------- */
  document.querySelectorAll(".inline-rating select").forEach(function (select) {
    var initial = select.value;
    select.addEventListener("change", function () {
      select.classList.toggle("is-changed", select.value !== initial);
    });
  });
})();
