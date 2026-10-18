// Extend rendering without replaying entry effects for old transactions.
const reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)');
const countFrames=new WeakMap();let motionSeen=new Set();
function countTo(element,from,to){
  if(countFrames.has(element))cancelAnimationFrame(countFrames.get(element));
  if(reducedMotion.matches||from===to){element.textContent=to.toLocaleString();return}
  const start=performance.now();element.classList.add('value-changing');
  function frame(now){const t=Math.min(1,(now-start)/420);element.textContent=Math.round(from+(to-from)*(1-Math.pow(1-t,3))).toLocaleString();if(t<1)countFrames.set(element,requestAnimationFrame(frame));else{element.classList.remove('value-changing');countFrames.delete(element)}}
  countFrames.set(element,requestAnimationFrame(frame));
}
const originalRender=render;
render=function(){
  const fields=['total','flagged','reviewed'];
  const before=fields.map(id=>Number(document.getElementById(id).textContent.replaceAll(',',''))||0);
  const arrivals=new Set(state.events.filter(r=>!motionSeen.has(r.id)).slice(0,12).map(r=>r.id));
  originalRender();
  fields.forEach((id,i)=>countTo(document.getElementById(id),before[i],[state.count,state.alerts,state.reviewed][i]));
  document.querySelectorAll('tr[data-id]').forEach(row=>{if(arrivals.has(row.dataset.id))row.classList.add('new-payment')});
  const bars=document.querySelectorAll('#chart .bar');
  state.events.slice(0,48).reverse().forEach((r,i)=>{if(arrivals.has(r.id)&&bars[i])bars[i].classList.add('new-bar')});
  motionSeen=new Set(state.events.map(r=>r.id));
  document.body.classList.toggle('replaying',timer!==null);
};
const originalStop=stop;
stop=function(){originalStop();document.body.classList.remove('replaying')};
document.getElementById('play').addEventListener('click',()=>document.body.classList.toggle('replaying',timer!==null));
