/* Executed during Docker build with installed TypeScript; no Apple account needed. */
'use strict';
const fs=require('node:fs');const vm=require('node:vm');const assert=require('node:assert/strict');
const ts=require('/web/node_modules/typescript');
function load(file) {
  const compiled=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022},reportDiagnostics:true});
  if(compiled.diagnostics?.some(d=>d.category===ts.DiagnosticCategory.Error)) throw new Error(`Invalid test module ${file}`);
  const module={exports:{}};
  vm.runInNewContext(compiled.outputText,{module,exports:module.exports,Error,JSON,console},{filename:file});
  return module.exports;
}
const flow=load('/web/src/lib/ha_config_flow.ts');const safe=load('/web/src/lib/ha_safe_error.ts');
const question={Name:'config_2fa',Required:true,Help:'Enter the code'};
(async()=>{
  let calls=[];let answers=['','123456'];
  await flow.runICloudConfiguration(async(path,body)=>{
    calls.push({path,body});return calls.length===1 ? {State:'2fa_do',Option:question} : {State:''};
  },async()=>answers.shift(),'test',{apple_id:'test@example.invalid',password:'TEST_ONLY_PASSWORD',cookies:'STALE_COOKIE'});
  assert.equal(calls.length,2,'Blank code must NOT reach rclone');
  assert.equal(calls[0].body.opt.nonInteractive,true);assert.equal(calls[0].body.opt.obscure,true);
  assert.equal(calls[0].body.parameters.cookies,undefined);
  assert.equal(calls[1].body.opt.state,'2fa_do');assert.equal(calls[1].body.opt.result,'123456');
  assert.equal(JSON.stringify(calls[1].body.parameters),'{}','Password not resent on continuation');
  console.log('PASS: push MFA, blank-code prevention, exact state, password obscuring and no password resend');
  calls=[];answers=['sms','7_sms','654321'];
  await flow.runICloudConfiguration(async(path,body)=>{
    calls.push({path,body});
    return [{State:'2fa_do',Option:question},
      {State:'2fa_sms_select',Option:{Name:'config_2fa_phone',Exclusive:true,Examples:[{Value:'7_sms',Help:'Phone'}]}},
      {State:'2fa_sms_7_sms',Option:{Name:'config_2fa_sms',Required:true}},
      {State:''}][calls.length-1];
  },async()=>answers.shift(),'test',{password:'TEST_ONLY_PASSWORD'});
  assert.equal(calls[1].body.opt.result,'sms');assert.equal(calls[3].body.opt.state,'2fa_sms_7_sms');
  console.log('PASS: SMS fallback and phone-selection continuation');
  calls=[];answers=['111111','222222'];let first=true;
  await flow.runICloudConfiguration(async(path,body)=>{
    calls.push({path,body});if(calls.length===1)return {State:'2fa_do',Option:question};
    if(first){first=false;throw new flow.SetupError('Code rejected','MFA_INVALID');}return {State:''};
  },async()=>answers.shift(),'test',{});
  assert.equal(calls.length,3);assert.equal(calls[2].body.opt.state,'2fa_do');
  console.log('PASS: incorrect code retry preserves server state');
  let cancelled=false;
  try{await flow.runICloudConfiguration(async()=>({State:'2fa_do',Option:question}),async()=>null,'test',{});}
  catch(e){cancelled=e.code==='CANCELLED';}assert.ok(cancelled);
  console.log('PASS: cancellation is not reported as configuration success');
  calls=[];
  await flow.runICloudConfiguration(async(path,body)=>{calls.push({path,body});return {State:''};},async()=>null,'test',{},true);
  assert.equal(calls[0].path,'/config/update','Existing remote is not deleted/recreated');
  const secret='TEST_ONLY_PASSWORD';
  for(const value of [{error:'unknown state authenticate',input:{parameters:secret}},
      JSON.stringify({error:'failed '+secret,input:{password:secret}}),'Backend echoed '+secret]) {
    assert.ok(!safe.safeRcloneError(value).includes(secret));
  }
  console.log('PASS: frontend rejects raw/nested/JSON-string secret-containing error data');
  // Type-check our complete helper modules with a minimal typed store stub.
  fs.writeFileSync('/patch/store_stub.d.ts','export declare const useStore: { getState(): {url: string} };\n');
  const program=ts.createProgram(['/web/src/lib/ha_config_flow.ts','/web/src/lib/ha_safe_error.ts','/web/src/lib/ha_remote_setup.ts','/web/src/ha-ingress.d.ts'],{
    noEmit:true,strict:true,skipLibCheck:true,erasableSyntaxOnly:true,noUnusedLocals:true,noUnusedParameters:true,target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext,
    moduleResolution:ts.ModuleResolutionKind.Bundler,
    paths:{'@/lib/store':['/patch/store_stub.d.ts']},
  });
  const diagnostics=ts.getPreEmitDiagnostics(program);
  if(diagnostics.length){console.error(ts.formatDiagnosticsWithColorAndContext(diagnostics,{getCurrentDirectory:()=>'/web',getCanonicalFileName:f=>f,getNewLine:()=> '\n'}));process.exitCode=1;return;}
  console.log('PASS: helper-module TypeScript typecheck');
})().catch(error=>{console.error(error);process.exitCode=1;});
