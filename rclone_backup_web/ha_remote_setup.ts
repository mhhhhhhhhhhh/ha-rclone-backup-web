import { useStore } from '@/lib/store';
import {runICloudConfiguration, SetupError, type Question} from './ha_config_flow';
import {safeRcloneError} from './ha_safe_error';

export function askConfiguration(question: Question, previousError = ''): Promise<string | null> {
  return new Promise(resolve => {
    const shade = document.createElement('div');
    shade.style.cssText = 'position:fixed;inset:0;z-index:2147483000;background:rgba(0,0,0,.65);display:flex;align-items:center;justify-content:center;padding:16px;overflow:auto';
    const form = document.createElement('form');
    form.setAttribute('role','dialog'); form.setAttribute('aria-modal','true');
    form.setAttribute('aria-labelledby','ha-rclone-mfa-title');
    form.style.cssText = 'width:100%;max-width:480px;background:#202124;color:#f5f5f5;border:1px solid #555;border-radius:16px;padding:24px;font:16px system-ui;box-shadow:0 12px 48px #0008';
    const title = document.createElement('h2'); title.id='ha-rclone-mfa-title';
    title.textContent = /2fa/.test(question.Name || '') ? 'iCloud: Zwei-Faktor-Authentifizierung' : 'rclone: Einrichtung fortsetzen';
    title.style.cssText='font-size:20px;margin:0 0 14px';
    const help = document.createElement('p'); help.textContent=question.Help || question.Name || 'Bitte beantworten';
    help.style.cssText='white-space:pre-wrap;line-height:1.5';
    const error = document.createElement('p'); error.setAttribute('role','alert');
    error.style.cssText='color:#ffb4ab;line-height:1.5'; error.textContent=previousError;
    let field: HTMLInputElement | HTMLSelectElement;
    if (question.Exclusive && question.Examples?.length) {
      const select=document.createElement('select');
      for (const example of question.Examples) {
        const option=document.createElement('option'); option.value=String(example.Value);
        option.textContent=example.Help || String(example.Value); select.append(option);
      }
      field=select;
    } else if (question.Type==='bool') {
      const select=document.createElement('select');
      for (const [value,label] of [['true','Ja'],['false','Nein']]) {
        const option=document.createElement('option'); option.value=value;option.textContent=label;select.append(option);
      }
      field=select;
    } else {
      const input=document.createElement('input');
      input.type=question.IsPassword ? 'password' : 'text';
      input.autocomplete=/2fa/.test(question.Name || '') ? 'one-time-code' : 'off';
      if (/2fa/.test(question.Name || '') && question.Name !== 'config_2fa') input.inputMode='numeric';
      input.required=Boolean(question.Required || /2fa/.test(question.Name || ''));
      field=input;
    }
    field.setAttribute('aria-label',question.Name || 'Antwort');
    field.style.cssText='width:100%;padding:12px;background:#303134;color:white;border:1px solid #888;border-radius:8px;font:inherit;margin:8px 0 16px';
    if (!question.IsPassword && !/2fa/.test(question.Name || '') && question.Default != null) field.value=String(question.Default);
    const row=document.createElement('div');row.style.cssText='display:flex;gap:12px;justify-content:flex-end';
    const cancel=document.createElement('button');cancel.type='button';cancel.textContent='Abbrechen';
    const submit=document.createElement('button');submit.type='submit';submit.textContent='Weiter';
    for (const button of [cancel,submit]) button.style.cssText='padding:10px 16px;border:1px solid #777;border-radius:8px;background:#353638;color:white;font:inherit;cursor:pointer';
    submit.style.background='#237649';row.append(cancel,submit);
    form.append(title,help,error,field,row);shade.append(form);
    const previousFocus=document.activeElement instanceof HTMLElement ? document.activeElement : null;
    let finished=false;
    const finish=(value: string | null) => {
      if (finished) return;finished=true;field.value='';shade.remove();previousFocus?.focus();resolve(value);
    };
    cancel.onclick=()=>finish(null);
    form.onsubmit=event=>{
      event.preventDefault();
      const value=field.value;
      if (/2fa/.test(question.Name || '') && !question.Exclusive &&
          !(/^\d{6}$/.test(value) || (question.Name==='config_2fa' && value.toLowerCase()==='sms'))) {
        error.textContent='Bitte gib den sechsstelligen Code ein; im ersten Schritt ist auch „sms“ möglich.';field.focus();return;
      }
      if (question.Required && !value) {error.textContent='Dieses Feld darf nicht leer sein.';return;}
      finish(value);
    };
    form.onkeydown=event=>{
      if (event.key==='Escape') {event.preventDefault();finish(null);}
      if (event.key==='Tab') {
        const focusables: HTMLElement[]=[field,cancel,submit];
        const index=focusables.indexOf(document.activeElement as HTMLElement);
        const next=event.shiftKey ? (index+focusables.length-1)%focusables.length : (index+1)%focusables.length;
        event.preventDefault();focusables[next].focus();
      }
    };
    document.body.append(shade);field.focus();
  });
}

