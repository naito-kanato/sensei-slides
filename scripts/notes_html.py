"""発表者ノート（原稿）を、スライド画像と横並びで読める1枚のHTMLにする。

    python notes_html.py "<資料名>_スライド.pptx"            # → <資料名>_原稿.html（スライドと同じフォルダ）
    python notes_html.py deck.pptx --pdf deck.pdf -o out.html  # 既にあるスライドPDFを使う・出力先を指定

- スライド画像は、PowerPoint で一時フォルダに書き出した PDF から作って HTML に埋め込み（1ファイルで完結）、PDF は消す
  （原稿HTMLがあるのでスライドの PDF はユーザーのフォルダに残さない）
- 各スライド：左にスライド画像、右に「番号・●見出し・青帯の結論・原稿」。幅が狭い画面では縦に並ぶ
- 原稿は1文ずつ段落に分け、「（資料外の補足）」「（教科書外の補足）」は灰色、「（要確認）」は橙で目立たせる
- ←/→ または j/k でスライド単位に移動、上部の番号から直接飛べる。ブラウザの印刷で PDF にもできる（1スライドずつ改ページ）
- コメントモード（C キーか上部の「コメント」ボタン）：原稿の文章を選ぶ／スライドをドラッグで囲むと、その場所にコメントできる。
  コメントはブラウザ（localStorage）に保存され、「一覧」→「書き出し」で <資料名>_コメント.json になる。
  それを comments_read.py で読み、回答スライドと原稿を作る（SKILL.md の手順8）
"""
import argparse
import base64
import html
import io
import re
import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER


MARKS = "●■◆▶▷►○□◇◎・▪▸•"   # 見出しの印


def slide_texts(prs):
    """各スライドの（タイトル, ●見出し, 青帯の結論, 原稿）を取り出す。"""
    out = []
    for sl in prs.slides:
        title = heading = band = ""
        for sh in sl.shapes:
            if sh.is_placeholder:
                pf = sh.placeholder_format
                if pf.type == PP_PLACEHOLDER.TITLE:
                    title = sh.text_frame.text.strip()
                elif pf.idx == 13:
                    band = sh.text_frame.text.strip()
            elif sh.name == "見出し" and sh.has_text_frame:
                t = sh.text_frame.text.strip()
                if t[:1] in MARKS:
                    heading = t.lstrip(MARKS).strip()
                else:   # 結論を見出しにする構造（結論ヘッダー・結論タイトル・副題）：印の無い「見出し」は、その枚の結論
                    band = band or t
            elif sh.name == "結論の一文" and sh.has_text_frame:   # 左の柱の結論
                band = band or sh.text_frame.text.strip()
        if "　／　" in title:   # 結論が上にある構造では、●見出しをタイトルの行の後ろに「／ 見出し」と足してある
            title, heading = (x.strip() for x in title.split("　／　", 1))
        if not title:  # 表紙・区切り：いちばん大きい文字を題目に
            boxes = [sh for sh in sl.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
            if boxes:
                big = max(boxes, key=lambda s: max(((r.font.size or 0) for p in s.text_frame.paragraphs for r in p.runs), default=0))
                title = big.text_frame.text.strip()
        notes = sl.notes_slide.notes_text_frame.text.strip() if sl.has_notes_slide else ""
        out.append((title, heading, band, notes))
    return out


QID = re.compile(r"^\s*(\d+-\d+)[\s　]+(.*)$", re.S)


def slide_questions(prs):
    """確認問題のスライド（●見出しに「問題」があり「解答」がない）から、問題番号と問題文を取り出す。
    問題は「1-1　問題文」の形で1問1つのテキスト枠になっている（build.py の qa()）。戻り値はスライドごとの [(番号, 問題文)]"""
    out = []
    for sl in prs.slides:
        heading = next((sh.text_frame.text for sh in sl.shapes if sh.name == "見出し" and sh.has_text_frame), "")
        qs = []
        if "問題" in heading and "解答" not in heading:
            for sh in sl.shapes:
                if sh.has_text_frame and not sh.is_placeholder:
                    m = QID.match(sh.text_frame.text)
                    if m:
                        qs.append((m.group(1), re.sub(r"\s*\n[\s　]*", "", m.group(2)).strip()))
        out.append(qs)
    return out


def slide_images(pdf_path, width=1400, quality=82):
    import pymupdf as fitz  # PyMuPDF（古い呼び名 fitz は将来なくなる）。PDF を使う所でだけ読む（無くても他は動く）
    doc = fitz.open(pdf_path)
    imgs = []
    for page in doc:
        z = width / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(z, z))
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=quality, optimize=True)
        imgs.append(base64.b64encode(buf.getvalue()).decode())
    doc.close()   # 一時フォルダを消せるように閉じる（Windows）
    return imgs


SENT = re.compile(r"[^。！？]*[。！？]+[」）』]*|[^。！？]+$")


LAB = r"(資料外の補足|教科書外の補足|資料外|要確認|図について)"


def tagify(esc):
    """先頭の「（資料外の補足）」などを札に変える。戻り値 (HTML, 札を付けたか)。"""
    if re.match(r"^（" + LAB + "：", esc):          # 「（教科書外の補足：本文。）」
        return re.sub(r"）$", "", re.sub(r"^（" + LAB + "：", r'<span class="tag">\1</span>', esc)), True
    if re.match(r"^（" + LAB + "）", esc):          # 「（資料外の補足）本文。」
        return re.sub(r"^（" + LAB + "）", r'<span class="tag">\1</span>', esc), True
    return esc, False


