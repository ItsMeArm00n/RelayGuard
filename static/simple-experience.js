/* Keep data renderers intact; present their results one layer at a time. */
const simpleRender=render;
render=function(){simpleRender();paymentToggles.forEach(([wrap,button])=>syncRowsToggle(wrap,button))};
Object.assign(pageNames,{overview:'Payments',alerts:'Review queue',performance:'Model results',setup:'Settings'});
Object.assign(descriptions,{overview:'Monitor payments and review what needs attention.',alerts:'Open a flagged payment to understand it and record a decision.',performance:'The measured results behind the current model.',setup:'Choose what you want to manage.'});
document.querySelector('[data-page="overview"] span').textContent='Payments';
document.querySelector('[data-page="performance"] span').textContent='Model';
document.querySelector('[data-page="setup"] span').textContent='Settings';
const detailedPayment=details;
details=function(id){
  detailedPayment(id);const root=$('#detail-content');const r=selected;if(!r)return;
  const brief=document.createElement('p');brief.className='payment-brief';brief.textContent=`${r.amount.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})} · ${r.type}`;root.querySelector('.detail-heading').after(brief);
  const why=disclosure('Why this result?',[root.querySelector('#why-score')]);
  const context=disclosure('Payment details & observed context',[root.querySelector('.detail-grid'),root.querySelector('.context-coverage'),root.querySelector('.context-section')]);
  root.querySelector('.review-section').before(why,context);
};
// The breadcrumb remains available for existing navigation without visual clutter.
navigate('overview');if(state.source)render();
