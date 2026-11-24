#!/usr/bin/env node
/* 덱 검사: 슬라이드마다 넘침·제목 길이·아래 여백을 재고 PNG를 저장한다.
   사용: node check_deck.js deck.html [출력폴더] [--mathjax 경로] [--fonts fontsource폴더]
   - 출력폴더에 s1.png, s2.png … 저장 (기본: deck 옆 _check/)
   - MathJax CDN이 막힌 환경이면 --mathjax로 로컬 파일을 지정 (npm pack mathjax@3.2.2)
   판정 (슬라이드별):
     over N   : 본문(.bd) 밖으로 N px 넘침 → 반드시 고친다
     note N   : 하단 요약 바와 N px 겹침 → 고친다 (단, 칸의 빈 padding만 겹치면 무시 가능)
     TITLE    : 제목이 길어 오른쪽 선이 사라짐 → 주제를 줄인다
     SVG id N : 그림 내용이 자기 viewBox 밖으로 N 넘침 → 그림 H/padB를 viewBox와 맞춘다 (구분선·표와 겹치는 원인)
     gap a/b  : 칸별 아래 여백 px. 60 이상이면 내용·그림을 키워 채운다
*/
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const { setupRoutes } = require('./_routes');
const args = process.argv.slice(2);
const file = path.resolve(args[0]);
let out = args[1] && !args[1].startsWith('--') ? path.resolve(args[1]) : path.join(path.dirname(file), '_check');
fs.mkdirSync(out, { recursive: true });
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1340, height: 900 } });
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await setupRoutes(pg, args);
  await pg.goto('file://' + file); await pg.waitForTimeout(3500);
  const res = await pg.evaluate(() => [...document.querySelectorAll('.slide')].map((s, i) => {
    const o = [];
    s.querySelectorAll('svg.tr').forEach(g => { const vb = g.viewBox.baseVal; if (!vb || !vb.width) return; let bb; try { bb = g.getBBox(); } catch (e) { return; }
      const ov = Math.max(vb.x - bb.x, vb.y - bb.y, bb.x + bb.width - vb.x - vb.width, bb.y + bb.height - vb.y - vb.height); if (ov > 2) o.push('SVG ' + (g.id || '?') + ' ' + Math.round(ov)); });
    const rule = s.querySelector('.hd .rule'); if (rule && rule.getBoundingClientRect().width < 30) o.push('TITLE');
    const bd = s.querySelector('.bd');
    if (bd) {
      const L = bd.getBoundingClientRect(); let over = 0;
      bd.querySelectorAll('*').forEach(e => { const r = e.getBoundingClientRect(); if (r.width && r.height) over = Math.max(over, r.bottom - L.bottom, r.right - L.right); });
      if (over > 1) o.push('over' + Math.round(over));
      const note = bd.querySelector(':scope > .note');
      const lim = note ? note.getBoundingClientRect().top - 12 : L.bottom;
      if (note) { const nt = note.getBoundingClientRect().top; let c = 0; bd.querySelectorAll('li,td,th,p,svg,.box,.eq,details,table').forEach(e => { if (note.contains(e)) return; const r = e.getBoundingClientRect(); if (r.height && r.bottom > nt + 1 && r.top < nt) c = Math.max(c, r.bottom - nt); }); if (c > 1) o.push('note' + Math.round(c)); }
      const cols = [...bd.querySelectorAll(':scope .two > div')]; const tg = cols.length ? cols : [bd];
      const gaps = tg.map(c => { let m = c.getBoundingClientRect().top; c.querySelectorAll('*').forEach(e => { if (note && note.contains(e)) return; if (e.closest('svg') && e.tagName !== 'svg') return; if (e.children.length && !['svg', 'TABLE'].includes(e.tagName)) return; const r = e.getBoundingClientRect(); if (r.height) m = Math.max(m, r.bottom); }); return Math.round(lim - m); });
      o.push('gap ' + gaps.join('/'));
    }
    return (i + 1) + ': ' + o.join(', ');
  }));
  const mjx = await pg.evaluate(() => document.querySelectorAll('mjx-merror,[data-mjx-error]').length);
  const sl = await pg.$$('.slide'); for (let i = 0; i < sl.length; i++) await sl[i].screenshot({ path: path.join(out, 's' + (i + 1) + '.png') });
  console.log(res.join('\n')); console.log('수식 오류: ' + mjx + (errs.length ? '\n스크립트 오류: ' + errs.join(' | ') : '')); console.log('PNG: ' + out);
  await b.close();
})();
