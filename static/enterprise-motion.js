/* Motion is progressive enhancement: content starts visible and stays usable. */
(()=>{
  'use strict';
  const preference=matchMedia('(prefers-reduced-motion: reduce)');
  const curve='cubic-bezier(0.16, 1, 0.3, 1)';
  const revealed=new WeakSet();
  const running=new Set();
  let entranceTimer=0;
  const revealSelector='.page > .stats, .page > .control-bar, .page > .panel, .page > .disclosure, .page > .queue-summary, .page > .performance-summary, .page > .settings-list';

  function animate(element,frames,options={}){
    if(preference.matches||!element||!element.isConnected)return;
    const animation=element.animate(frames,{duration:460,easing:curve,fill:'backwards',...options});
    running.add(animation);
    animation.finished.then(()=>running.delete(animation),()=>running.delete(animation));
    return animation;
  }
  function reveal(element,delay=0){
    animate(element,[{opacity:.15,transform:'translateY(14px)'},{opacity:1,transform:'translateY(0)'}],{delay});
  }
  const observer='IntersectionObserver' in window?new IntersectionObserver(entries=>{
    const arriving=entries.filter(entry=>entry.isIntersecting);
    arriving.forEach(({target},index)=>{
      observer.unobserve(target);revealed.add(target);reveal(target,Math.min(index,4)*45);
    });
  },{threshold:.06,rootMargin:'0px 0px -16px 0px'}):null;

  function scan(){
    document.querySelectorAll(revealSelector).forEach(element=>{
      if(!revealed.has(element))observer?.observe(element);
    });
  }
  const originalNavigate=navigate;
  navigate=function(page){
    originalNavigate(page);
    window.scrollTo({top:0,behavior:'instant'});
    reveal(document.querySelector('.heading'));
    const current=document.getElementById(page);
    let stagger=0;
    current.querySelectorAll(':scope > .stats, :scope > .control-bar, :scope > .panel, :scope > .queue-summary, :scope > .performance-summary, :scope > .settings-list').forEach(element=>{
      const bounds=element.getBoundingClientRect();
      if(bounds.top<innerHeight&&bounds.bottom>0){revealed.add(element);observer?.unobserve(element);reveal(element,45+stagger++*45)}
    });
    scan();
  };

  // Native details retain their semantics and keyboard behaviour. No height tween.
  document.addEventListener('toggle',event=>{
    if(event.target instanceof HTMLDetailsElement&&event.target.open){
      const content=event.target.querySelector(':scope > .disclosure-content');
      animate(content,[{opacity:.25,transform:'translateY(8px)'},{opacity:1,transform:'translateY(0)'}],{duration:280});
    }
  },true);

  function closeDialog(dialog){
    if(!dialog.open||dialog.dataset.closing)return;
    if(preference.matches){dialog.close();return}
    dialog.dataset.closing='true';
    const animation=animate(dialog,[{opacity:1,transform:'translateY(0) scale(1)'},{opacity:0,transform:'translateY(10px) scale(.995)'}],{duration:150,fill:'forwards'});
    if(!animation){delete dialog.dataset.closing;dialog.close();return}
    animation.finished.catch(()=>{}).then(()=>{dialog.close();animation.cancel();delete dialog.dataset.closing});
  }
  document.querySelectorAll('dialog').forEach(dialog=>{
    dialog.querySelector('.close').onclick=()=>closeDialog(dialog);
    dialog.addEventListener('cancel',event=>{event.preventDefault();closeDialog(dialog)});
  });

  // Animate only genuinely new rows, never the full table on a scoring refresh.
  let knownIds=new Set((state.events||[]).map(event=>event.id));
  const previousRender=render;
  render=function(){
    const incoming=new Set((state.events||[]).filter(event=>!knownIds.has(event.id)).map(event=>event.id));
    const firstLoad=knownIds.size===0;
    previousRender();
    knownIds=new Set(state.events.map(event=>event.id));
    if(!firstLoad)document.querySelectorAll('tr[data-id]').forEach(row=>{
      if(incoming.has(row.dataset.id))animate(row,[{opacity:.35,transform:'translateY(4px)'},{opacity:1,transform:'translateY(0)'}],{duration:300});
    });
    scan();
  };

  const signal=document.createElement('div');
  signal.className='intro-signal';signal.setAttribute('aria-hidden','true');document.querySelector('.app-header').append(signal);
  const replay=document.createElement('button');replay.className='replay-intro';replay.type='button';replay.innerHTML=icon('play')+'Replay intro animation';
  document.querySelector('.hero').parentElement.append(replay);
  function finishIntro(){clearTimeout(entranceTimer);document.body.classList.remove('intro-running');replay.disabled=false}
  function intro(){
    finishIntro();if(preference.matches)return;
    requestAnimationFrame(()=>{
      if(preference.matches)return;
      document.body.classList.add('intro-running');replay.disabled=true;
      reveal(document.querySelector('.heading'),45);
      document.querySelectorAll('.stats article').forEach((element,index)=>animate(element,[{opacity:.15},{opacity:1}],{delay:90+index*55}));
      entranceTimer=setTimeout(finishIntro,1300);
    });
  }
  replay.onclick=()=>{window.scrollTo({top:0,behavior:'instant'});intro()};
  preference.addEventListener('change',()=>{
    if(preference.matches){finishIntro();running.forEach(animation=>animation.cancel());running.clear();observer?.disconnect()}
    else scan();
  });
  scan();intro();
})();
