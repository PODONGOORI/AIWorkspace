/* 검사·PDF 스크립트 공용: CDN이 막힌 환경에서 MathJax·Noto Sans KR을 로컬 파일로 대신 공급한다.
   --mathjax <tex-svg.js 경로>   : npm pack mathjax@3.2.2 → package/es5/tex-svg.js
   --fonts   <fontsource 폴더>   : npm pack @fontsource/noto-sans-kr → package/
   글꼴을 넣지 않으면 대체 글꼴로 그려져 줄바꿈·여백이 브라우저 화면과 달라진다. */
const fs = require('fs'), path = require('path');
function opt(args, name) { const i = args.indexOf(name); return i > -1 ? args[i + 1] : null; }
async function setupRoutes(pg, args) {
  const mj = opt(args, '--mathjax'), fd = opt(args, '--fonts');
  if (mj) await pg.route('https://cdnjs.cloudflare.com/**', r => r.fulfill({ contentType: 'application/javascript', body: fs.readFileSync(mj, 'utf8') }));
  if (fd) {
    const css = [300, 400, 500, 700, 800].map(w => fs.readFileSync(path.join(fd, w + '.css'), 'utf8')).join('\n')
      .replace(/url\(\.\/files\//g, 'url(https://fonts.gstatic.com/fs/');
    await pg.route('https://fonts.googleapis.com/**', r => r.fulfill({ contentType: 'text/css', body: css }));
    await pg.route('https://fonts.gstatic.com/fs/**', r => {
      const f = path.join(fd, 'files', path.basename(new URL(r.request().url()).pathname));
      fs.existsSync(f) ? r.fulfill({ contentType: f.endsWith('2') ? 'font/woff2' : 'font/woff', body: fs.readFileSync(f) }) : r.abort();
    });
  }
  return { fonts: !!fd };
}
module.exports = { setupRoutes, opt };
