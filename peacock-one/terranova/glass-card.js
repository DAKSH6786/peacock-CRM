/**
 * Liquid-glass card frame sync.
 *
 * The card is a window onto a refracted duplicate of the background video.
 * We size the duplicate to the VIEWPORT (not the card) deliberately: the SVG
 * filter shifts each colour channel by a different amount, so the filtered
 * element's own leading edges show hard channel-separation bands. At viewport
 * size those bands fall outside the card and only clean refraction shows.
 *
 * The duplicate stays at 1× even on retina: the SVG filter's cost scales with
 * pixel count, and what shows through is a soft refraction where 4× the filter
 * work buys nothing.
 */

const DUP_PIXEL_RATIO = 1;

const video = document.getElementById("bg-video");
const card = document.querySelector("[data-glass-card]");
const dupContainer = document.getElementById("dup-video-container");
const canvas = document.getElementById("dup-image");
const ctx = canvas?.getContext("2d", { alpha: false });

let lastW = 0;
let lastH = 0;

function syncFrame() {
  if (!video || !card || !dupContainer || !canvas || !ctx) {
    requestAnimationFrame(syncFrame);
    return;
  }

  const rect = card.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0 || video.videoWidth === 0 || video.videoHeight === 0) {
    requestAnimationFrame(syncFrame);
    return;
  }

  const vw = document.documentElement.clientWidth;
  const vh = document.documentElement.clientHeight;

  dupContainer.style.left = `${-rect.left}px`;
  dupContainer.style.top = `${-rect.top}px`;
  dupContainer.style.width = `${vw}px`;
  dupContainer.style.height = `${vh}px`;

  const w = Math.max(1, Math.round(vw * DUP_PIXEL_RATIO));
  const h = Math.max(1, Math.round(vh * DUP_PIXEL_RATIO));
  if (w !== lastW || h !== lastH) {
    canvas.width = w;
    canvas.height = h;
    lastW = w;
    lastH = h;
  }

  // Reproduce object-fit: cover for the video frame into the viewport-sized canvas.
  try {
    const cover = Math.max(vw / video.videoWidth, vh / video.videoHeight);
    const sw = vw / cover;
    const sh = vh / cover;
    const sx = (video.videoWidth - sw) / 2;
    const sy = (video.videoHeight - sh) / 2;
    ctx.drawImage(video, sx, sy, sw, sh, 0, 0, w, h);
  } catch {
    // Frame may not be decodable yet.
  }

  requestAnimationFrame(syncFrame);
}

requestAnimationFrame(syncFrame);
