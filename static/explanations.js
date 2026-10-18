// On-demand explanations use the feature snapshot from the original decision.
async function loadExplanation(id){
  const panel=document.getElementById('why-score');
  if(!panel)return;
  panel.setAttribute('aria-busy','true');
  try{
    const result=await api('explain/'+encodeURIComponent(id));
    if(selected?.id!==id||!document.getElementById('detail').open)return;
    const max=Math.max(.000001,...result.contributions.map(r=>Math.abs(r.value)));
    const rows=[...result.contributions].sort((a,b)=>Math.abs(b.value)-Math.abs(a.value));
    const signed=v=>(v>0?'+':'')+v.toFixed(4);
    panel.innerHTML=`<div class="explain-heading"><h2>Why this score?</h2><span class="explain-method">MODEL ATTRIBUTION</span></div>
      <p class="explain-summary">${esc(result.summary)}</p>
      <div class="score-journey"><div><small>Reference score</small><strong>${result.baseline.toFixed(4)}</strong></div><span>→</span><div><small>Net contribution</small><strong>${signed(result.score-result.baseline)}</strong></div><span>→</span><div><small>This payment</small><strong>${result.score.toFixed(4)}</strong></div></div>
      <div class="attribution-legend"><span>← Lowers the score</span><span>Raises the score →</span></div>
      <div class="attributions">${rows.map(r=>{const width=Math.abs(r.value)/max*48;return `<div class="attribution"><div class="attribution-label"><span>${esc(r.label)}</span><strong class="${r.value>0?'raises':'lowers'}">${signed(r.value)}</strong></div><div class="attribution-track" role="img" aria-label="${esc(r.label)}: ${r.direction} the score by ${Math.abs(r.value).toFixed(4)}"><div class="attribution-bar ${r.value>0?'raises':'lowers'}" style="left:${r.value>=0?50:50-width}%;width:${width}%"></div></div></div>`}).join('')}</div>
      <p class="reconciled">✓ Reference + all contributions = the recorded model score.</p>
      <details class="explain-notes"><summary>How to read this explanation</summary><p>Positive values raised the model score relative to the reference; negative values lowered it. They are score units, not percentages of fraud risk.</p><p>${esc(result.method)} over ${result.reference_count} training reference observations. Related inputs, such as payment-type indicators and clock features, are explained together.</p><p>${esc(result.limitation)}</p></details>`;
  }catch(error){
    if(selected?.id!==id)return;
    panel.innerHTML=`<h2>Why this score?</h2><p class="explain-unavailable">${esc(error.message)}</p>`;
  }finally{if(selected?.id===id&&document.getElementById('why-score'))document.getElementById('why-score').setAttribute('aria-busy','false')}
}