def format_notes(text):
    """原稿をHTMLの段落に。
    - 改行のある原稿（読み上げ原稿, notes.md）：行＝段落のまま。「※」で始まる行は読まない補足として灰色の囲みに
    - 改行のない原稿（従来のメモ形式）：1文ずつ段落に分ける
    資料外の補足・要確認・図についての札は、どちらの形でも付ける。"""
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if len(lines) > 1:
        out = []
        for l in lines:
            if l.startswith("※"):
                body, tagged = tagify(html.escape(l[1:].strip()))
                cls = "aside check" if "要確認" in l[:8] else "aside"
                out.append(f'<p class="{cls}">{body if tagged else "<span class=tag>補足</span>" + body}</p>')
            else:
                out.append(f"<p>{html.escape(l)}</p>")
        return "\n".join(out)
    paras = []
    for block in lines:
        for s in SENT.findall(block):
            s = s.strip()
            if not s:
                continue
            cls = ""
            if re.match(r"^（(資料外|教科書外)", s) or "資料外の補足" in s[:12]:
                cls = "extra"
            elif s.startswith("（要確認）") or s.startswith("（要確認"):
                cls = "check"
            elif re.match(r"^（図について", s):
                cls = "fig"
            esc, _ = tagify(html.escape(s))
            paras.append(f'<p class="{cls}">{esc}</p>' if cls else f"<p>{esc}</p>")
    return "\n".join(paras) or '<p class="empty">（原稿なし）</p>'