async function request(path: string, body: Record<string,unknown>): Promise<Record<string,unknown>> {
  const base=useStore.getState().url.replace(/\/+$/,'');
  if (!base) throw new SetupError('Keine rclone-Verbindung eingerichtet.');
  const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),180000);
  try {
    const response=await fetch(base+path, {
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body),signal:controller.signal,cache:'no-store',
    });
    let payload: Record<string,unknown>={};
    try {payload=await response.json() as Record<string,unknown>;} catch { /* no raw HTML/response body in errors */ }
    if (!response.ok || payload.error) {
      throw new SetupError(safeRcloneError(payload),typeof payload.code==='string' ? payload.code : 'REQUEST_FAILED');
    }
    return payload;
  } catch (error) {
    if (error instanceof SetupError) throw error;
    throw new SetupError('Die Verbindung wurde unterbrochen oder die Anfrage hat zu lange gedauert.');
  } finally {clearTimeout(timeout);}
}

export async function createRemoteWithQuestions(name: string,type: string,parameters: Record<string,unknown>): Promise<void> {
  if (type !== 'iclouddrive') {
    await request('/config/create',{name,type,parameters,opt:{obscure:true}});return;
  }
  try {
    const list=await request('/config/listremotes',{});
    const exists=Array.isArray(list.remotes) && list.remotes.includes(name);
    if (exists) {
      const remote=await request('/config/get',{name});
      if (remote.type!=='iclouddrive') throw new SetupError('Ein Remote mit diesem Namen existiert bereits und ist kein iCloud-Remote. Wähle einen anderen Namen.');
      const answer=await askConfiguration({
        Name:'reauth_confirm',Help:'Ein iCloud-Remote mit diesem Namen existiert bereits. Möchtest du dessen Anmeldung erneuern? Vorhandene Optionen werden nicht gelöscht.',
        Exclusive:true,Default:'false',Examples:[{Value:'false',Help:'Abbrechen'},{Value:'true',Help:'iCloud erneut anmelden'}],
      });
      if (answer!=='true') throw new SetupError('Einrichtung abgebrochen.','CANCELLED');
    }
    await runICloudConfiguration(async (path, body) => {
      const out = await request(path, body);
      return {
        State: typeof out.State === 'string' ? out.State : '',
        Error: typeof out.Error === 'string' ? out.Error : '',
        Option: typeof out.Option === 'object' && out.Option !== null ? out.Option as Question : null,
      };
    },askConfiguration,name,parameters,exists);
  } finally {
    delete parameters.password;delete parameters.cookies;delete parameters.trust_token;
  }
}

export async function updateRemoteWithQuestions(name: string, parameters: Record<string, unknown>): Promise<void> {
  try {
    const current = await request('/config/get', {name});
    if (current.type !== 'iclouddrive') {
      await request('/config/update', {name, parameters});
      return;
    }
    const changes = {...parameters};
    // The edit form contains the existing obscured password. Do not obscure it twice.
    if (changes.password === current.password || changes.password === '') delete changes.password;
    delete changes.type;
    delete changes.cookies;
    delete changes.trust_token;
    delete changes._auth_session;
    await runICloudConfiguration(async (path, body) => {
      const out = await request(path, body);
      return {
        State: typeof out.State === 'string' ? out.State : '',
        Error: typeof out.Error === 'string' ? out.Error : '',
        Option: typeof out.Option === 'object' && out.Option !== null ? out.Option as Question : null,
      };
    }, askConfiguration, name, changes, true);
  } finally {
    delete parameters.password; delete parameters.cookies; delete parameters.trust_token;
  }
}
