# 이력서 수정 규칙

이력서는 `/Users/hc.cho/obsidian-projects/my obsidian/Resume/` 아래에서 관리된다.

## 반드시 이 순서를 따를 것

**1. `resume.md`만 수정한다. HTML 파일 직접 수정 금지.**

**2. HTML 재생성:**
```bash
node "/Users/hc.cho/obsidian-projects/my obsidian/Resume/scripts/md-to-html.mjs" <회사명>
```

**3. PDF 생성 (Codex 슬래시 커맨드):**
```
/resume-pdf <회사명>
```

또는 수동으로:
```bash
cat << 'EOF' > /tmp/make_pdf.mjs
import puppeteer from '/tmp/node_modules/puppeteer/lib/puppeteer/puppeteer.js';
import { readFileSync } from 'fs';
const company = 'SMR';
const base = `/Users/hc.cho/obsidian-projects/my obsidian/Resume/${company}`;
const html = readFileSync(`${base}/resume.html`, 'utf8');
const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true, args: ['--no-sandbox']
});
const page = await browser.newPage();
await page.setContent(html, { waitUntil: 'networkidle0' });
await page.pdf({
  path: `${base}/resume.pdf`, format: 'A4', printBackground: true,
  displayHeaderFooter: false,
  margin: { top: '15mm', bottom: '15mm', left: '15mm', right: '15mm' }
});
await browser.close();
EOF
pkill -f Preview 2>/dev/null; sleep 1
node /tmp/make_pdf.mjs
open "/Users/hc.cho/obsidian-projects/my obsidian/Resume/SMR/resume.pdf"
```

## 금지 사항

- **HTML 직접 수정 금지** — md-to-html.mjs 실행 시 덮어씌워짐
- **Chrome headless 직접 호출 금지** — PDF 상단에 제목·타임스탬프가 찍힘
- **`page.goto('file://...')` 금지** — 캐시 문제 발생, `setContent` 사용

## 디자인·CSS 변경 시

`scripts/md-to-html.mjs` 안의 CSS 상수를 수정한다. 모든 회사 이력서에 일괄 반영됨.
