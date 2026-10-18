/* Decorative entrance only: no input blocking, no data or timer changes. */
(()=>{
  const header=document.querySelector('.app-header');
  const signal=document.createElement('div');signal.className='intro-signal';signal.setAttribute('aria-hidden','true');header.append(signal);
  const motion=window.matchMedia('(prefers-reduced-motion: reduce)');
  const replay=document.createElement('button');replay.className='replay-intro';replay.type='button';replay.innerHTML=icon('play')+'Replay intro animation';
  document.querySelector('.hero').parentElement.append(replay);
  let timeout;
  function finish(){clearTimeout(timeout);document.body.classList.remove('intro-running');replay.disabled=false}
  function start(){
    finish();if(motion.matches)return;
    // The next frame separates removal from addition when replaying.
    requestAnimationFrame(()=>requestAnimationFrame(()=>{
      if(motion.matches)return;
      document.body.classList.add('intro-running');replay.disabled=true;timeout=setTimeout(finish,1700);
    }));
  }
  replay.addEventListener('click',()=>{window.scrollTo({top:0,behavior:'instant'});start()});
  motion.addEventListener('change',()=>{if(motion.matches)finish()});
  start();
})();
