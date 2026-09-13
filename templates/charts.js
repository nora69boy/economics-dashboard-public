/* Reviewed local snapshots only; no network, storage, forms or trade execution. */
(()=>{
'use strict';
const D=JSON.parse(document.getElementById('market-data').textContent),$=id=>document.getElementById(id);
const C=['#69dec8','#94b8ff','#f4c97c','#e4ace0','#bbabff','#a7d68a'];
const S={index:'SPX',region:'all',normal:false,stock:'NVDA',candle:true,n:6,ma:true};
const pct=x=>(x>=0?'+':'')+x.toFixed(2)+'%',num=x=>x.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const change=r=>(r.at(-1).close/r[0].close-1)*100;
function dd(r){let peak=r[0].close,w=0;for(const x of r){peak=Math.max(peak,x.close);w=Math.min(w,(x.close/peak-1)*100);}return w;}
function average(r){return r.map((_,i)=>i<4?null:r.slice(i-4,i+1).reduce((s,x)=>s+x.close,0)/5);}
function graph(id,series,labels,{bars=false,candles=null,unit='',zero=false}={}){
 const el=$(id);if(el.closest('.panel').hidden)return;
 const w=Math.max(250,el.parentElement.clientWidth-24),h=280,dpr=Math.min(devicePixelRatio||1,3);
 el.width=w*dpr;el.height=h*dpr;el.style.height=h+'px';const c=el.getContext('2d');c.scale(dpr,dpr);
 const values=series.flatMap(s=>s.values.filter(x=>x!==null));if(candles)values.push(...candles.flatMap(r=>[r.high,r.low]));
 let lo=zero?0:Math.min(...values),hi=Math.max(...values),gap=(hi-lo)||Math.max(1,hi*.02);if(!zero)lo-=gap*.12;hi+=gap*.12;
 const left=61,right=w-24,top=25,bottom=h-38,x=i=>left+i*(right-left)/Math.max(1,labels.length-1),y=v=>bottom-(v-lo)/(hi-lo)*(bottom-top);
 c.fillStyle='#bcd0e0';c.font='11px sans-serif';c.fillText(unit,8,13);
 for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4,yy=y(v);c.strokeStyle='#2e465e';c.lineWidth=1;c.beginPath();c.moveTo(left,yy);c.lineTo(right,yy);c.stroke();c.textAlign='right';c.fillText(Math.abs(v)>=1e6?(v/1e6).toFixed(1)+'m':Math.abs(v)>=10000?(v/1000).toFixed(1)+'k':v.toFixed(1),left-7,yy+4);}
 c.textAlign='center';labels.forEach((l,i)=>c.fillText(l,x(i),bottom+22));
 series.forEach((s,j)=>{c.strokeStyle=c.fillStyle=C[j%C.length];c.lineWidth=2;
 if(bars){const bw=Math.min(18,(right-left)/(labels.length*series.length*2));s.values.forEach((v,i)=>c.fillRect(x(i)+(j-series.length/2)*bw,y(v),bw-1,bottom-y(v)));}
 else{c.beginPath();let begun=false;s.values.forEach((v,i)=>{if(v===null){begun=false;return;}if(begun)c.lineTo(x(i),y(v));else c.moveTo(x(i),y(v));begun=true;});c.stroke();s.values.forEach((v,i)=>{if(v===null)return;c.beginPath();c.arc(x(i),y(v),3,0,Math.PI*2);c.fill();});}});
 if(candles){const bw=Math.min(22,(right-left)/labels.length*.5);candles.forEach((r,i)=>{c.strokeStyle=c.fillStyle=r.close>=r.open?C[0]:'#f399b0';c.beginPath();c.moveTo(x(i),y(r.low));c.lineTo(x(i),y(r.high));c.stroke();c.fillRect(x(i)-bw/2,Math.min(y(r.open),y(r.close)),bw,Math.max(1,Math.abs(y(r.close)-y(r.open))));});}
 el._plot={left,right,w,count:labels.length};
 const legend=$(id+'-legend');if(legend){legend.replaceChildren();series.forEach((s,i)=>{const e=document.createElement('span');e.textContent=s.label;e.style.color=C[i%C.length];legend.appendChild(e);});}
}
function readout(kind,pos){const a=kind==='index'?D.indices.find(a=>a.symbol===S.index):D.assets.find(a=>a.symbol===S.stock);const r=kind==='index'?a.observations:a.observations.slice(-S.n),v=r[Math.max(0,Math.min(r.length-1,pos))];$(kind+'-readout').textContent=a.name+' | '+v.date+' | '+num(v.close)+(kind==='index'?' pt':' USD')+(kind==='stock'?' | O '+num(v.open)+' H '+num(v.high)+' L '+num(v.low)+' | Vol '+v.volume.toLocaleString('en-US'):'');}
function world(){
 const a=D.indices.find(x=>x.symbol===S.index),r=a.observations,v=r.map(x=>S.normal?x.close/r[0].close*100:x.close);
 $('index-title').textContent=a.name+' / '+(S.normal?'Start=100':'Index points');$('index-last').textContent=num(r.at(-1).close)+' pt';$('index-return').textContent=pct(change(r));$('index-basis').textContent=(a.basis==='price'?'Price':'Total return')+' / '+a.currency+' / '+a.zone;
 const links=$('index-sources');links.replaceChildren();a.sources.forEach((u,i)=>{const e=document.createElement('a');e.href=u;e.rel='noopener noreferrer';e.referrerPolicy='no-referrer';e.textContent='Source '+(i+1);links.appendChild(e);});
 graph('index-chart',[{label:a.symbol,values:v}],r.map(x=>x.date.slice(5)),{unit:S.normal?'Start=100':'points'});readout('index',2);
 const eligible=D.indices.filter(x=>x.basis==='price'&&(S.region==='all'||x.region===S.region));const selected=S.region==='all'?eligible.filter(x=>['SPX','TOPIX','FTSE','CAC','HSI','NIFTY'].includes(x.symbol)):eligible;
 graph('world-compare',selected.map(x=>({label:x.symbol,values:x.observations.map(v=>v.close/x.observations[0].close*100)})),r.map(x=>x.date.slice(5)),{unit:'Start=100'});
 const sorted=eligible.slice().sort((a,b)=>change(b.observations)-change(a.observations));$('world-analysis').textContent='9/8 - 9/10 | '+sorted.length+' indices | Positive: '+sorted.filter(x=>change(x.observations)>0).length+' | Highest: '+sorted[0].symbol+' '+pct(change(sorted[0].observations))+' | Lowest: '+sorted.at(-1).symbol+' '+pct(change(sorted.at(-1).observations));
 document.querySelectorAll('.index-card').forEach(x=>x.hidden=S.region!=='all'&&x.dataset.region!==S.region);
 document.querySelectorAll('[data-index]').forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.index===S.index)));
}
function stocks(){
 const a=D.assets.find(x=>x.symbol===S.stock),r=a.observations.slice(-S.n),labels=r.map(x=>x.date.slice(5));$('stock-title').textContent=a.name+' / '+a.symbol+' / '+a.kind;$('stock-last').textContent=num(r.at(-1).close);$('stock-return').textContent=pct(change(r));$('stock-dd').textContent=pct(dd(r));$('stock-source').href=a.sources[0];$('stock-source').textContent='Stock Analysis / '+a.symbol;
 const series=[];if(!S.candle)series.push({label:'Close',values:r.map(x=>x.close)});if(S.ma)series.push({label:'MA5',values:average(r)});if(!series.length)series.push({label:'OHLC',values:r.map(x=>null)});
 graph('price-chart',series,labels,{unit:'USD',candles:S.candle?r:null});readout('stock',r.length-1);
 graph('volume-chart',[{label:'Volume',values:r.map(x=>x.volume)}],labels,{unit:'Shares',bars:true,zero:true});
 graph('stock-compare',D.assets.filter(x=>x.symbol===S.stock||x.symbol==='SPY').map(x=>{const v=x.observations.slice(-S.n);return {label:x.symbol,values:v.map(y=>y.close/v[0].close*100)};}),labels,{unit:'Start=100'});
 const q=D.financials.periods;graph('financial-chart',[{label:'Revenue',values:q.map(x=>x.revenue)},{label:'Operating income',values:q.map(x=>x.operating_income)}],q.map(x=>x.period),{unit:'USD million',bars:true,zero:true});graph('margin-chart',[{label:'Gross margin',values:q.map(x=>x.gross_margin)},{label:'Operating margin',values:q.map(x=>x.operating_income/x.revenue*100)}],q.map(x=>x.period),{unit:'Percent',bars:true,zero:true});
 $('financial-yoy').textContent=pct((q.at(-1).revenue/q[0].revenue-1)*100);$('financial-margin').textContent=(q.at(-1).operating_income/q.at(-1).revenue*100).toFixed(2)+'%';
}
function draw(){world();stocks();}
function bind(sel,fn){document.querySelectorAll(sel).forEach(b=>b.addEventListener('click',()=>{fn(b);document.querySelectorAll(sel).forEach(x=>x.setAttribute('aria-pressed',String(x===b)));draw();}));}
bind('[data-index]',b=>S.index=b.dataset.index);
bind('button[data-region]',b=>{S.region=b.dataset.region;if(S.region!=='all'&&D.indices.find(x=>x.symbol===S.index).region!==S.region)S.index=D.indices.find(x=>x.region===S.region).symbol;});
bind('[data-index-mode]',b=>S.normal=b.dataset.indexMode==='normal');bind('[data-asset]',b=>S.stock=b.dataset.asset);bind('[data-price-mode]',b=>S.candle=b.dataset.priceMode==='candle');bind('[data-points]',b=>S.n=Number(b.dataset.points));
$('ma-toggle').addEventListener('click',()=>{S.ma=!S.ma;$('ma-toggle').setAttribute('aria-pressed',String(S.ma));draw();});
for(const [id,k] of [['index-chart','index'],['price-chart','stock']]){const e=$(id);let pos=0;e.addEventListener('pointermove',v=>{const p=e._plot;if(!p)return;pos=Math.round(((v.clientX-e.getBoundingClientRect().left)*p.w/e.clientWidth-p.left)/(p.right-p.left)*(p.count-1));readout(k,pos);});e.addEventListener('keydown',v=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(v.key))return;v.preventDefault();const n=e._plot.count;pos=v.key==='Home'?0:v.key==='End'?n-1:Math.min(n-1,Math.max(0,pos+(v.key==='ArrowRight'?1:-1)));readout(k,pos);});}
document.querySelectorAll('[data-tab]').forEach(b=>{b.addEventListener('click',()=>requestAnimationFrame(draw));b.addEventListener('keydown',()=>requestAnimationFrame(draw));});window.addEventListener('resize',()=>requestAnimationFrame(draw));document.querySelectorAll('.chart-controls').forEach(e=>e.hidden=false);activate($('tab-world'));requestAnimationFrame(draw);
})();

