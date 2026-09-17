# Generative Artificial Intelligence

Marketing site for **Generative Artificial Intelligence** — `genai-usa.com`.

Monochrome editorial landing page, inspired by the Endel Manifesto: pure black background, white ink, muted gray, Roboto 400, centered editorial layout, scroll-driven statement reveals, and a full-screen cinematic hero video.

## Stack
- Static HTML / CSS / vanilla JS — no build step, no framework
- Hero video: `assets/video/hero.mp4` (Pexels, free license)

## Structure
```
index.html            # single landing page
assets/video/hero.mp4 # cinematic hero video
```

## Run locally
Open `index.html` in a browser, or:
```bash
python3 -m http.server 8080
```

## Deploy (free)
**Cloudflare Pages** — connect this repo, no build command, output directory `/` (root).
Also compatible with Netlify and Vercel free tiers.
