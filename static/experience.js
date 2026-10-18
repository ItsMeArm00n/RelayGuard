/* Presentation layer: existing API/model behaviour remains the source of truth. */
const icons={
 grid:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
 shield:'<path d="m12 3 8 3v5c0 5-4 8-8 10-4-2-8-5-8-10V6Z"/><path d="M12 8v5m0 3h.01"/>',
 chart:'<path d="M4 3v17h17M8 14l4-4 4 2 5-7"/>',
 settings:'<path d="m9 3-.7 2.5-2 .9L4 5.8 2 9l1.8 1.8v2.4L2 15l2 3.2 2.3-.6 2 .9L9 21h4l.7-2.5 2-.9 2.3.6 2-3.2-1.8-1.8v-2.4L20 9l-2-3.2-2.3.6-2-.9L13 3Z"/><circle cx="11" cy="12" r="3"/>',
 arrow:'<path d="M4 12h15m-5-5 5 5-5 5"/>',
 download:'<path d="M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5"/>',
 upload:'<path d="M12 16V4m-4 4 4-4 4 4M4 16v5h16v-5"/>',
 database:'<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 4 16 4 16 0V5M4 12v7c0 4 16 4 16 0v-7"/>',
 lock:'<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V6a4 4 0 0 1 8 0v4m-4 5v2"/>',
 layers:'<path d="m12 3 10 5-10 5L2 8Zm-10 9 10 5 10-5M2 16l10 5 10-5"/>',
 pulse:'<path d="M2 12h5l3-8 4 16 3-8h5"/>',
 scan:'<path d="M8 3H3v5m13-5h5v5M3 16v5h5m8 0h5v-5M7 12h10M9 8v8m6-8v8"/>',
 user:'<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
 arrows:'<path d="M3 7h17m-4-4 4 4-4 4M21 17H4m4-4-4 4 4 4"/>',
 check:'<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
 bolt:'<path d="m13 2-9 12h7l-1 8 10-13h-7Z"/>',
 play:'<path d="m8 4 12 8-12 8Z"/>',pause:'<path d="M8 4v16m8-16v16"/>',
 search:'<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>',
 plus:'<path d="M12 4v16M4 12h16"/>',
 mouse:'<rect x="6" y="2" width="12" height="20" rx="6"/><path d="M12 6v4"/>',
 filter:'<path d="M3 4h18l-7 8v7l-4 2v-9Z"/>',
 info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10h.01"/>',
 sliders:'<path d="M4 6h4m4 0h8M4 18h8m4 0h4"/><circle cx="10" cy="6" r="2"/><circle cx="14" cy="18" r="2"/>',
 reset:'<path d="M3 10a9 9 0 1 1 1 7M3 3v7h7"/>',
 close:'<path d="m6 6 12 12M6 18 18 6"/>',
 chevron:'<path d="m9 5 7 7-7 7"/>',
 inbox:'<path d="m5 3-3 12v6h20v-6L19 3ZM2 15h6l2 3h4l2-3h6"/>'
};
function icon(name){return `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${icons[name]||icons.info}</svg>`}
function mountIcons(root=document){root.querySelectorAll('[data-icon]').forEach(e=>e.innerHTML=icon(e.dataset.icon))}
mountIcons();
document.getElementById('today').textContent=new Intl.DateTimeFormat('en',{month:'short',day:'numeric',year:'numeric'}).format(new Date());
const descriptions={overview:'A clear view of your payments. Context for every decision.',alerts:'Focus on the signals that need your judgment.',performance:'Understand the evidence behind your detection model.',setup:'Your data source, alert policy, and session controls.'};
const pageNames={overview:'Risk overview',alerts:'Review queue',performance:'Model studio',setup:'Data & settings'};
function navigate(page){
  document.querySelectorAll('nav button').forEach(button=>{const active=button.dataset.page===page;button.classList.toggle('active',active);if(active)button.setAttribute('aria-current','page');else button.removeAttribute('aria-current')});
  document.querySelectorAll('.page').forEach(p=>p.classList.toggle('hidden',p.id!==page));
  $('#page-title').textContent=pageNames[page];$('#page-description').textContent=descriptions[page];$('#breadcrumb-page').textContent=pageNames[page];
}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>navigate(b.dataset.page));
document.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>navigate(b.dataset.go));
document.addEventListener('keydown',event=>{
  if(event.key==='/'&&!document.querySelector('dialog[open]')&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){event.preventDefault();navigate('overview');$('#search').focus()}
});