/* Independent, read-only market portal. All interactions stay in page memory. */
(()=>{
'use strict';
const $=id=>document.getElementById(id), D=JSON.parse($('market-data').textContent);
const ROWS=[...D.indices,...D.assets], MAP=new Map(ROWS.map(a=>[a.symbol,a]));
const J={home:'総合マーケット',screen:'比較・絞り込み',macro:'マクロ・データ',status:'出典・実装状況',ref:'二次情報 / 参考値',missing:'未接続',past:'過去の参考値',all:'すべて'};
const names={SPX:'S&P 500',IXIC:'NASDAQ総合',DJI:'ダウ30',N225:'日経225',TOPIX:'TOPIX',FTSE:'FTSE 100',DAX:'DAX / TR',CAC:'CAC 40',STOXX50E:'EURO STOXX 50',HSI:'香港ハンセン',SSEC:'上海総合',KOSPI:'KOSPI',NIFTY:'Nifty 50',ASX200:'ASX 200'};
const region={us:'米国',japan:'日本',europe:'欧州',asia:'アジア・大洋州'};
const dates=D.indices[0].observations.map(r=>r.date);
const type={index:'指数',stock:'個別株',etf:'ETF'};
const num=n=>new Intl.NumberFormat('en-US',{maximumFractionDigits:2,minimumFractionDigits:2}).format(n);
const pct=n=>(n>=0?'+':'')+n.toFixed(2)+'%';
const recent=a=>a.observations.filter(r=>dates.includes(r.date));
const ret=a=>{const r=recent(a);return (r.at(-1).close/r[0].close-1)*100;};
const dd=a=>{let high=0,low=0;for(const r of recent(a)){high=Math.max(high,r.close);low=Math.min(low,(r.close/high-1)*100);}return low;};
const comparable=a=>a.basis!=='total_return'&&!/derived/i.test(a.note||'');
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function add(parent,...children){children.forEach(c=>parent.append(c));return parent;}
function btn(label,fn,cls=''){const n=el('button',cls,label);n.type='button';n.addEventListener('click',fn);return n;}
function badge(text,cls=''){return el('span','p-badge '+cls,text);}
function source(url,label){const a=el('a','p-source',label);a.href=url;a.rel='noopener noreferrer';a.referrerPolicy='no-referrer';return a;}
function go(id,symbol){const t=$('tab-'+id);activate(t);t.click();if(symbol){const key=id==='world'?'index':'asset';const b=document.querySelector('[data-'+key+'="'+symbol+'"]');if(b)b.click();}window.scrollTo({top:0,behavior:'auto'});}
function card(title,...body){return add(el('article','p-card'),el('h3','',title),...body);}
function empty(parent){while(parent.firstChild)parent.firstChild.remove();}
function panel(id,label){const p=el('section','panel');p.id=id;p.setAttribute('aria-labelledby','tab-'+id);p.setAttribute('role','tabpanel');p.hidden=true;document.querySelector('footer').before(p);panels.push(p);const b=btn(label,()=>activate(b));b.id='tab-'+id;b.dataset.tab=id;b.setAttribute('aria-controls',id);b.setAttribute('role','tab');b.addEventListener('keydown',e=>navKey(e,b));tabs.push(b);document.querySelector('.nav').append(b);return p;}
function navKey(e,t){const order=[...document.querySelectorAll('.nav [data-tab]')];const i=order.indexOf(t);let n;
 if(['ArrowDown','ArrowRight'].includes(e.key))n=(i+1)%order.length;else if(['ArrowUp','ArrowLeft'].includes(e.key))n=(i+order.length-1)%order.length;else if(e.key==='Home')n=0;else if(e.key==='End')n=order.length-1;else return;
 e.preventDefault();e.stopImmediatePropagation();order[n].click();order[n].focus();}
const screen=panel('screener',J.screen),macro=panel('macro',J.macro);
const nav=document.querySelector('.nav');
const order=['overview','world','market','screener','macro','events','topics','scenarios','reports','archive','operations'];
const labels={overview:J.home,world:'世界指数',market:'株価・決算',events:'イベント',topics:'継続論点',scenarios:'シナリオ',reports:'レポート',archive:'履歴',operations:J.status,screener:J.screen,macro:J.macro};
order.forEach(id=>{const t=$('tab-'+id);t.textContent=labels[id];nav.append(t);t.addEventListener('keydown',e=>navKey(e,t),true);});
nav.setAttribute('aria-orientation',innerWidth>1050?'vertical':'horizontal');
const side=el('aside','p-sidebar'),brand=add(el('div','p-brand'),el('span','p-mark','E.'),el('div','','ECONOMICS\nRESEARCH'));
add(side,brand,el('p','p-nav-caption','RESEARCH WORKSPACE'),nav,el('p','p-sidebar-note','v0.5.0\nPUBLIC RESEARCH\n個人データの入力・保管用ではありません。'));
document.body.prepend(side);document.body.classList.add('portal-ready');
const mast=document.querySelector('.mast');empty(mast);
add(mast,el('div','p-mast-title','Economics Research Dashboard'),add(el('div','p-mast-status'),badge('v0.5.0'),badge('SNAPSHOT / '+D.as_of,'p-warn')));
document.title='Economics Research Dashboard | v0.5.0';
const oldAge=$('age');if(oldAge)oldAge.classList.add('p-stale');
const topNotice=document.querySelector('.wrap > .notice');if(topNotice)topNotice.remove();
const head=el('div','p-page-head');add(head,el('div','p-eyebrow','MARKET INTELLIGENCE / WORKSPACE'),el('h1','',J.home),el('p','p-lead','市場の全体像から、比較・根拠・次の確認へ。'));
const home=$('overview');empty(home);home.append(head);
const caution=add(el('div','p-caution'),badge(J.past,'p-warn'),el('p','','価格の最終収録は '+D.as_of+'。一次情報の照合未完了で、現在の相場や売買シグナルではありません。'));
home.append(caution);
const ribbon=el('div','p-ribbon');for(const symbol of ['SPX','IXIC','N225','TOPIX','FTSE','KOSPI']){const a=MAP.get(symbol);const b=btn('',()=>go('world',symbol),'p-ticker');add(b,el('span','',names[symbol]),el('strong','',num(a.observations.at(-1).close)),el('small',ret(a)>=0?'rise':'fall',pct(ret(a))+' / 9.8 - 9.10'));ribbon.append(b);}home.append(ribbon);
const kpis=el('div','p-kpis');for(const [a,b,c] of [['14','世界の指数','4地域 / 3観測点'],['6','個別株・ETF','5社 + 1 ETF / 6取引日'],['8','登録イベント','予想・実績は未収録'],['0','接続済み自動取得','リアルタイム値なし']])kpis.append(add(el('article','p-kpi'),el('small','',b),el('strong','',a),el('span','',c)));home.append(kpis);
const cols=el('div','p-home-cols'),heat=card('世界指数の参考マップ',el('p','small','同一期間 9/8 - 9/10 / 変化率の計算値。色は投資判断ではありません。'));
const tiles=el('div','p-heatmap');D.indices.forEach(a=>{const b=btn('',()=>go('world',a.symbol),'p-tile '+(comparable(a)?(ret(a)>=0?'p-up':'p-down'):'p-neutral'));add(b,el('span','',names[a.symbol]),el('strong','',pct(ret(a))),el('small','',!comparable(a)?'基準差・参考系列':region[a.region]));tiles.append(b);});heat.append(tiles);cols.append(heat);
const next=card('次に確認すること');const eventRows=[...document.querySelectorAll('.event-card')];
eventRows.slice(0,3).forEach(row=>{const title=row.querySelector('h3'),dt=row.querySelector('.date');if(title)add(next,add(el('div','p-agenda'),el('small','',dt?dt.textContent.trim():''),el('strong','',title.textContent.trim())));});
add(next,btn('全8件の登録日程を確認',()=>go('events'),'p-link-button'),el('p','small','会合の未確認時刻を補完せず、時差を区別して表示します。'));cols.append(next);home.append(cols);
const bottom=el('div','p-two');
const ranked=D.indices.filter(comparable).sort((a,b)=>ret(b)-ret(a));const leaders=card('参考値の相対比較');
ranked.slice(0,5).forEach((a,i)=>add(leaders,add(el('div','p-ranking'),el('span','p-rank',String(i+1).padStart(2,'0')),btn(names[a.symbol],()=>go('world',a.symbol),'p-text-button'),el('strong',ret(a)>=0?'rise':'fall',pct(ret(a))))));
add(leaders,el('p','small','配当再投資系と提供元の算出参考系列は除外。全系列とも一次照合は未完了です。'));
const plan=card('判断までの確認順',el('p','','1. 対象日・出典・基準を確認'),el('p','','2. 同じ期間で市場と銘柄を比較'),el('p','','3. 決算・反証条件で仮説を点検'),btn(J.screen+'を開く',()=>go('screener'),'p-link-button'));
add(bottom,leaders,plan);home.append(bottom);
// Screening uses one common date window; no mixed-currency level ranking.
add(screen,el('div','p-eyebrow','COMPARE & SCREEN'),el('h2','',J.screen),el('p','p-lead','20系列を同じ日付で比較。色より、条件と根拠を確認します。'));
const search=el('input','p-search');search.type='search';search.id='instrument-search';search.maxLength=40;search.autocomplete='off';search.spellcheck=false;search.setAttribute('aria-label','収録銘柄の検索');search.placeholder='銘柄名・シンボルで検索';
const searchLabel=el('label','p-search-label','銘柄検索');searchLabel.htmlFor=search.id;add(screen,searchLabel,search,el('p','small','検索はこの画面内のみ。記録・送信しません。個人データは入力しないでください。'));
const F={kind:'all',quality:'comparable',sort:'name',query:''},filterBar=el('div','p-screen-filters');
for(const [key,options] of [['kind',[['all',J.all],['index','指数'],['stock','個別株'],['etf','ETF']]],['quality',[['comparable','比較基準を揃える'],['all','基準差も表示']]],['sort',[['name','銘柄順'],['return','騰落率順'],['drawdown','下落幅順']]]]){const line=el('div','p-control-row');for(const [v,l] of options){const b=btn(l,()=>{F[key]=v;renderScreen();});b.dataset.screenFilter=key;b.dataset.screenValue=v;line.append(b);}filterBar.append(line);}
add(screen,filterBar);const summary=el('p','small');summary.id='screen-count';summary.setAttribute('aria-live','polite');screen.append(summary);
const tw=el('div','table-wrap'),table=el('table','data-table p-screen-table');table.id='screen-table';const thead=el('thead'),tr=el('tr');['銘柄 / 種別','最終収録値','共通期間の変化','期間内最大下落','基準・品質','出典'].forEach(t=>tr.append(el('th','',t)));thead.append(tr);const tbody=el('tbody');add(table,thead,tbody);add(tw,table);screen.append(tw);
const selections=new Set(['SPX','TOPIX']);const compare=card('共通日付・開始値100の比較',el('p','small','最大4系列。為替換算なし / 配当込み系列・算出参考系列は選択対象外。'));
const pick=el('div','p-pick');ROWS.filter(comparable).forEach(a=>{const b=btn(a.symbol,()=>{if(selections.has(a.symbol)){if(selections.size>1)selections.delete(a.symbol);}else if(selections.size<4)selections.add(a.symbol);else{compareNote.textContent='比較は最大4系列です。先に1つ解除してください。';return;}drawCompare();});b.dataset.compare=a.symbol;pick.append(b);});
const canvas=el('canvas');canvas.id='portal-compare';canvas.height=290;canvas.setAttribute('role','img');canvas.setAttribute('aria-label','選択銘柄の開始値100比較');const compareNote=el('p','small');compareNote.id='compare-note';compareNote.setAttribute('aria-live','polite');const cmpTable=el('div','p-compare-values');cmpTable.id='compare-values';add(compare,pick,canvas,compareNote,cmpTable);screen.append(compare);
function renderScreen(){document.querySelectorAll('[data-screen-filter]').forEach(b=>b.setAttribute('aria-pressed',String(F[b.dataset.screenFilter]===b.dataset.screenValue)));let rows=ROWS.filter(a=>(F.kind==='all'||F.kind===a.kind)&&(F.quality==='all'||comparable(a))&&((a.symbol+' '+a.name+' '+(names[a.symbol]||'')).toLowerCase().includes(F.query)));
 rows.sort((a,b)=>{if(F.sort==='name')return a.symbol.localeCompare(b.symbol);if(comparable(a)!==comparable(b))return comparable(a)?-1:1;if(!comparable(a))return a.symbol.localeCompare(b.symbol);return F.sort==='return'?ret(b)-ret(a):dd(a)-dd(b);});empty(tbody);
 rows.forEach(a=>{const r=el('tr');r.dataset.symbol=a.symbol;const cell=el('td');add(cell,btn(names[a.symbol]||a.symbol,()=>go(a.kind==='index'?'world':'market',a.symbol),'p-text-button'),el('small','',type[a.kind]+' / '+a.symbol));const unit=a.kind==='index'?'pt':a.currency;const can=comparable(a);add(r,cell,el('td','',num(recent(a).at(-1).close)+' '+unit),el('td',ret(a)>=0?'rise':'fall',can?pct(ret(a)):'比較対象外'),el('td','',can?pct(dd(a)):'—'),el('td','small',!can?'基準差 / 参考系列':J.ref),add(el('td'),source(a.sources[0],'出典')));tbody.append(r);});
 summary.textContent=rows.length+' / 20系列 | '+dates[0]+' - '+dates.at(-1)+' / 全系列の共通3点'+(rows.length?'':' / 一致する銘柄はありません');}
search.addEventListener('input',()=>{F.query=search.value.slice(0,40).trim().toLowerCase();renderScreen();});search.addEventListener('keydown',e=>{if(e.key==='Escape'){search.value='';F.query='';renderScreen();}});renderScreen();
function drawCompare(){if(screen.hidden)return;const rs=[...selections].map(s=>MAP.get(s)),colors=['#6dd8ba','#8aafff','#f4ce8a','#d1a4f3'];pick.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(selections.has(b.dataset.compare))));const w=Math.max(260,canvas.parentElement.clientWidth-42),h=290,dpr=Math.min(devicePixelRatio||1,3);canvas.width=w*dpr;canvas.height=h*dpr;canvas.style.height=h+'px';const c=canvas.getContext('2d');c.scale(dpr,dpr);const series=rs.map(a=>recent(a).map(r=>100*r.close/recent(a)[0].close));const all=series.flat(),lo=Math.min(...all)-.25,hi=Math.max(...all)+.25,x=i=>52+i*(w-75)/2,y=v=>238-(v-lo)/(hi-lo)*200;c.font='11px sans-serif';c.strokeStyle='#263c52';c.fillStyle='#a9bdce';
 for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4;const yy=y(v);c.beginPath();c.moveTo(50,yy);c.lineTo(w-15,yy);c.stroke();c.fillText(v.toFixed(1),7,yy+4);}dates.forEach((d,i)=>c.fillText(d.slice(5),x(i)-16,266));
 series.forEach((values,j)=>{c.strokeStyle=colors[j];c.fillStyle=colors[j];c.lineWidth=2.4;c.beginPath();values.forEach((v,i)=>i?c.lineTo(x(i),y(v)):c.moveTo(x(i),y(v)));c.stroke();values.forEach((v,i)=>{c.beginPath();c.arc(x(i),y(v),3.5,0,Math.PI*2);c.fill();});});empty(cmpTable);
 rs.forEach((a,j)=>{const n=el('div','p-compare-value');n.style.borderColor=colors[j];add(n,el('strong','',a.symbol),el('span','',pct(ret(a))),el('small','',dates[0]+' - '+dates.at(-1)));cmpTable.append(n);});compareNote.textContent=rs.length+'系列を比較 / 各市場の引け時刻は同時ではありません。';}