CSS = """
:root{--band:#215F99;--text:#3d3d3e;--ink:#1f2a36;--muted:#8c8c8c;--line:#e3e8ef;--bg:#f6f8fb;--card:#fff;--extra:#7a7a7a;--check:#b45309;--accent:#005AFF}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font-family:"BIZ UDPGothic","Yu Gothic UI","Meiryo",system-ui,sans-serif;line-height:1.85}
header{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line);padding:10px 20px}
header h1{margin:0;font-size:18px;color:var(--band)}
header .sub{font-size:12px;color:var(--muted);margin-left:10px;font-weight:normal}
nav{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
nav a{font-size:12px;min-width:28px;text-align:center;padding:2px 6px;border:1px solid var(--line);border-radius:4px;color:var(--text);text-decoration:none}
nav a.on{background:var(--band);color:#fff;border-color:var(--band)}
main{margin:0 auto;padding:14px 16px 60vh}
section{display:grid;grid-template-columns:minmax(0,1.75fr) minmax(0,1fr);gap:22px;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:18px;margin:0 0 18px;scroll-margin-top:96px}
section.cur{border-color:var(--band);box-shadow:0 0 0 2px rgba(33,95,153,.15)}
.img{position:sticky;top:110px;align-self:start}
.img img{width:100%;display:block;border:1px solid var(--line);border-radius:4px}
.meta{font-size:13px;color:var(--muted);margin-bottom:16px}
h2{font-size:21px;margin:2px 0 8px;color:var(--text)}
h2 .dot{color:var(--accent)}
.band{display:inline-block;background:var(--band);color:#fff;font-weight:bold;font-size:15px;padding:4px 12px;border-radius:4px;margin-bottom:10px}
/* 原稿はスライドの本文（20pt）より少し小さく、墨色でスライドの文字と見分ける（フォントはゴシックのまま。明朝はユーザーの好みでなかった）。
   スライド画像の幅は画面幅に比例するので、文字も vw で追従させる（画像列≈画面の62%、20pt≈スライド幅の2.1% ⇒ 本文≈1.3vw） */
.notes{color:var(--ink)}
.notes p{margin:0 0 .7em;font-size:clamp(13px,1.0vw,18px);line-height:1.9}
.notes p.extra{color:var(--extra);font-size:.88em}
.notes p.fig{color:var(--extra);font-size:.88em}
.notes p.check{color:var(--check)}
.notes .tag{font-size:12px;border:1px solid currentColor;border-radius:3px;padding:0 4px;margin-right:6px;white-space:nowrap}
.notes p.empty{color:var(--muted)}
.notes p.aside{font-family:"BIZ UDPGothic","Yu Gothic UI","Meiryo",sans-serif;color:var(--extra);font-size:clamp(12px,.82vw,14.5px);line-height:1.7;border-left:3px solid var(--line);padding-left:10px;margin-top:.9em}
.notes p.aside.check{color:var(--check);border-left-color:#f3c48b}
.help{font-size:12px;color:var(--muted);margin-left:auto}
/* ---- コメント機能 ---- */
:root{--cm:#c2410c;--cmbg:#fff1d6}
.navrow{display:flex;align-items:flex-start;gap:12px;margin-top:6px}
.navrow nav{flex:1;margin-top:0}
.tools{display:flex;gap:6px;flex-shrink:0}
.tools button,.cm-pop button,.cm-panel button{font:inherit;font-size:12px;line-height:1.6;padding:2px 10px;border:1px solid #cfd6e0;border-radius:4px;background:#fff;color:var(--text);cursor:pointer}
.tools button:hover,.cm-pop button:hover,.cm-panel button:hover{border-color:var(--band)}
.tools button.on{background:var(--cm);border-color:var(--cm);color:#fff}
.tools kbd{font-family:inherit;font-size:11px;opacity:.75;margin-left:4px}
.cm-banner{display:none;margin-top:6px;font-size:12px;color:var(--cm);background:var(--cmbg);border-radius:4px;padding:3px 10px}
body.cm-on .cm-banner{display:block}
body.cm-on section{border-color:#f0c99a}
.shot{position:relative;user-select:none}
body.cm-on .shot{cursor:crosshair}
.cm-layer{position:absolute;inset:0}
.cm-rect{position:absolute;border:2px solid var(--cm);background:rgba(194,65,12,.07);border-radius:2px;cursor:pointer}
.cm-rect.tmp{border-style:dashed;pointer-events:none}
.cm-rect::after{content:attr(data-n);position:absolute;top:-11px;left:-11px;min-width:20px;height:20px;padding:0 5px;border-radius:10px;background:var(--cm);color:#fff;font-size:11px;line-height:20px;text-align:center}
.cm-rect.tmp::after{content:none}
mark.cm-hl{background:var(--cmbg);color:inherit;border-bottom:2px solid #f59e0b;cursor:pointer;padding:0}
mark.cm-hl.last::after{content:attr(data-n);font-size:10px;font-weight:bold;vertical-align:super;color:var(--cm);margin-left:1px}
mark.cm-hl.flash,.cm-rect.flash{outline:3px solid #f59e0b;outline-offset:1px}
body.cm-on .notes{cursor:text}
.cm-pop{position:fixed;z-index:30;width:340px;max-width:92vw;background:#fff;border:1px solid #d0d7e2;border-radius:8px;box-shadow:0 8px 28px rgba(0,0,0,.18);padding:10px 12px;display:none}
.cm-pop.open{display:block}
.cm-pop .k{font-size:12px;color:var(--muted);margin-bottom:4px}
.cm-pop .q{font-size:12px;color:#7c5a1a;background:var(--cmbg);border-radius:4px;padding:3px 6px;max-height:4.8em;overflow:auto;margin-bottom:6px}
.cm-pop textarea{width:100%;min-height:84px;font:inherit;font-size:14px;line-height:1.6;border:1px solid #cfd6e0;border-radius:4px;padding:6px 8px;resize:vertical}
.cm-pop .row{display:flex;gap:6px;justify-content:flex-end;align-items:center;margin-top:6px}
.cm-pop .row .del{margin-right:auto;color:#b91c1c}
.cm-pop .hint{font-size:11px;color:var(--muted);margin-right:auto}
.cm-panel{position:fixed;top:0;right:0;bottom:0;width:min(400px,92vw);z-index:25;background:#fff;border-left:1px solid var(--line);box-shadow:-6px 0 20px rgba(0,0,0,.08);transform:translateX(105%);transition:transform .18s;display:flex;flex-direction:column}
.cm-panel.open{transform:none}
.cm-panel .hd{padding:10px 14px;border-bottom:1px solid var(--line)}
.cm-panel .hd b{color:var(--band)}
.cm-panel .hd .row{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
.cm-panel .hd .x{float:right}
.cm-panel .list{overflow:auto;padding:10px 14px;flex:1}
.cm-panel .note{font-size:12px;color:var(--muted);margin:0 0 8px}
.cm-item{border:1px solid var(--line);border-radius:6px;padding:8px 10px;margin-bottom:8px;font-size:13px;line-height:1.6;cursor:pointer}
.cm-item:hover{border-color:var(--band)}
.cm-item .k{font-size:12px;color:var(--muted)}
.cm-item .k b{color:var(--cm)}
.cm-item .q{font-size:12px;color:#7c5a1a;margin:2px 0}
.cm-item .lost{color:#b91c1c;font-size:12px}
.cm-item .t{white-space:pre-wrap;color:var(--ink)}
.cm-toast{position:fixed;right:16px;bottom:16px;z-index:40;max-width:min(460px,92vw);background:#1f2a36;color:#fff;font-size:13px;line-height:1.6;padding:8px 14px;border-radius:6px;box-shadow:0 6px 20px rgba(0,0,0,.2);opacity:0;transform:translateY(8px);transition:.2s;pointer-events:none}
.cm-toast.open{opacity:1;transform:none}
/* 確認問題に答える欄 */
.qa{margin-top:18px;border-top:1px dashed var(--line);padding-top:12px}
.qa-h{font-size:13px;color:var(--band);font-weight:bold;margin-bottom:8px}
.qa-row{margin-bottom:10px}
.qa-btn{font:inherit;font-size:13px;padding:3px 12px;border:1px solid var(--band);border-radius:4px;background:#fff;color:var(--band);cursor:pointer}
.qa-btn:hover{background:#eef4fb}
.qa-btn.done{border-color:#cfd6e0;color:var(--muted)}
.qa-ans{white-space:pre-wrap;font-size:14px;line-height:1.7;color:var(--ink);background:#f3f8f1;border-left:3px solid #6aa84f;border-radius:3px;padding:4px 10px;margin-top:5px}
.qa-ans:empty{display:none}
@media (max-width:900px){section{grid-template-columns:1fr}.img{position:static}.notes p{font-size:15px}main{padding:12px 12px 40vh}header{padding:8px 12px}}
@media print{header{position:static}nav,.help,.tools,.cm-banner,.cm-pop,.cm-panel,.cm-layer,.qa-btn{display:none}mark.cm-hl{background:none;border:none}mark.cm-hl.last::after{content:none}main{padding:0}section{break-inside:avoid;break-after:page;border:none;box-shadow:none;grid-template-columns:1fr;gap:10px}.img{position:static}.img img{max-height:45vh;width:auto;margin:0 auto}body{background:#fff}}
"""

