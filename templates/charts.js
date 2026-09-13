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
const J={home:'ç·åˆå¸‚å ´ç”»éŠ œ±ÍÉ••¸èŸš¾S¢òïÚû
+¢úóÿ)Ÿ,macro*&ŠÛ^uÛ¶‰^a