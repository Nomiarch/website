# Connect nomiarch.com to GitHub Pages

## GitHub first

1. Create Nomiarch/website as a public repository and upload the entire repository structure to main.
2. In Settings → Pages, select GitHub Actions as the publishing source, then run the Deploy website workflow from the Actions tab.
3. Set Custom domain to nomiarch.com and Save **before** changing DNS.
4. Recommended: verify nomiarch.com under Nomiarch organization Settings → Pages. Add the exact TXT verification record GitHub supplies. No verification token is invented or included here.

## Namecheap

If Namecheap hosts the domain's DNS, open Domain List → nomiarch.com → Manage → Advanced DNS → Host Records. Add the following with TTL Automatic:

| Type | Host | Value |
| --- | --- | --- |
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | nomiarch.github.io |

Replace only conflicting A/AAAA, CNAME, or URL Redirect records at @ and www. Keep email/MX and unrelated TXT records. Do not combine these GitHub targets with the earlier Sites targets. If DNS is hosted elsewhere, edit the authoritative DNS provider instead.

DNS can take up to 24 hours. After GitHub completes DNS validation and certificate issuance, enable Enforce HTTPS and test both nomiarch.com and www.nomiarch.com. With nomiarch.com selected as the custom domain, GitHub redirects www to the apex when both DNS records are correct.

Reference: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