JS = r"""
const secs=[...document.querySelectorAll('section')],links=[...document.querySelectorAll('nav a')];
let cur=0;
function mark(i){cur=i;secs.forEach((s,k)=>s.classList.toggle('cur',k===i));links.forEach((a,k)=>a.classList.toggle('on',k===i));}
function go(i){i=Math.max(0,Math.min(secs.length-1,i));secs[i].scrollIntoView({block:'start'});mark(i);history.replaceState(null,'','#s'+(i+1));}
const tgt=e=>e.target instanceof Element?e.target:document.body;
document.addEventListener('keydown',e=>{if(tgt(e).closest('input,textarea')||e.ctrlKey||e.metaKey||e.altKey)return;
 if(['ArrowRight','ArrowDown','j','PageDown',' '].includes(e.key)){e.preventDefault();go(cur+1);}
 if(['ArrowLeft','ArrowUp','k','PageUp'].includes(e.key)){e.preventDefault();go(cur-1);}});
const io=new IntersectionObserver(es=>{es.forEach(en=>{if(en.isIntersecting&&en.intersectionRatio>.5)mark(secs.indexOf(en.target));});},{threshold:[.5]});
secs.forEach(s=>io.observe(s));
const h=location.hash.match(/^#s(\d+)$/);if(h)go(+h[1]-1);else mark(0);

/* ================= コメント機能 =================
   文章：コメントモードで原稿の文章を選ぶ → その範囲にコメント（引用＋前後の文脈＋文字位置で記録）
   スライド：コメントモードでスライド画像をドラッグ → 囲んだ範囲にコメント（画像に対する 0〜1 の割合で記録）
   保存はこのブラウザの localStorage。「一覧」→「書き出し」で JSON にして AI に渡す */
const KEY='zemi-comments:'+document.title;
const $=s=>document.querySelector(s);
let C=[],on=false,drag=null,pop=null;
function load(){try{C=JSON.parse(localStorage.getItem(KEY)||'[]')}catch(e){C=[]}}
function save(){try{localStorage.setItem(KEY,JSON.stringify(C))}catch(e){alert('ブラウザに保存できませんでした。「書き出し」でファイルに残してください。')}}
function nextN(){return C.reduce((m,c)=>Math.max(m,c.n),0)+1}
function uid(){return 'c'+Date.now().toString(36)+Math.random().toString(36).slice(2,6)}
function esc(s){return String(s).replace(/[&<>"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]))}
function notesOf(i){return secs[i].querySelector('.notes')}
function shotOf(i){return secs[i].querySelector('.shot')}
function setMode(v){on=v;document.body.classList.toggle('cm-on',on);$('#cm-mode').classList.toggle('on',on);if(!on)closePop();}

/* ---- 文章の範囲 <-> 文字位置 ---- */
function offset(root,node,off){const r=document.createRange();r.setStart(root,0);r.setEnd(node,off);return r.toString().length}
function locate(root,c){
  const T=root.textContent;
  if(T.slice(c.start,c.end)===c.quote)return [c.start,c.end];
  let best=null,score=-1,i=T.indexOf(c.quote);
  while(i>=0){
    const pre=T.slice(Math.max(0,i-c.prefix.length),i),suf=T.slice(i+c.quote.length,i+c.quote.length+c.suffix.length);
    let s=0;for(let k=1;k<=Math.min(pre.length,c.prefix.length)&&pre[pre.length-k]===c.prefix[c.prefix.length-k];k++)s++;
    for(let k=0;k<Math.min(suf.length,c.suffix.length)&&suf[k]===c.suffix[k];k++)s++;
    s-=Math.abs(i-c.start)/1e6;
    if(s>score){score=s;best=[i,i+c.quote.length]}
    i=T.indexOf(c.quote,i+1);
  }
  return best;
}
function wrap(root,a,b,c){
  const tw=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let pos=0,n,parts=[];
  while((n=tw.nextNode())){const L=n.nodeValue.length,s=Math.max(a,pos),e=Math.min(b,pos+L);
    if(s<e&&n.nodeValue.slice(s-pos,e-pos).trim())parts.push([n,s-pos,e-pos]);pos+=L;if(pos>=b)break;}
  parts.forEach(([n,x,y],k)=>{let t=n;if(x>0)t=t.splitText(x);if(y-x<t.nodeValue.length)t.splitText(y-x);
    const m=document.createElement('mark');m.className='cm-hl'+(k===parts.length-1?' last':'');
    m.dataset.id=c.id;m.dataset.n=c.n;m.title='#'+c.n+' '+c.comment;t.parentNode.insertBefore(m,t);m.appendChild(t);});
}
function render(){
  document.querySelectorAll('mark.cm-hl').forEach(m=>m.replaceWith(...m.childNodes));
  secs.forEach(s=>{const r=s.querySelector('.notes');if(r)r.normalize();const l=s.querySelector('.cm-layer');if(l)l.innerHTML='';});
  [...C].sort((p,q)=>p.n-q.n).forEach(c=>{
    const i=c.slide-1;if(!secs[i]||c.kind==='answer')return;
    if(c.kind==='text'){const root=notesOf(i),pos=locate(root,c);c.lost=!pos;if(pos)wrap(root,pos[0],pos[1],c);}
    else{const d=document.createElement('div');d.className='cm-rect';d.dataset.id=c.id;d.dataset.n=c.n;d.title='#'+c.n+' '+c.comment;
      const [x,y,w,hh]=c.rect;Object.assign(d.style,{left:x*100+'%',top:y*100+'%',width:w*100+'%',height:hh*100+'%'});
      shotOf(i).querySelector('.cm-layer').appendChild(d);}
  });
  $('#cm-count').textContent=C.length;renderList();renderAnswers();
}
function kindLabel(c){return c.kind==='text'?'原稿':c.kind==='answer'?c.q+' への答え':'スライドの範囲'}
function renderAnswers(){document.querySelectorAll('.qa-row').forEach(r=>{
  const c=C.find(c=>c.kind==='answer'&&c.q===r.dataset.q),b=r.querySelector('.qa-btn');
  r.querySelector('.qa-ans').textContent=c?c.comment:'';b.textContent=c?r.dataset.q+' の答えを直す':r.dataset.q+' に答える';b.classList.toggle('done',!!c);});}

/* ---- 入力欄（新規・編集） ---- */
function openPop(x,y,opt){
  pop=opt;const el=$('#cm-pop');
  el.querySelector('.k').textContent=opt.label;
  const q=el.querySelector('.q');q.style.display=opt.quote?'block':'none';q.textContent=opt.quote||'';
  const ta=el.querySelector('textarea');ta.value=opt.text||'';
  el.querySelector('.del').style.display=opt.id?'inline-block':'none';
  el.classList.add('open');
  const W=el.offsetWidth,H=el.offsetHeight;
  el.style.left=Math.max(8,Math.min(innerWidth-W-8,x))+'px';el.style.top=Math.max(8,Math.min(innerHeight-H-8,y))+'px';
  setTimeout(()=>ta.focus(),0);
}
function closePop(){const el=$('#cm-pop');el.classList.remove('open');if(pop&&pop.tmp)pop.tmp.remove();pop=null;}
function commitPop(){
  if(!pop)return;const t=$('#cm-pop textarea').value.trim();
  if(!t){if(pop.id)delC(pop.id);closePop();return;}
  if(pop.id){const c=C.find(c=>c.id===pop.id);c.comment=t;c.updated=new Date().toISOString();}
  else{const c=Object.assign({id:uid(),n:nextN(),comment:t,created:new Date().toISOString()},pop.data);C.push(c);}
  save();closePop();render();
}
function delC(id){C=C.filter(c=>c.id!==id);save();render();}
function editC(id,x,y){const c=C.find(c=>c.id===id);if(!c)return;
  openPop(x,y,{id,text:c.comment,quote:c.kind==='text'?c.quote:'',label:'#'+c.n+'　スライド '+c.slide+'・'+kindLabel(c)});}

/* ---- 文章を選んでコメント ---- */
document.addEventListener('mouseup',e=>{
  if(drag){endDrag(e);return;}
  if(!on||tgt(e).closest('#cm-pop,.cm-panel,header'))return;
  setTimeout(()=>{
    const sel=getSelection();if(!sel.rangeCount||sel.isCollapsed)return;
    const r=sel.getRangeAt(0),sec=(r.startContainer.nodeType===1?r.startContainer:r.startContainer.parentNode).closest('section');
    if(!sec)return;const root=sec.querySelector('.notes');if(!root.contains(r.startContainer))return;
    let a=offset(root,r.startContainer,r.startOffset),b=root.contains(r.endContainer)?offset(root,r.endContainer,r.endOffset):root.textContent.length;
    const T=root.textContent;while(a<b&&/\s/.test(T[a]))a++;while(b>a&&/\s/.test(T[b-1]))b--;
    if(b-a<1)return;
    const quote=T.slice(a,b),i=secs.indexOf(sec),box=r.getBoundingClientRect();
    sel.removeAllRanges();
    openPop(box.left,box.bottom+8,{label:'スライド '+(i+1)+'・原稿へのコメント',quote,
      data:{slide:i+1,kind:'text',quote,start:a,end:b,prefix:T.slice(Math.max(0,a-40),a),suffix:T.slice(b,b+40)}});
  },0);
});

/* ---- スライドをドラッグで囲んでコメント ---- */
document.addEventListener('mousedown',e=>{
  if(!on||e.button!==0)return;const shot=tgt(e).closest('.shot');if(!shot||tgt(e).closest('.cm-rect'))return;
  e.preventDefault();closePop();
  const b=shot.getBoundingClientRect(),tmp=document.createElement('div');tmp.className='cm-rect tmp';
  shot.querySelector('.cm-layer').appendChild(tmp);
  drag={shot,b,x0:(e.clientX-b.left)/b.width,y0:(e.clientY-b.top)/b.height,tmp};moveDrag(e);
});
function clamp(v){return Math.max(0,Math.min(1,v))}
function dragRect(e){const d=drag,x1=clamp((e.clientX-d.b.left)/d.b.width),y1=clamp((e.clientY-d.b.top)/d.b.height);
  return [Math.min(d.x0,x1),Math.min(d.y0,y1),Math.abs(x1-d.x0),Math.abs(y1-d.y0)]}
function moveDrag(e){const [x,y,w,hh]=dragRect(e);Object.assign(drag.tmp.style,{left:x*100+'%',top:y*100+'%',width:w*100+'%',height:hh*100+'%'});}
document.addEventListener('mousemove',e=>{if(drag)moveDrag(e)});
function endDrag(e){
  let [x,y,w,hh]=dragRect(e);const d=drag;drag=null;
  if(w*d.b.width<8&&hh*d.b.height<8){w=.04;hh=.06;x=clamp(d.x0-w/2);y=clamp(d.y0-hh/2);}  // クリックだけなら小さな枠
  const rect=[x,y,w,hh].map(v=>Math.round(v*1000)/1000),i=secs.indexOf(d.shot.closest('section'));
  Object.assign(d.tmp.style,{left:x*100+'%',top:y*100+'%',width:w*100+'%',height:hh*100+'%'});
  openPop(e.clientX+12,e.clientY+12,{label:'スライド '+(i+1)+'・スライドの範囲へのコメント',tmp:d.tmp,data:{slide:i+1,kind:'region',rect}});
}

/* ---- 既存のコメントを開く ---- */
document.addEventListener('click',e=>{
  const t=tgt(e).closest('mark.cm-hl,.cm-rect:not(.tmp)');if(!t||(on&&!getSelection().isCollapsed))return;
  editC(t.dataset.id,e.clientX+12,e.clientY+12);
});

/* ---- 一覧・書き出し・読み込み ---- */
function renderList(){
  const L=$('#cm-list');
  if(!C.length){L.innerHTML='<p class="note">まだコメントはありません。「コメント」ボタン（C キー）でコメントモードにして、原稿の文章を選ぶか、スライドをドラッグで囲んでください。</p>';return;}
  L.innerHTML=[...C].sort((p,q)=>p.slide-q.slide||p.n-q.n).map(c=>`<div class="cm-item" data-id="${c.id}">
   <div class="k"><b>#${c.n}</b>　スライド ${c.slide}・${kindLabel(c)}</div>
   ${c.kind!=='region'?`<div class="q">「${esc(c.quote.length>60?c.quote.slice(0,60)+'…':c.quote)}」</div>`:''}
   ${c.lost?'<div class="lost">原稿が変わって、選んだ文章が見つかりません</div>':''}
   <div class="t">${esc(c.comment)}</div></div>`).join('');
}
$('#cm-list').addEventListener('click',e=>{const it=e.target.closest('.cm-item');if(!it)return;
  const c=C.find(c=>c.id===it.dataset.id);go(c.slide-1);
  setTimeout(()=>document.querySelectorAll(`[data-id="${c.id}"]`).forEach(el=>{if(el.classList.contains('cm-item'))return;
    el.classList.add('flash');el.scrollIntoView({block:'center'});setTimeout(()=>el.classList.remove('flash'),1600);}),350);});
function exportData(){return{format:'zemi-comments',version:1,deck:document.title.replace(/ 原稿$/,''),
  html:decodeURIComponent(location.pathname),save_dir:document.body.dataset.savePath||'',course_id:document.body.dataset.courseId||'',
  slides:secs.length,exported:new Date().toISOString(),
  comments:[...C].sort((p,q)=>p.slide-q.slide||p.n-q.n).map(({lost,...c})=>c)}}
function asText(){const d=exportData();let s=`# コメント：${d.deck}（${d.comments.length}件）\n`,last=0;
  d.comments.forEach(c=>{if(c.slide!==last){s+=`\n## スライド ${c.slide}\n`;last=c.slide;}
    s+=c.kind==='answer'?`- #${c.n} ${c.q} への答え（問題：${c.quote}）\n  → ${c.comment.replace(/\n/g,'\n    ')}\n`
      :c.kind==='text'?`- #${c.n} 原稿「${c.quote}」\n  → ${c.comment.replace(/\n/g,'\n    ')}\n`
      :`- #${c.n} スライドの範囲（左${Math.round(c.rect[0]*100)}%・上${Math.round(c.rect[1]*100)}%・幅${Math.round(c.rect[2]*100)}%・高さ${Math.round(c.rect[3]*100)}%）\n  → ${c.comment.replace(/\n/g,'\n    ')}\n`;});
  return s;}
/* 書き出すファイル名：README の講座IDを頭に付ける（01_生成AIは何をしているか → AI01_生成AIは何をしているか_コメント.json） */
function exportName(){const b=fileBase(),id=document.body.dataset.courseId||'';
  return (id?(/^\d/.test(b)?id+b:id+'_'+b):b)+'_コメント.json'}
function fileBase(){const f=decodeURIComponent(location.pathname.split('/').pop()||'');return f.replace(/_原稿\.html$/,'').replace(/\.html$/,'')||document.title.replace(/ 原稿$/,'')}
/* 書き出し：保存先は資料フォルダの README（00_README.md の「書き出しの保存先」）で決まり、JSON に save_dir として入る。
   ブラウザはページから任意のフォルダへ書けないので、ふだんは何も聞かずにダウンロードフォルダへ保存し、
   AI が comments_read.py --find で読むときに save_dir へ移す（ユーザーにフォルダを選ばせない）。
   一覧の「保存先フォルダを登録」で一度フォルダを許可しておけば（任意・全デッキ共通）、以後はそこへ直接保存する */
const SAVE_NAME=document.body.dataset.saveName||'',SAVE_PATH=document.body.dataset.savePath||'';
function idb(){return new Promise((ok,ng)=>{const r=indexedDB.open('zemi-comments',1);r.onupgradeneeded=()=>r.result.createObjectStore('kv');r.onsuccess=()=>ok(r.result);r.onerror=()=>ng(r.error);})}
async function kv(k,v){const db=await idb();return new Promise((ok,ng)=>{const t=db.transaction('kv',v===undefined?'readonly':'readwrite'),s=t.objectStore('kv');
  const r=v===undefined?s.get(k):v===null?s.delete(k):s.put(v,k);r.onsuccess=()=>ok(r.result);r.onerror=()=>ng(r.error);})}
const DIRKEY='dir:'+(SAVE_PATH||'default');
function toast(s){const t=$('#cm-toast');t.textContent=s;t.classList.add('open');clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('open'),6000);$('#cm-msg').textContent=s;}
async function grantedDir(){   // 登録済みで、いま許可が出ているフォルダだけ返す（確認の画面は出さない）
  try{const h=await kv(DIRKEY);if(h&&await h.queryPermission({mode:'readwrite'})==='granted')return h;}catch(e){}
  return null;
}
async function registerDir(){
  if(!window.showDirectoryPicker){toast('このブラウザでは登録できません。書き出しはダウンロードフォルダに保存されます');return;}
  try{const h=await showDirectoryPicker({id:'zemi-comments',mode:'readwrite'});
    if(SAVE_NAME&&h.name!==SAVE_NAME&&!confirm('「'+h.name+'」が選ばれました。README の保存先は「'+SAVE_NAME+'」です。\nこのフォルダを登録しますか？'))return;
    await kv(DIRKEY,h);toast('「'+h.name+'」を保存先に登録しました（同じ保存先のデッキ全部で使います）');}
  catch(e){if(e.name!=='AbortError')toast('登録できませんでした: '+e.message);}
}
async function doExport(){
  if(!C.length){toast('コメントがありません');return;}
  const name=exportName(),body=JSON.stringify(exportData(),null,1),d=await grantedDir();
  if(d){try{const fh=await d.getFileHandle(name,{create:true}),w=await fh.createWritable();await w.write(body);await w.close();
      toast('「'+d.name+'」に '+name+' を保存しました（'+C.length+'件）。AI に「コメントした」と伝えてください。');return;}
    catch(e){console.warn(e);}}
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([body],{type:'application/json'}));
  a.download=name;document.body.appendChild(a);a.click();a.remove();
  toast('「'+name+'」を保存しました（'+C.length+'件、ダウンロードフォルダ）。AI に「コメントした」と伝えれば、'
    +(SAVE_NAME?'README の保存先「'+SAVE_NAME+'」へ移してから読みます。':'そこから読みます。'));
}
$('#cm-export').onclick=doExport;
$('#cm-export2').onclick=doExport;
$('#cm-where').onclick=registerDir;
$('#cm-copy').onclick=async()=>{const s=asText();
  try{await navigator.clipboard.writeText(s)}catch(e){const t=document.createElement('textarea');t.value=s;document.body.appendChild(t);t.select();document.execCommand('copy');t.remove();}
  $('#cm-msg').textContent='コメントを文章でコピーしました（チャットに貼り付けられます）。';};
$('#cm-import').onclick=()=>$('#cm-file').click();
$('#cm-file').onchange=async e=>{const f=e.target.files[0];if(!f)return;
  try{const d=JSON.parse(await f.text());let k=0;(d.comments||[]).forEach(c=>{if(C.some(x=>x.id===c.id))return;
    if(C.some(x=>x.n===c.n))c.n=nextN();C.push(c);k++;});save();render();$('#cm-msg').textContent=k+'件を読み込みました。';}
  catch(err){alert('読み込めませんでした: '+err.message)}e.target.value='';};
$('#cm-clear').onclick=()=>{if(C.length&&confirm('このページのコメント '+C.length+' 件を全部消します。先に「書き出し」で保存しましたか？')){C=[];save();render();}};
/* ---- 確認問題に答える（コメントモードでなくても使える） ---- */
document.addEventListener('click',e=>{const b=tgt(e).closest('.qa-btn');if(!b)return;
  const r=b.closest('.qa-row'),i=secs.indexOf(b.closest('section')),c=C.find(c=>c.kind==='answer'&&c.q===r.dataset.q),bb=b.getBoundingClientRect();
  openPop(bb.left,bb.bottom+6,{id:c&&c.id,text:c?c.comment:'',quote:r.dataset.text,label:r.dataset.q+' への答え（スライド '+(i+1)+'）',
    data:{slide:i+1,kind:'answer',q:r.dataset.q,quote:r.dataset.text}});});
$('#cm-mode').onclick=()=>setMode(!on);
$('#cm-open').onclick=()=>$('#cm-panel').classList.toggle('open');
$('#cm-close').onclick=()=>$('#cm-panel').classList.remove('open');
$('#cm-pop .ok').onclick=commitPop;$('#cm-pop .cancel').onclick=closePop;
$('#cm-pop .del').onclick=()=>{if(pop&&pop.id&&confirm('このコメントを消しますか？')){delC(pop.id);closePop();}};
document.addEventListener('keydown',e=>{
  if(tgt(e).closest('#cm-pop')){if(e.key==='Escape'){e.preventDefault();closePop();}
    if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();commitPop();}return;}
  if(tgt(e).closest('input,textarea')||e.ctrlKey||e.metaKey||e.altKey)return;
  if(e.key==='c'||e.key==='C'){e.preventDefault();setMode(!on);}
  if(e.key==='l'||e.key==='L'){e.preventDefault();$('#cm-panel').classList.toggle('open');}
  if(e.key==='Escape'){if(pop)closePop();else if($('#cm-panel').classList.contains('open'))$('#cm-panel').classList.remove('open');else if(on)setMode(false);}
});
load();render();
"""