table=function(rows){
  if(!rows.length){const filtered=$('#search').value||$('#review-filter').value!=='All reviews';return `<div class="empty ${filtered?'filtered':''}"><div class="empty-icon">${icon(filtered?'search':'inbox')}</div><strong>${filtered?'No matching payments':'A clear desk. Ready for the next signal.'}</strong><small>${filtered?'Try another search or review filter.':'Start the replay or submit a hypothetical payment to begin.'}</small></div>`}
  return `<table><thead><tr><th>Transaction</th><th>Account route</th><th>Amount</th><th>Risk score</th><th>Decision</th><th>Review status</th><th aria-label="Open payment"></th></tr></thead><tbody>${rows.map(r=>`<tr data-id="${esc(r.id)}" tabindex="0" aria-label="Open transaction ${esc(r.id)}"><td class="id">${esc(r.id)}<small>${esc(r.type)} · Step ${r.step}</small></td><td><div class="route">${esc(r.sender)}${icon('arrow')}${esc(r.recipient)}</div></td><td class="amount-cell">${r.amount.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}</td><td><div class="score ${r.flagged?'high':''}">${r.score.toFixed(3)}<i><b style="width:${r.score*100}%"></b></i></div></td><td><span class="badge ${r.flagged?'warn':''}">${r.flagged?'Review suggested':'Low risk'}</span></td><td><span class="review-label">${esc(r.review)}</span></td><td class="row-chevron">${icon('chevron')}</td></tr>`).join('')}</tbody></table>`
};
document.addEventListener('keydown',event=>{const row=event.target.closest('tr[data-id]');if(row&&(event.key==='Enter'||event.key===' ')){event.preventDefault();details(row.dataset.id)}});

let chartSignature='';
function drawChart(){
  const data=state.events.slice(0,48).reverse();$('#chart-threshold').textContent=state.threshold.toFixed(3);
  if(!data.length){$('#chart').innerHTML=`<div class="empty"><div class="empty-icon">${icon('pulse')}</div><strong>Waiting for the first payment.</strong><small>Your scores will appear here as the replay begins.</small></div>`;chartSignature='';return}
  const signature=data.map(r=>r.id).join('|');const changed=signature!==chartSignature;chartSignature=signature;
  const x=i=>34+(data.length===1?300:i/(data.length-1)*600);const y=s=>144-Math.max(0,Math.min(1,s))*130;
  const coordinates=data.map((r,i)=>`${x(i)},${y(r.score)}`).join(' ');const area=`M${x(0)},144 L${coordinates.replaceAll(' ',' L')} L${x(data.length-1)},144 Z`;
  $('#chart').innerHTML=`<svg viewBox="0 0 650 170" preserveAspectRatio="none" role="img" aria-label="Model risk scores of the latest ${data.length} scored payments. Dashed line: current alert threshold ${state.threshold.toFixed(4)}." class="${changed?'chart-enter':''}"><defs><linearGradient id="score-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1766d8" stop-opacity=".16"/><stop offset="100%" stop-color="#1766d8" stop-opacity=".01"/></linearGradient></defs>${[0,.5,1].map(v=>`<line class="chart-grid" x1="32" x2="638" y1="${y(v)}" y2="${y(v)}"/><text x="0" y="${y(v)+3}">${v.toFixed(1)}</text>`).join('')}<path d="${area}" fill="url(#score-fill)"/><line class="policy-line" x1="32" x2="638" y1="${y(state.threshold)}" y2="${y(state.threshold)}"/><polyline class="chart-line" points="${coordinates}"/>${data.map((r,i)=>`<circle class="point ${r.flagged?'flag':''}" cx="${x(i)}" cy="${y(r.score)}" r="${r.flagged?3.7:2.4}"><title>${esc(r.id)} · score ${r.score.toFixed(4)} · ${r.flagged?'Review suggested':'Low risk'}</title></circle>`).join('')}</svg>`;
}
function drawPerformance(){
  const reports=Object.values(state.reports);const r=reports[reports.length-1];if(!r)return;
  $('#performance-summary').innerHTML=`<article class="featured"><span class="section-label">FRAUD DETECTION / RECALL</span><span class="metric-note">${icon('scan')}</span><strong>${(100*r.recall).toFixed(1)}<small>%</small></strong><p>${r.tp} of ${r.test_fraud} labelled frauds detected</p></article><article><span class="section-label">ALERT QUALITY / PRECISION</span><span class="metric-note">${icon('shield')}</span><strong>${(100*r.precision).toFixed(1)}<small>%</small></strong><p>${r.tp} correct flags out of ${r.tp+r.fp} alerts</p></article><article><span class="section-label">LEGITIMATE PAYMENT FALSE ALERTS</span><span class="metric-note">${icon('filter')}</span><strong>${r.fp.toLocaleString()}</strong><p>Among ${(r.fp+r.tn).toLocaleString()} legitimate test payments</p></article>`;
  $('#model-chip').textContent='HELD-OUT EVALUATION';
  $('#cohort').innerHTML=`<div class="cohort-heading"><span>Fraud detection breakdown</span><strong>${r.test_fraud.toLocaleString()} frauds in the held-out cohort</strong></div><div class="cohort-bar" role="img" aria-label="${r.tp} frauds detected; ${r.fn} frauds missed"><span style="width:${100*r.recall}%;background:#1766d8"></span><span style="width:${100*(1-r.recall)}%;background:#163965"></span></div><div class="cohort-key"><span><b style="background:#1766d8"></b>${r.tp} detected</span><span><b style="background:#163965"></b>${r.fn} missed</span><span><b style="background:#91a9c8"></b>${r.fp} legitimate payments flagged</span></div>`;
}
function updateControls(){
  const playing=timer!==null;
  $('#play').innerHTML=icon(playing?'pause':'play')+(playing?'Pause replay':'Start replay');
  $('#replay-status').textContent=playing?'STREAMING':'READY';document.body.classList.toggle('replaying',playing);
}
const renderBeforeDesign=render;
render=function(){
  renderBeforeDesign();
  $('#connection-label').textContent='Backend connected';
  $('#loaded-count').textContent=state.events.length.toLocaleString();
  const alerts=state.events.filter(r=>r.flagged);
  $('#queue-open').textContent=alerts.filter(r=>r.review==='Unreviewed').length;
  $('#queue-investigate').textContent=alerts.filter(r=>r.review==='Needs investigation').length;
  $('#queue-dismissed').textContent=alerts.filter(r=>r.review==='Dismissed').length;
  const progress=state.split.test?Math.max(0,Math.min(100,(state.split.test-state.remaining)/state.split.test*100)):0;
  $('#replay-progress').style.transform='scaleX('+(progress/100)+')';$('#replay-percent').textContent=progress.toFixed(1)+'%';
  drawChart();drawPerformance();updateControls();
};
const stopBeforeDesign=stop;
stop=function(){stopBeforeDesign();updateControls()};
$('#play').addEventListener('click',updateControls);
$('#csv').addEventListener('change',()=>{$('#file-name').textContent=$('#csv').files[0]?.name||'CSV · up to 40 MB / 150,000 rows'});

