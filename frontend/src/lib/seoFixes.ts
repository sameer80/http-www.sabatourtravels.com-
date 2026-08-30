export const FIX_GUIDES: Record<string, string> = {
  missing_title: "WordPress → edit page → SEO title (Yoast/RankMath). Add keyword + brand.",
  missing_meta_description: "Add 140–160 char meta description with target keyword and CTA.",
  missing_h1: "Ensure exactly one H1 with primary keyword. Use H2/H3 for subheadings.",
  multiple_h1: "Keep one H1 only. Change extra H1 tags to H2 in the page editor.",
  thin_content: "Expand to 400+ useful words: routes, fares, FAQs, booking steps.",
  canonical_mismatch: "Set canonical URL to this page URL in Yoast/RankMath → Advanced → Canonical.",
  missing_alt: "Edit images in WordPress media library and add descriptive alt text with keywords.",
  duplicate_title: "Write unique title tags for each service page.",
  duplicate_meta_description: "Write unique meta descriptions per page.",
  redirect_chain: "Fix redirects in .htaccess or Redirection plugin — one hop only.",
  http_404: "Fix broken URL or add 301 redirect to the correct live page.",
  rate_limited: "Wait and re-crawl. No site edit needed.",
  fetch_error: "Check page is live and not blocking bots.",
  missing_robots_txt: "Add robots.txt in Hostinger file manager or SEO plugin.",
  missing_sitemap: "Enable XML sitemap in Yoast/RankMath or Hostinger SEO settings.",
  orphan_page: "Add internal links from related service pages to this URL.",
};

export function fixGuide(issueType: string): string {
  return FIX_GUIDES[issueType] || "Review page in WordPress admin and apply the recommended SEO change.";
}
