// Browser regression on the actual public artifact; TradingView transport is allowlisted and blocked during deterministic CI.
import {spawn} from 'node:child_process';
import {mkdtemp,rm,readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const html=await readFile(resolve(process.argv[2]),'utf8');
const assertions=await readFile(join(dirname(fileURLToPath(import.meta.url)),'release_assertions.js'),'utf8');
const START_TIMEOUT_MS=20000;
const MAX_START_ATTEMPTS=2;
const delay=ms=>new Promise(ok=>setTimeout(ok,ms));

async function runBrowserCheck(){
 const profile=await mkdtemp(join(tmpdir(),'macro-release-'));
 const args=['--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--disable-sync','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'];
 if(process.getuid&&process.getuid()===0)args.unshift('--no-sandbox');
 const proc=spawn(process.env.CHROME_BIN||'google-chrome',args,{stdio:['ignore','ignore','pipe']});let socket;
 try{
  const endpoint=await new Promise((ok,bad)=>{let buffer='';const timer=setTimeout(()=>bad(Error('start timeout')),START_TIMEOUT_MS);proc.on('error',()=>{clearTimeout(timer);bad(Error('browser unavailable'));});proc.on('exit',()=>{clearTimeout(timer);bad(Error('browser exited'));});proc.stderr.on('data',b=>{buffer=(buffer+b.toString()).slice(-10000);const m=buffer.match(/DevTools listening on (ws:\/\/[^\s]+)/);if(m){clearTimeout(timer);ok(m[1]);}});});
  socket=new WebSocket(endpoint);await new Promise((ok,bad)=>{socket.onopen=ok;socket.onerror=bad;});let seq=0,session;const pending=new Map(),errors=[],requests=[];
  socket.onmessage=e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){const {ok,bad,timer}=pending.get(m.id);pending.delete(m.id);clearTimeout(timer);if(m.error)bad(Error('CDP command'));else ok(m.result);}else if(m.sessionId===session){if(m.method==='Runtime.exceptionThrown')errors.push(1);if(m.method==='Network.requestWillBeSent')requests.push(m.params.request.url);}};
  function send(method,params={},scoped=true){return new Promise((ok,bad)=>{const id=++seq,timer=setTimeout(()=>{pending.delete(id);bad(Error('CDP timeout'));},20000);pending.set(id,{ok,bad,timer});const m={id,method,params};if(scoped&&session)m.sessionId=session;socket.send(JSON.stringify(m));});}
  const t=await send('Target.createTarget',{url:'about:blank'},false);session=(await send('Target.attachToTarget',{targetId:t.targetId,flatten:true},false)).sessionId;
  await send('Page.enable');await send('Runtime.enable');await send('Network.enable');
  await send('Network.setBlockedURLs',{urls:['https://s3.tradingview.com/*','https://*.tradingview.com/*','https://*.tradingview-widget.com/*','wss://*.tradingview.com/*','wss://*.tradingview-widget.com/*']});
  async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails){const detail=r.exceptionDetails.exception?.description||r.exceptionDetails.text||'browser assertion';throw Error(detail.split('\n')[0]);}return r.result.value;}
  async function load(){await send('Page.navigate',{url:'about:blank'});await new Promise(ok=>setTimeout(ok,100));const f=await send('Page.getFrameTree');await send('Page.setDocumentContent',{frameId:f.frameTree.frame.id,html});await new Promise(ok=>setTimeout(ok,180));}
  const results=[];for(const width of [390,768,1440]){await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});await load();results.push(await evaluate('('+assertions+')()'));}
  await send('Emulation.setScriptExecutionDisabled',{value:true});await load();
  const external=requests.filter(u=>/^(?:https?|wss?):/i.test(u));
  const allowed=u=>/^https:\/\/(?:[^./]+\.)?tradingview\.com\//i.test(u)||/^https:\/\/(?:[^./]+\.)?tradingview-widget\.com\//i.test(u)||/^wss:\/\/(?:[^./]+\.)?tradingview\.com\//i.test(u)||/^wss:\/\/(?:[^./]+\.)?tradingview-widget\.com\//i.test(u);
  const unexpected=external.filter(u=>!allowed(u));
  if(!(await evaluate("document.querySelectorAll('.panel').length===9 && [...document.querySelectorAll('.panel')].every(p=>!p.hidden) && document.querySelector('.nav').hidden && document.body.textContent.includes('VIX withheld')"))||errors.length||unexpected.length)throw Error('fallback or unexpected background request');
  console.log(JSON.stringify({status:'PASS',viewports:[390,768,1440],cases:results,external_requests:external.length,unexpected_external_requests:unexpected.length,page_errors:0,no_script:true,source_links_not_clicked:true}));await send('Browser.close',{},false).catch(()=>{});
 }finally{
  if(socket)socket.close();
  if(!proc.killed)proc.kill('SIGKILL');
  await delay(250);
  await rm(profile,{recursive:true,force:true}).catch(()=>{});
 }
}

let failure=null;
for(let attempt=1;attempt<=MAX_START_ATTEMPTS;attempt++){
 try{await runBrowserCheck();failure=null;break;}
 catch(e){
  failure=e;
  if(e?.message==='start timeout'&&attempt<MAX_START_ATTEMPTS){console.error('BROWSER START RETRY: start timeout; retrying once with a clean profile');await delay(500);continue;}
  break;
 }
}
if(failure){console.error('BROWSER CHECK FAILED: '+failure.message);process.exitCode=1;}
