#!/usr/bin/env node
/* 덱을 PDF로 저장: 슬라이드 1장 = PDF 1쪽 (1280×720).
   사용: node export_pdf.js deck.html [out.pdf] [--mathjax 경로] [--fonts fontsource폴더]
   - 툴바·발표 버튼은 빼고, 축소를 풀어 원래 크기로 찍는다.
   - 웹 글꼴(Google Fonts)을 못 받는 환경이면 반드시 --fonts를 준다. 안 주면 대체 글꼴이라 화면과 달라진다.
   - '눌러서 답 보기'(details)는 접힌 상태로 나온다.
*/
const path = require('path');
const { chromium } = require('playwright');
const { setupRoutes } = require('./_routes');
const args = process.argv.slice(2);
const file = path.resolve(args[0]);
const out = args[1] && !args[1].startsWith('--') ? path.resolve(args[1]) : file.replace(/\.html?$/i, '') + '.pdf';
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1340, height: 900 } });
  const r = await setupRoutes(pg, args);
  await pg.goto('file://' + file, { waitUntil: 'load' });
  await pg.evaluate(() => document.fonts && document.fonts.ready); await pg.waitForTimeout(3500);
  const fontOk = await pg.evaluate(() => document.fonts.check('16px "Noto Sans KR"', '가'));
  await pg.addStyleTag({ content: `
    html,body{background:#fff!important;margin:0!important;padding:0!important}
    body::before,.bar,.pnav{display:none!important}
    .deck{display:block!important;padding:0!important;gap:0!important}
    .sw{width:1280px!important;height:720px!important;max-width:none!important;overflow:hidden;break-after:page;page-break-after:always}
    .sw:last-child{break-after:auto;page-break-after:auto}
    .slide{transform:none!important;box-shadow:none!important}
    @page{size:1280px 720px;margin:0}` });
  await pg.evaluate(() => document.documentElement.style.setProperty('--s', 1));
  await pg.waitForTimeout(300);
  await pg.pdf({ path: out, width: '1280px', height: '720px', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  const n = await pg.evaluate(() => document.querySelectorAll('.slide').length);
  console.log(`PDF ${n}쪽 -> ${out}`);
  if (!fontOk) console.log('주의: Noto Sans KR을 불러오지 못해 대체 글꼴로 저장됨 (--fonts 지정 필요)');
  await b.close();
})();
