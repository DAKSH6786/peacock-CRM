const menu = document.getElementById("menu");
const menuOpen = document.getElementById("menu-open");
const menuClose = document.getElementById("menu-close");
const menuBackdrop = document.getElementById("menu-backdrop");

function setMenu(open) {
  if (!menu || !menuOpen || !menuClose) return;

  menu.classList.toggle("is-open", open);
  menuOpen.setAttribute("aria-expanded", open ? "true" : "false");

  if (open) {
    menuClose.focus({ preventScroll: true });
  } else {
    menuOpen.focus({ preventScroll: true });
  }
}

menuOpen?.addEventListener("click", () => setMenu(true));
menuClose?.addEventListener("click", () => setMenu(false));
menuBackdrop?.addEventListener("click", () => setMenu(false));

menu?.querySelectorAll(".menu__link").forEach((link) => {
  link.addEventListener("click", () => setMenu(false));
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && menu?.classList.contains("is-open")) {
    setMenu(false);
  }
});
