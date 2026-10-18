/* Progressive disclosure. Move existing content without removing its controls. */
function disclosure(title,nodes,className=''){
  const box=document.createElement('details');box.className='disclosure '+className;
  const summary=document.createElement('summary');summary.textContent=title;box.append(summary);
  const inner=document.createElement('div');inner.className='disclosure-content';nodes.forEach(n=>{if(n)inner.append(n)});box.append(inner);return box;
}
const pick=s=>document.querySelector(s);
const sidebar=pick('.sidebar');
const brand=pick('.brand'),nav=pick('nav'),account=pick('.workspace');
const appHeader=document.createElement('header');appHeader.className='app-header';
appHeader.append(brand,nav);const demo=document.createElement('span');demo.className='demo-indicator';demo.textContent='Demo workspace';appHeader.append(demo);document.body.insertBefore(appHeader,sidebar);
const retainedHeader=pick('.topbar');retainedHeader.remove();
const about=disclosure('About this workspace',[pick('.hero'),pick('.sidebar-note')]);
const source=disclosure('Data source, exports & runtime',[pick('.source-banner'),account,pick('.aside-bottom')]);
source.querySelector('.disclosure-content').append(retainedHeader,pick('.nav-label'));sidebar.remove();
const overview=pick('#overview');const stats=pick('.stats');
const extraStats=disclosure('Scoring performance',[stats.querySelector('article:last-child')]);
const metricHelp=document.createElement('div');metricHelp.className='metric-help';stats.querySelectorAll('article').forEach(article=>{const line=document.createElement('p');const title=document.createElement('strong');title.textContent=article.querySelector('.stat-top span').textContent+': ';line.append(title,article.querySelector('small'));metricHelp.append(line)});about.querySelector('.disclosure-content').append(metricHelp);
const controlBar=document.createElement('div');controlBar.className='control-bar';
const guide=document.createElement('div');guide.innerHTML='<strong>Payment monitor</strong><span>Start the demo feed, or test a payment.</span>';
const actions=document.createElement('div');actions.className='control-actions';actions.append(pick('#play'),pick('#manual-open'));controlBar.append(guide,actions);stats.after(controlBar);
const activity=pick('.activity-grid');activity.remove();
const activityDetails=document.createElement('section');activityDetails.className='panel live-activity';activityDetails.id='live-activity';activityDetails.setAttribute('aria-labelledby','live-activity-title');
const activityHeading=document.createElement('header');activityHeading.className='live-activity-heading';activityHeading.innerHTML='<h2 id="live-activity-title">Activity & replay details</h2>';
const activityBody=document.createElement('div');activityBody.className='live-activity-body';activityBody.append(activity,extraStats);activityDetails.append(activityHeading,activityBody);activityHeading.append(controlBar);overview.prepend(activityDetails);
const feed=pick('.feed-panel');feed.after(about,source);
const ledgerHelp=disclosure('How to use the payment list',[feed.querySelector('.panel-head p')]);feed.append(ledgerHelp);
const caption=pick('.replay-panel h2');caption.id='replay-caption';
const feedTools=pick('.feed-panel .tools');const columns=document.createElement('button');columns.className='secondary column-toggle';columns.textContent='More columns';columns.setAttribute('aria-pressed','false');columns.onclick=()=>{const more=document.body.classList.toggle('expanded-columns');columns.textContent=more?'Fewer columns':'More columns';columns.setAttribute('aria-pressed',String(more))};feedTools.append(columns);
function addRowsToggle(selector){const wrap=pick(selector);const button=document.createElement('button');button.className='rows-toggle';button.type='button';button.hidden=true;button.onclick=()=>{wrap.classList.toggle('show-all');syncRowsToggle(wrap,button)};wrap.after(button);return [wrap,button]}
function syncRowsToggle(wrap,button){const count=wrap.querySelectorAll('tbody tr').length;button.hidden=count<=8;button.textContent=wrap.classList.contains('show-all')?'Show fewer payments':`Show all ${count} payments`;button.setAttribute('aria-expanded',String(wrap.classList.contains('show-all')))}
const paymentToggles=[addRowsToggle('#feed'),addRowsToggle('#alert-table')];
pick('#alerts').prepend(disclosure('About the review process',[pick('#alerts .section-intro')]));
const perf=pick('#performance');const modelPanel=perf.querySelector('.panel');
perf.append(disclosure('Evaluation details & model comparison',[modelPanel]));
const modelIntro=perf.querySelector('.section-intro');const modelHelp=disclosure('How this model is evaluated',[]);modelIntro.before(modelHelp);modelHelp.querySelector('.disclosure-content').append(modelIntro);
const settings=pick('#setup');const grid=settings.querySelector('.settings-grid');
const settingsIntro=disclosure('About these settings',[settings.querySelector('.section-intro')]);
const train=grid.querySelector('.padded'),policy=grid.querySelector('.policy-card'),reset=grid.querySelector('.reset-card');
const settingsList=document.createElement('div');settingsList.className='settings-list';settingsList.append(disclosure('Upload data & train a model',[train]),disclosure('Alert threshold',[policy]),disclosure('Reset & archived reviews',[reset]),settingsIntro);grid.replaceWith(settingsList);
const utility=document.createElement('div');utility.className='utility-links';utility.append(pick('.export-button'));source.querySelector('.disclosure-content').prepend(utility);
const note=document.createElement('p');note.className='simulation-notice';note.textContent='Simulated payments · Flags request human review.';pick('.heading').after(note);




