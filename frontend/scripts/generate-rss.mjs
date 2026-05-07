import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');
const dataPath = path.join(rootDir, 'src', 'data', 'research.json');
const outPath = path.join(rootDir, 'public', 'rss.xml');

const DOMAIN = process.env.VITE_APP_URL || 'https://10kiq.com';
const AUTHOR_EMAIL = 'happyislearning@gmail.com (Harpreet Ahluwalia)';

function escapeXml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function generateRss() {
  console.log('📰 Generating RSS feed...');
  if (!fs.existsSync(dataPath)) {
    console.error('❌ research.json not found at', dataPath);
    process.exit(1);
  }

  const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
  const articles = [...(data.articles || [])];
  articles.sort((a, b) => new Date(b.sortDate) - new Date(a.sortDate));

  const buildDate = new Date().toUTCString();

  let rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:atom="http://www.w3.org/2005/Atom"
  xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
  <title>${escapeXml(data.title)}</title>
  <description>${escapeXml(data.description)}</description>
  <link>${DOMAIN}/research</link>
  <atom:link href="${DOMAIN}/rss.xml" rel="self" type="application/rss+xml"/>
  <language>en-us</language>
  <managingEditor>${AUTHOR_EMAIL}</managingEditor>
  <webMaster>${AUTHOR_EMAIL}</webMaster>
  <lastBuildDate>${buildDate}</lastBuildDate>
  <ttl>1440</ttl>
`;

  for (const item of articles) {
    const pubDate = new Date(item.sortDate).toUTCString();
    const guid = `${DOMAIN}/research/${item.id}`;
    const link = item.url || `${DOMAIN}/research#${item.id}`;

    rss += `  <item>
    <title>${escapeXml(item.title)}</title>
    <link>${link}</link>
    <guid isPermaLink="false">${guid}</guid>
    <pubDate>${pubDate}</pubDate>
    <dc:creator>Harpreet Ahluwalia</dc:creator>
    <category>${escapeXml(item.category || 'Research')}</category>
    <description><![CDATA[<p>${item.description || ''}</p>]]></description>
  </item>
`;
  }

  rss += `</channel>\n</rss>\n`;
  fs.writeFileSync(outPath, rss, 'utf8');
  console.log(`✨ RSS feed → ${outPath} (${articles.length} items, ${(Buffer.byteLength(rss) / 1024).toFixed(1)} KB)`);
}

generateRss();