def qa_block(qs):
    """確認問題のスライドの原稿の下に置く「1-1 に答える」ボタン（答えはコメントとして保存・書き出し）"""
    if not qs:
        return ""
    rows = "".join(f'<div class="qa-row" data-q="{html.escape(q)}" data-text="{html.escape(t)}">'
                   f'<button class="qa-btn">{html.escape(q)} に答える</button><div class="qa-ans"></div></div>' for q, t in qs)
    return f'<div class="qa"><div class="qa-h">あなたの答え（書き出すと、まとめて添削します）</div>{rows}</div>'


SAVE_RE = re.compile(r"書き出し(?:の)?保存先\s*[:：]\s*(.+)")
CID_RE = re.compile(r"講座\s*ID\s*[:：]\s*([A-Za-z][A-Za-z0-9]*)")


def memo_lines(path):
    """資料フォルダのメモ（00_README.md など）の行"""
    folder = path.resolve().parent
    memos = sorted(folder.glob("00_*.md")) + sorted(folder.glob("*README*.md")) + sorted(folder.glob("*メモ*.md"))
    for memo in dict.fromkeys(memos):
        yield from memo.read_text(encoding="utf-8", errors="ignore").splitlines()


def save_setting(pptx):
    """資料フォルダの README の「書き出しの保存先: …」を読む。戻り値 (フォルダ名, パス) か None。
    値が「このフォルダ」で始まればメモのあるフォルダ、それ以外はパス（相対ならメモのフォルダから）"""
    folder = pptx.resolve().parent
    for line in memo_lines(pptx):
        m = SAVE_RE.search(line)
        if m:
            v = m.group(1).strip().strip("`")
            p = folder if v.startswith("このフォルダ") else (folder / v).resolve()
            return p.name, str(p)
    return None