details=function(id){
  selected=state.events.find(r=>r.id===id);if(!selected)return;const r=selected;
  $('#detail-content').innerHTML=`<div class="detail-heading"><div class="eyebrow">INVESTIGATION WORKSPACE</div><h2>${esc(r.id)}</h2><div class="detail-summary"><span class="badge ${r.flagged?'warn':''}">${r.flagged?'Review suggested':'Low risk'}</span><span class="detail-score">Model score <strong>${r.score.toFixed(4)}</strong></span></div></div><div class="detail-grid"><div><small>Account route</small><strong>${esc(r.sender)} → ${esc(r.recipient)}</strong></div><div><small>Amount / payment type</small><strong>${r.amount.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})} / ${esc(r.type)}</strong></div><div><small>Timeline / source</small><strong>Step ${r.step} · ${esc(r.origin)}</strong></div><div><small>Recorded policy / model</small><strong>${r.threshold.toFixed(4)} / ${esc(r.version)}</strong></div></div><section id="why-score" class="why-score" aria-live="polite"><h2>Why this score?</h2><div class="explain-loading">Calculating contributions from the recorded model inputs…</div></section><p class="context-coverage">Context coverage: ${esc(r.context_source||'Observed session history')}</p><section class="context-section"><h2>Observed context</h2><div class="evidence">${r.reasons.map(reason=>`<p>${icon('check')}<span>${esc(reason)}</span></p>`).join('')}</div><p>Supporting observations explain context. They are not causal proof of fraud.</p></section><section class="review-section"><h2>Your review decision</h2><textarea id="note" maxlength="1000" aria-label="Review note" placeholder="Record what you observed and the next action…">${esc(r.note)}</textarea><p>Current status: ${esc(r.review)}</p><div class="review-buttons"><button class="primary" id="investigate">${icon('shield')}Needs investigation</button><button class="secondary" id="dismiss">${icon('check')}Dismiss alert</button></div></section>`;
  $('#investigate').onclick=()=>review('Needs investigation');$('#dismiss').onclick=()=>review('Dismissed');
  if(!$('#detail').open)$('#detail').showModal();$('#detail').scrollTop=0;loadExplanation(r.id);
};
// Bootstrap can complete before this final script on a cached connection.
if(state.source)render();


