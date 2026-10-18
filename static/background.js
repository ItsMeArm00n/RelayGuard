/* Composited decorative parallax; UI content never moves with the pointer. */
(()=>{
  const background=document.createElement('div');background.className='architectural-backdrop';background.setAttribute('aria-hidden','true');
  const art=document.createElement('div');art.className='architectural-backdrop-art';
  const float=document.createElement('div');float.className='architectural-backdrop-float';float.append(art);background.append(float);document.body.prepend(background);
  const left=document.createElement('div');left.className='architectural-backdrop architectural-backdrop--left';left.setAttribute('aria-hidden','true');
  const mirror=document.createElement('div');mirror.className='architectural-backdrop-mirror';mirror.append(float.cloneNode(true));left.append(mirror);document.body.prepend(left);
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const fine=matchMedia('(hover: hover) and (pointer: fine)');
  let width=innerWidth,height=innerHeight,frame=0,x=0,y=0,paused=false;
  const toggle=document.createElement('button');toggle.type='button';toggle.className='replay-intro';toggle.style.marginLeft='8px';
  const about=document.querySelector('.hero').parentElement;about.append(toggle);
  function syncMotion(){
    document.body.classList.toggle('background-motion-paused',paused);
    toggle.disabled=reduced.matches;toggle.setAttribute('aria-pressed',String(paused));
    toggle.textContent=reduced.matches?'Background animation disabled':paused?'Resume background animation':'Pause background animation';
  }
  function reset(){cancelAnimationFrame(frame);frame=0;background.style.transform='translate3d(0,0,0)';left.style.transform='translate3d(0,0,0)'}
  document.addEventListener('pointermove',event=>{
    if(paused||reduced.matches||!fine.matches||document.hidden)return;
    x=(event.clientX/width-.5)*12;y=(event.clientY/height-.5)*8;
    if(!frame)frame=requestAnimationFrame(()=>{background.style.transform=`translate3d(${x.toFixed(2)}px,${y.toFixed(2)}px,0)`;left.style.transform=`translate3d(${(-x*.65).toFixed(2)}px,${(-y*.65).toFixed(2)}px,0)`;frame=0});
  },{passive:true});
  document.documentElement.addEventListener('pointerleave',reset);
  addEventListener('resize',()=>{width=innerWidth;height=innerHeight;reset()},{passive:true});
  toggle.addEventListener('click',()=>{paused=!paused;reset();syncMotion()});
  function syncVisibility(){document.body.classList.toggle('background-motion-hidden',document.hidden);if(document.hidden)reset()}
  document.addEventListener('visibilitychange',syncVisibility);
  reduced.addEventListener('change',()=>{reset();syncMotion()});fine.addEventListener('change',reset);
  syncMotion();syncVisibility();
})();
