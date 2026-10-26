/* Apply HA setup/security edits with the TypeScript AST. Fail on upstream drift. */
'use strict';
const fs=require('node:fs');
const ts=require('/web/node_modules/typescript');
function rewrite(file,collect,imports) {
  const text=fs.readFileSync(file,'utf8');
  const ast=ts.createSourceFile(file,text,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
  if(ast.parseDiagnostics.length) throw new Error(`Invalid input syntax: ${file}`);
  const edits=[];collect(ast,text,edits);
  let result=text;
  for(const edit of edits.sort((a,b)=>b.start-a.start)) result=result.slice(0,edit.start)+edit.text+result.slice(edit.end);
  result=imports+'\n'+result;
  const check=ts.createSourceFile(file,result,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
  if(check.parseDiagnostics.length) throw new Error(`HA setup patch produced invalid syntax: ${file}`);
  fs.writeFileSync(file,result);console.log(`Patched setup/security: ${file}`);
}
rewrite('/web/src/pages/RemotesNew.tsx',(ast,text,edits)=>{
  let calls=0,settled=0;
  function visit(node) {
    if(ts.isAwaitExpression(node)&&ts.isCallExpression(node.expression)&&
       node.expression.expression.getText(ast)==='rclone'&&
       node.expression.arguments[0]&&ts.isStringLiteral(node.expression.arguments[0])&&
       node.expression.arguments[0].text==='/config/create') {
      edits.push({start:node.getStart(ast),end:node.getEnd(),text:'await createRemoteWithQuestions(name, type, parameters)'});calls++;
    }
    if(ts.isVariableDeclaration(node)&&node.name.getText(ast)==='createRemoteMutation'&&
       node.initializer&&ts.isCallExpression(node.initializer)) {
      const object=node.initializer.arguments[0];
      if(!object||!ts.isObjectLiteralExpression(object)) throw new Error('Unknown mutation options');
      if(object.properties.some(p=>p.name&&p.name.getText(ast)==='onSettled')) throw new Error('Unexpected upstream onSettled; review patch');
      edits.push({start:object.getStart(ast)+1,end:object.getStart(ast)+1,text:`
        onSettled: () => setConfig(previous => {
          const next = { ...previous };
          delete next.password; delete next.cookies; delete next.trust_token;
          return next;
        }),
      `});settled++;
    }
    ts.forEachChild(node,visit);
  }
  visit(ast);
  if(calls!==1||settled!==1) throw new Error('Remote setup patch no longer matches upstream');
},"import { createRemoteWithQuestions } from '@/lib/ha_remote_setup';");
rewrite('/web/src/rclone/client.ts',(ast,text,edits)=>{
  let stringify=0,constructor=0;
  function visit(node) {
    if(ts.isFunctionDeclaration(node)&&node.name?.text==='stringifyError'&&node.body) {
      edits.push({start:node.body.getStart(ast),end:node.body.getEnd(),text:'{ return safeRcloneError(error); }'});stringify++;
    }
    if(ts.isClassDeclaration(node)&&node.name?.text==='RcloneError') {
      for(const member of node.members) {
        if(ts.isConstructorDeclaration(member)&&member.body) {
          for(const statement of member.body.statements) {
            if(ts.isExpressionStatement(statement)&&ts.isCallExpression(statement.expression)&&
               statement.expression.expression.kind===ts.SyntaxKind.SuperKeyword) {
              const call=statement.expression;
              edits.push({start:call.getStart(ast),end:call.getEnd(),text:'super(safeRcloneError(message))'});constructor++;
            }
          }
        }
      }
    }
    ts.forEachChild(node,visit);
  }
  visit(ast);
  if(stringify!==1||constructor!==1) throw new Error('Error sanitization patch no longer matches upstream');
},"import { safeRcloneError } from '@/lib/ha_safe_error';");
