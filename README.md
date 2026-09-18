# Nomiarch website

Website and public documentation for Nomiarch. The product is in development; there is no runnable runtime release yet.

## Conventions

Repository: `Nomiarch/website`. Default branch: `main`. Use `feat/<description>`, `fix/<description>` or `docs/<description>` for changes and merge reviewed pull requests into main. Commit examples: `feat: add architecture overview`, `fix: correct mobile navigation`.

| Path | Purpose |
| --- | --- |
| `site/` | Public HTML, CSS and assets |
| `site/docs/` | Public documentation |
| `.github/workflows/pages.yml` | Validation and GitHub Pages deployment |
| `scripts/check_site.py` | Local links, anchors and social-preview validation |
| `site/assets/brand/` | Signature wordmark, icons and social preview assets |
| `DOMAIN-SETUP.md` | Namecheap DNS and custom domain instructions |

Only `site/` is published. Semantic HTML and responsive CSS keep this informational site simple, fast and dependency-free. Add a framework when a feature requires it.

## Preview

From the repository root:

```sh
python3 scripts/check_site.py
python3 -m http.server 8000 --directory site
```

Open http://localhost:8000. Edit pages under `site/` and shared styling in `site/styles.css`. Add guides under `site/docs/` and update navigation and `site/sitemap.xml`.

## Deployment

1. Create the public `Nomiarch/website` repository with `main` as its default branch.
2. Upload the full repository including `.github/` and `scripts/`.
3. Select **Settings → Pages → Source → GitHub Actions**.
4. Run **Actions → Deploy website** on `main`.
5. Set **Pages → Custom domain** to `nomiarch.com` before changing DNS; follow [DOMAIN-SETUP.md](DOMAIN-SETUP.md).
6. Enable **Enforce HTTPS** after domain validation and certificate issuance.

Pull requests validate local links and social previews without deployment permissions. Pushes to main validate and deploy through official GitHub Pages actions. The deploy job uses the `github-pages` environment and its configured protection rules. No personal access token is needed. Repository creation, Pages enablement and branch protection are separate settings; this workflow does not configure them.

## Social previews

Brand SVGs use editable path geometry and the same `n` glyph for the wordmark and icons. Pre-rendered assets are committed, so deployment does not need an image build. To regenerate them, run `python3 scripts/build_brand_assets.py` with Pillow, fontTools, and either CairoSVG or Inkscape installed. The script defaults to DejaVu Sans for social-card headline outlines; `--font-regular` and `--font-bold` accept explicit font paths. The logo lettering itself is defined by paths in the script.

The home page and documentation pages include Open Graph and large-image card metadata directly in the HTML, so crawlers do not need JavaScript. Each page keeps its own title, description and canonical URL while using the shared 1200 × 630 PNG at `site/assets/brand/social-preview-v1.png`.

When changing this artwork, publish a new versioned image filename and update the image URLs in every shareable page. Run `python3 scripts/check_site.py` to check that the image exists and that its dimensions match the metadata. Keep social images public, served over HTTPS, and accessible through `robots.txt`.

After deployment, inspect `https://nomiarch.com/` in [LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/) to refresh LinkedIn's cached metadata. A successful deployment and crawler fetch verify our serving configuration; LinkedIn controls when an existing preview updates.

Canonical metadata targets the intended `https://nomiarch.com` domain. `site/CNAME` records the intended domain, but Actions deployments require it to be set in repository Settings. Neither file establishes that DNS or TLS is active.

Keep runtime source in separate repositories. Do not commit secrets, customer data or private infrastructure configuration. Keep planned product capabilities clearly labelled. A software license has not been selected; describing the project's open-source ambition does not grant a license.