def course_id(pptx):
    """README の「講座ID: GA」を読む。書き出すコメントのファイル名の頭に付け（GA01_…_コメント.json）、
    同じIDのコメントだけをまとめて保存先へ移すのに使う。なければ空文字"""
    for line in memo_lines(pptx):
        m = CID_RE.search(line)
        if m:
            return m.group(1)
    return ""


def build_html(deck_title, items, imgs, qs=None, save=None, cid=""):
    n = len(items)
    save_name, save_path = save or ("", "")
    save_title = f"（保存先：{save_name}）" if save_name else ""
    qs = qs or [[] for _ in items]
    nav = "".join(f'<a href="#s{i+1}">{i+1}</a>' for i in range(n))
    secs = []
    for i, ((title, heading, band, notes), img) in enumerate(zip(items, imgs)):
        # ●見出しと青帯は左のスライド画像に見えているので、原稿側には出さない
        secs.append(f"""<section id="s{i+1}">
<div class="img"><div class="shot"><img src="data:image/jpeg;base64,{img}" alt="スライド {i+1}" draggable="false"><div class="cm-layer"></div></div></div>
<div><div class="meta">スライド {i+1} / {n}</div><div class="notes">{format_notes(notes)}</div>{qa_block(qs[i] if i < len(qs) else [])}</div>
</section>""")
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="generator" content="sensei-slides notes_html.py">
<title>{html.escape(deck_title)} 原稿</title><style>{CSS}</style></head>
<body data-save-name="{html.escape(save_name)}" data-save-path="{html.escape(save_path)}" data-course-id="{html.escape(cid)}"><header><div style="display:flex;align-items:baseline"><h1>{html.escape(deck_title)}<span class="sub">原稿（発表者ノート）・全{n}枚</span></h1>
<span class="help">← → / j k で移動、C でコメント、印刷でPDF</span></div>
<div class="navrow"><nav>{nav}</nav><div class="tools">
<button id="cm-mode" title="コメントモードの切り替え（C キー）">コメント<kbd>C</kbd></button>
<button id="cm-export2" title="コメントと答えをファイルに書き出す{save_title}">書き出し</button>
<button id="cm-open" title="コメント一覧・書き出し（L キー）">一覧 <span id="cm-count">0</span></button></div></div>
<div class="cm-banner">コメントモード：原稿の文章を選ぶとその部分に、スライドはドラッグで範囲を囲むとそこにコメントできます（C か Esc で終了）</div></header>
<main>{''.join(secs)}</main>
<div id="cm-pop" class="cm-pop"><div class="k"></div><div class="q"></div><textarea placeholder="疑問点・コメント"></textarea>
<div class="row"><button class="del">削除</button><span class="hint">Ctrl+Enter で保存</span><button class="cancel">取消</button><button class="ok">保存</button></div></div>
<aside id="cm-panel" class="cm-panel"><div class="hd"><button id="cm-close" class="x">閉じる</button><b>コメント一覧</b>
<div class="row"><button id="cm-export" title="JSON ファイルに書き出す（AI に渡す用）">書き出し</button><button id="cm-where" title="任意：一度フォルダを許可すると、以後はダウンロードを通さず直接そこへ保存する">保存先フォルダを登録</button><button id="cm-copy">文章でコピー</button>
<button id="cm-import">読み込み</button><button id="cm-clear">全部消す</button><input id="cm-file" type="file" accept=".json,application/json" hidden></div>
<p class="note" id="cm-msg" style="margin:6px 0 0">コメントはこのブラウザに自動で保存されます。全部書いたら「書き出し」で AI に渡します。</p></div>
<div class="list" id="cm-list"></div></aside>
<div id="cm-toast" class="cm-toast"></div>
<script>{JS}</script></body></html>"""


def export_temp_pdf(pptx, tmpdir):
    """一時フォルダに PDF を書き出す（ユーザーのフォルダには PDF を残さない）。
    Windows では PowerPoint 本体で。PowerPoint が無い・開けないときは LibreOffice で（render_check_lo.py）。"""
    import platform
    import shutil
    import subprocess
    pdf = Path(tmpdir) / "slides.pdf"
    msg = ""
    if platform.system() == "Windows" and shutil.which("powershell"):
        ps1 = Path(__file__).resolve().parent / "export_pdf.ps1"
        r = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1), "-Pptx", str(pptx.resolve()),
                            "-Pdf", str(pdf)], capture_output=True, text=True, errors="replace")
        if pdf.exists():
            return pdf
        msg = f"PowerPoint で PDF に書き出せない:\n{r.stdout}\n{r.stderr}\n"
    try:
        import render_check_lo
        render_check_lo.export_pdf(pptx, pdf)
        print("スライド画像は LibreOffice で書き出した（PowerPoint が無い・開けないため）")
        return pdf
    except SystemExit as e:
        sys.exit(f"スライド画像を作れませんでした。{msg}LibreOffice でも書き出せない：{e}")


def main():
    import tempfile
    import pymupdf as fitz
    fitz.TOOLS.mupdf_display_errors(False)   # LibreOffice の PDF の構造ツリーの警告（無害）を出さない
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--pdf", help="スライドのPDF（省略時は PowerPoint で一時フォルダに書き出して使い、終わったら消す）")
    ap.add_argument("-o", "--out", help="出力HTML（省略時は <資料名>_原稿.html）")
    a = ap.parse_args()
    pptx = Path(a.pptx)
    stem = pptx.stem[:-len("_スライド")] if pptx.stem.endswith("_スライド") else pptx.stem
    out = Path(a.out) if a.out else pptx.with_name(f"{stem}_原稿.html")
    prs = Presentation(str(pptx))
    items = slide_texts(prs)
    if a.pdf:
        imgs = slide_images(Path(a.pdf))
    else:
        with tempfile.TemporaryDirectory() as td:
            imgs = slide_images(export_temp_pdf(pptx, td))
    if len(imgs) != len(items):
        print(f"注意: スライド {len(items)} 枚に対し画像 {len(imgs)} 枚。--pdf で渡した PDF が古い可能性あり")
    deck_title = prs.core_properties.title or items[0][0] or stem
    save, cid = save_setting(pptx), course_id(pptx)
    out.write_text(build_html(deck_title, items, imgs, slide_questions(prs), save, cid), encoding="utf-8")
    if save:
        print(f"コメントの保存先（README の指定）: {save[1]}" + (f"　講座ID: {cid}" if cid else ""))
    print(f"saved {out} ({len(items)} slides, {out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):   # パイプで走らせると日本語の Windows では cp932 になり、✔ や珍しい字で落ちる
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    main()
