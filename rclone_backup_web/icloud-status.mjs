const prefix=location.pathname.replace(/\/icloud-status\.html$/, '').replace(/\/$/,'');
const rcBase=prefix+'/rc';
const notice=document.getElementById('notice');
const dialog=document.getElementById('mfa');
let busy=false;
document.getElementById('back').href=prefix+'/';
const labels={connected:'Connected',reauth_required:'Sign-in required',auth_pending:'MFA pending',unverified:'Sign-in saved; check pending',connection_error:'Connection error',access_error:'Apple access error',unknown:'Not checked'};
async function api(path,body={}) {
  const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),240000);
  try {
    const response=await fetch(rcBase+'/ha/icloud/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal,cache:'no-store'});
    const data=await response.json();
    if(!response.ok) {
      // Display only local classifications, not any response/error text.
      const error=new Error(data.code==='MFA_INVALID' ? 'The code was not accepted. Retry or restart sign-in.' : data.code==='MFA_EMPTY' ? 'Please enter a code.' : 'The request failed. Check connectivity, or restart sign-in.');
      error.code=data.code;throw error;
    }
    return data;
  } catch(error) {
    if(error.code)throw error;
    throw new Error('Connection interrupted or request timed out.');
  } finally {clearTimeout(timeout);}
}
function date(value){return value ? new Date(value).toLocaleString() : 'Unknown (existing sign-in was not dated)';}
function show(data){
  const rows=document.getElementById('rows');rows.replaceChildren();
  if(!data.enabled){notice.textContent='Background monitoring is disabled in app options.';}
  if(!data.remotes?.length){rows.textContent='No iCloud remotes found yet. Create a remote in rclone Web, then check connections.';return;}
  for(const row of data.remotes){
    const card=document.createElement('article');card.className='card';
    const heading=document.createElement('h2');heading.textContent=row.name+' — '+(labels[row.status]||'Unknown');
    const list=document.createElement('dl');
    for(const [key,value] of [['Last check',date(row.last_check)],['Last successful check',date(row.last_success)],['Recorded sign-in',date(row.authenticated_at)],['Estimated renewal',date(row.estimated_renewal)]]){
      const term=document.createElement('dt');term.textContent=key;
      const definition=document.createElement('dd');definition.textContent=value;list.append(term,definition);
    }
    const renew=document.createElement('button');renew.textContent='Renew sign-in';renew.disabled=busy;renew.onclick=()=>reauthenticate(row.name);
    card.append(heading,list,renew);rows.append(card);
  }
}
async function refresh(){try{show(await api('status'));}catch(error){notice.textContent=error.message;}}
function ask(option,errorText=''){
  return new Promise(resolve=>{
    const host=document.getElementById('field');host.replaceChildren();
    document.getElementById('mfa-help').textContent=option.Help||option.Name||'Enter your answer';
    document.getElementById('mfa-error').textContent=errorText;
    const isCode=/2fa/.test(option.Name||'')&&!option.Exclusive;
    const field=document.createElement(option.Exclusive||option.Type==='bool'?'select':'input');
    if(field.tagName==='SELECT'){
      const examples=option.Examples?.length ? option.Examples : [{Value:'true',Help:'Yes'},{Value:'false',Help:'No'}];
      for(const example of examples){const item=document.createElement('option');item.value=String(example.Value);item.textContent=example.Help||String(example.Value);field.append(item);}
    }else{
      field.type=option.IsPassword?'password':'text';field.autocomplete=isCode?'one-time-code':'off';
      if(isCode&&option.Name!=='config_2fa')field.inputMode='numeric';
    }
    field.setAttribute('aria-label',option.Name||'Answer');host.append(field);
    const finish=value=>{field.value='';dialog.close();resolve(value);};
    document.getElementById('cancel').onclick=()=>finish(null);
    dialog.oncancel=event=>{event.preventDefault();finish(null);};
    document.getElementById('mfa-form').onsubmit=event=>{
      event.preventDefault();const value=field.value.trim();
      if((isCode&&!(/^\d{6}$/.test(value)||(option.Name==='config_2fa'&&value.toLowerCase()==='sms')))||(option.Required&&!value)){
        document.getElementById('mfa-error').textContent='Enter the six-digit code. In the first MFA step, you can also enter sms.';return;
      }
      finish(value);
    };
    dialog.showModal();field.focus();
  });
}
async function reauthenticate(name){
  if(busy)return;
  if(!confirm('Renew iCloud sign-in for '+name+'? This starts a new Apple authentication session. The remote and backup jobs will not be deleted.'))return;
  busy=true;await refresh();notice.textContent='Starting Apple sign-in…';
  try{
    let step=await api('reauth',{name});let errorText='';let tries=0;
    for(let count=0;count<24;count++){
      if(!step.State){
        if(step.Error)throw new Error('Sign-in did not finish. Restart sign-in.');
        notice.textContent='Sign-in saved. Checking the connection…';
        show(await api('check'));notice.textContent='Connection check finished. See the status below.';return;
      }
      if(!step.Option)throw new Error('No MFA question was returned. Restart sign-in.');
      const answer=await ask(step.Option,errorText||step.Error||'');
      if(answer===null){await api('cancel',{name});notice.textContent='Sign-in cancelled. The remote was kept.';return;}
      try{step=await api('reauth',{name,continue:true,state:step.State,result:answer});errorText='';tries=0;}
      catch(error){if(error.code==='MFA_INVALID'&&tries++<2){errorText=error.message;continue;}throw error;}
    }
    throw new Error('Too many sign-in steps. Restart sign-in.');
  }catch(error){notice.textContent=error.message;}
  finally{busy=false;await refresh();}
}
document.getElementById('check').onclick=async()=>{
  if(busy)return;busy=true;document.getElementById('check').disabled=true;notice.textContent='Checking connections…';
  try{show(await api('check'));notice.textContent='Connection checks complete.';}
  catch(error){notice.textContent=error.message;}
  finally{busy=false;document.getElementById('check').disabled=false;await refresh();}
};
refresh();setInterval(()=>{if(!busy)refresh();},60000);
