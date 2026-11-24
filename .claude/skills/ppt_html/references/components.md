# 부품 목록 (ppt_html)

모든 좌표는 1280×720 캔버스 기준. 본문 영역 `.bd`는 top 190 ~ bottom 674 (높이 484px), 탭형은 left 197.

## 1. 슬라이드 틀 (모든 본문 장에 필수)
```html
<section class="slide">            <!-- 탭을 쓰면 class="slide tb" -->
 <div class="hd"><span class="no">01</span><span class="tt"><span class="sec2">섹션</span><span class="sep">|</span>주제</span><span class="rule"></span></div>
 <div class="tag">섹션</div>
 <div class="ins">이 장의 결론 한 문장</div>
 <div class="bd"> … </div>
 <div class="pg"></div>              <!-- 쪽번호는 자동 -->
</section>
```
- 제목: 번호(가는 남색) + 섹션명(보통) `|` 주제(굵게). 주제는 한 줄, 공백 포함 약 22자 이내. 길면 `.hd .rule`이 사라진다(검사 스크립트가 TITLE로 표시).
- `.tag`: 우측 상단, 제목 오른쪽 선 바로 위. 섹션명을 그대로 쓴다.
- `.ins`: 남색 핵심 메시지 바. 결론 한 문장(약 60자 이내, 한 줄). 질문형이나 소제목형 금지.
- 출처가 있으면 `<p class="src">출처: …</p>`를 `.bd` 밖, `.pg` 앞에 둔다.

## 2. 본문 배치 패턴 (밀도 순)
| 패턴 | 구조 | 쓸 때 |
|---|---|---|
| 그림 위 + 두 칸 | `.bd`를 `display:flex;flex-direction:column;gap:8px`로, 위에 `svg.tr`(높이 190~240), 아래 `<div class="two split">` | 그림이 핵심인 장 (가장 자주 씀) |
| 두 칸 | `<div class="two">` 또는 `.two.w6`(왼쪽 넓게) | 표 + 해설, 비교 |
| 카드 3개 | `<div class="cards3">` + `.card3` | 원칙·사실·요소 나열 |
| 표 단독 | `table.t` 하나 | 정의·대응표. 행이 적으면 자동으로 행 높이가 늘어난다 |
| 그림 3개 나란히 | `display:grid;grid-template-columns:repeat(3,1fr)` | 단계 비교(Step 1·2·3) |

하단 요약 바 `.note`를 쓰면 위 칸에 `padding-bottom:54px`(그림 위+두 칸) 또는 `height:calc(100% - 54px)`(두 칸만)를 준다.

## 3. 텍스트 부품
- 소제목: `<div class="sub"><span class="num">1</span><span class="t">소제목</span><small>오른쪽 보조</small></div>` → 번호는 ①②로 자동 변환.
- 글머리: `<ul class="ul"><li><b>핵심어</b>: 설명<span class="s">보조 한 줄</span></li></ul>`. 항목은 2~4개, 항목당 1~2줄.
- 카드: `<div class="box"><h4>제목</h4>내용</div>` (흰 바탕·둥근 모서리·옅은 그림자).
- 하단 요약 바: `<div class="note"><b>라벨</b>한 줄</div>` (`.bd`의 직계 자식).
- 눌러서 답 보기: `<details><summary>Q. …</summary><p>답</p></details>`.
- 수식: 본문 `$…$`, 크게 `<div class="eq">\[ … \]</div>` (작게 `.eq.sm`). `\underbrace{…}_{\text{설명}}`로 항 이름 달기.

## 4. 표
```html
<table class="t c tight">
 <thead><tr><th>구분</th><th>값</th></tr></thead>
 <tbody>
  <tr><td class="k">항목</td><td class="best">강조</td></tr>
  <tr class="sep"><td class="l">왼쪽 정렬</td><td class="na">—</td></tr>
 </tbody>
</table>
```
- 기본 16px·패딩 10px. 칸이 좁거나 행이 많으면 `.c`(14px) → `.c.tight`(패딩 5px).
- `td.k` 굵은 머리칸, `td.best` 연남색 강조, `td.v` 남색 숫자, `td.na` 흐린 칸, `tr.sep` 그룹 구분선, `td.l` 왼쪽 정렬.
- `rowspan`으로 같은 항목 묶기.

## 5. 인덱스 탭 (단계 진행형)
```html
<section class="slide tb"> …
 <div class="tabs" data-on="2" data-items="설정|Step 1<br>t = 3|Step 2|정책표"></div>
```
- 같은 묶음의 모든 장에 같은 `data-items`, 현재 장 번호만 `data-on`. 탭은 페이지 아래까지 자동으로 늘어난다.

## 6. 그림 (SVG)
`window.PPT`의 도우미를 스크립트의 "덱별 그림은 여기에" 자리에서 쓴다.

```js
PPT.graph(document.getElementById('fig1'),{
  W:1123,H:220,padT:60,padB:40,r:24,
  nodes:{S:[0,1],A:[1,0],B:[1,2],E:[2,1]},          // [열, 행]
  edges:[['S','A','2'],['S','B','5'],['A','E','7'],['B','E','3']],
  cols:['출발','1단계','도착'],                        // 열 제목(선택)
  ncls:function(id){return id==='S'?'st':'';},        // '', 'on'(남색 채움), 'st'(굵은 테두리), 'dash'(아직)
  ecls:function(e){return e[1]==='B'?'hl':'w';},      // 'w' 기본, 'hl' 선택, 'd' 점선, 'gr' 비교 점선, 'f' 흐림, 'dsh' 아직
  val:function(id){return id==='E'?'V = 0':null;}     // 노드 위(맨 아래 행은 아래) 숫자
});
```
- 단계별 설명은 같은 그림을 장마다 다시 그리고 상태만 바꾼다: 이번 열 `on`, 끝난 부분 실선(`w`), 아직인 부분 `dash`/`dsh`.
- 직접 그릴 때는 `PPT.E(태그,속성,글자)`, `PPT.defs(svg)` 후 `PPT.arrow(svg,x1,y1,x2,y2,'hl','c',r1,r2)`, 여러 줄 글자는 `PPT.multiline`.
- 글자는 노드·선과 겹치지 않게: 라벨은 선 중간보다 출발점 쪽(labAt 0.3 근처)으로, 노드 아래 공간이나 그림 위·아래 여백에 둔다. 겹치면 그림 높이(`H`, `padT`)를 늘린다.
- `svg.tr`는 칸 너비에 맞춰 줄어든다. `width/height/viewBox`를 같은 값으로 주고, 세로 크기는 `style="height:…px"`로 고정.

## 7. 표지 · 목차
- 표지 `.slide.cv`: 소속(우측 상단) · 가는 선 · 제목(46px 남색) · 부제(29px 회색) · 일러스트 · 하단 남색 띠(왼쪽 발표일시, 오른쪽 행사·발표자).
- 목차 `.slide.toc2`: 큰 `Contents`(80px) + 오른쪽 번호 목록(`li` + `small` 한 줄 설명) + 좌우 반전 일러스트. **목차에는 핵심 메시지 바나 요약 박스를 넣지 않는다.**
- 일러스트 자리는 `{{COVER_ILL}}`, `scripts/inline_assets.py`가 채운다.
