/* Track attention changes independently of table filtering and animation frames. */
class ReviewAlertTracker {
  constructor(){this.known=new Set()}
  update(events){
    const pending=events.filter(event=>event.flagged&&event.review!=='Dismissed');
    const arrivals=pending.filter(event=>!this.known.has(event.id));
    this.known=new Set(pending.map(event=>event.id));
    return {pending,arrivals};
  }
}
(()=>{
  const tracker=new ReviewAlertTracker();
  const tab=document.querySelector('nav [data-page="alerts"]');
  const count=document.getElementById('nav-count');
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const announcement=document.createElement('div');announcement.className='sr-only';announcement.id='review-announcement';announcement.setAttribute('role','status');announcement.setAttribute('aria-live','polite');announcement.setAttribute('aria-atomic','true');document.body.append(announcement);
  let firstFrame=0,secondFrame=0;
  function clearPulse(){cancelAnimationFrame(firstFrame);cancelAnimationFrame(secondFrame);tab.classList.remove('review-attention')}
  function flash(){
    clearPulse();if(reduced.matches||tab.classList.contains('active'))return;
    firstFrame=requestAnimationFrame(()=>{secondFrame=requestAnimationFrame(()=>tab.classList.add('review-attention'))});
  }
  function update(){
    if(!Array.isArray(state.events))return;
    const {pending,arrivals}=tracker.update(state.events);
    tab.classList.toggle('has-review-alerts',pending.length>0);
    count.classList.toggle('requires-review',pending.length>0);
    tab.title=`${state.alerts} flagged payments; ${pending.length} require attention in the loaded payment window.`;
    if(!pending.length){clearPulse();announcement.textContent='No payments require review in the loaded payment window.'}
    else if(arrivals.length){
      announcement.textContent=`${arrivals.length} ${arrivals.length===1?'payment requires':'payments require'} review. ${pending.length} awaiting attention in the loaded payment window.`;
      flash();
    }
  }
  tab.addEventListener('click',clearPulse);
  tab.addEventListener('animationend',event=>{if(event.animationName==='review-arrival')clearPulse()});
  reduced.addEventListener('change',()=>{if(reduced.matches)clearPulse()});
  const previousRender=render;render=function(){previousRender();update()};
  update();
})();