$('tab-screener').addEventListener('click',()=>requestAnimationFrame(drawCompare));window.addEventListener('resize',()=>requestAnimationFrame(drawCompare));
// Data coverage is a measured inventory, never a fictional market reading.
add(macro,el('div','p-eyebrow','DATA CATALOG / MACRO'),el('h2','',J.macro),el('p','p-lead','空欄を0で埋めない。未接続と観測値を明確に区別します。'));
const catalogue=[['米国金利・政策','金利・金利カーブの時系列は未収録。会合日程は登録済み。','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm','FRB'],['CPI / 消費者物価','実績、改定値、対象月を分けて収録する必要があります。','https://www.bls.gov/cpi/','BLS'],['PCE / 個人消費物価','総合とコア、前月比と前年比を分離します。','https://www.bea.gov/data/personal-consumption-expenditures-price-index','BEA'],['雇用・失業率','発表日と統計対象月、改定履歴の管理が必要です。','https://www.bls.gov/schedule/2026/home.htm','BLS'],['VIX / 変動性','恐怖スコアを自作せず、確認済みの原系列を使います。','https://www.cboe.com/tradable-products/vix','Cboe'],['為替・資源価格','通貨ペア、取引単位、先物の限月を確認してから追加します。',null,'']];
const macroGrid=el('div','p-three');catalogue.forEach(([title,note,url,label])=>{const c=card(title,badge(J.missing,'p-warn'),el('div','p-missing','—'),el('p','small',note));if(url)c.append(source(url,label+' / 公式情報'));macroGrid.append(c);});macro.append(macroGrid);
const coverage=card('現在のデータカバレッジ');[['世界指数','14系列 / 3点','二次情報・一次照合待ち'],['株価・ETF','6系列 / 6日','限定スナップショット'],['決算','1社 / 比較3期間','前版からの収録値'],['金利・物価・VIX','未収録','時系列接続前'],['コンセンサス予想','未収録','利用条件・提供元の確認が必要']].forEach(a=>coverage.append(add(el('div','p-coverage-row'),el('strong','',a[0]),el('span','',a[1]),el('small','',a[2]))));macro.append(coverage);
const operations=$('operations');operations.querySelector('h2')?.remove();operations.prepend(el('h2','',J.status));
const statusGrid=el('div','p-two');statusGrid.append(card('公開前の三段階',el('p','','① 公開可能な原稿・データのみを準備'),el('p','','② 内容・参照先・整合性を公開書込前に検査'),el('p','','③ 配信前の自動検査とHTTPS内容照合')));
statusGrid.append(card('おさえるべき境界',el('p','','本サイトは公開リサーチ用。他サイトの公式版・提携サービスではありません。'),el('p','small','参照サイトの画面・リサーチ全文との厳密な照合は未完了。完全再現や脆弱性ゼロを保証しません。')));operations.append(statusGrid);
const roadmap=card('実装状況と次の依存条件');[
 ['UI / 実装済み','総合画面、銘柄検索、絞込み、共通期間比較、データ品質表示'],
 ['DATA / 依存条件待ち','長期履歴・毎日の更新は、取得元と再配布条件の確認が前提'],
 ['RESEARCH / 未接続','レポート本文・過去履歴・ニュース自動取込は別工程'],
 ['RELEASE / 継続','更新ごとに内容照合と画面テスト。データの無い指標を作らない']
].forEach(([t,b])=>roadmap.append(add(el('div','p-roadmap'),el('strong','',t),el('p','small',b))));operations.append(roadmap);
const archive=$('archive');archive.append(card('v0.5.0 / 2026-09-13',el('p','','市場全体の入口を再設計。価格データは前版の収録値を維持し、更新したとは扱わない。')));
// Expose a small read-only verification surface, containing public calculations only.
Object.defineProperty(window,'EconomicsPortal',{value:Object.freeze({version:'0.5.0',commonDates:Object.freeze([...dates]),metrics:s=>{const a=MAP.get(s);return a?Object.freeze({returnPct:ret(a),drawdownPct:dd(a),comparable:comparable(a)}):null;}})});
document.querySelector('footer').textContent='Public research / v0.5.0 / 自動更新なし / 追跡タグなし。検索は画面内だけで処理し、保存・送信しません。';
activate($('tab-overview'));
})();
