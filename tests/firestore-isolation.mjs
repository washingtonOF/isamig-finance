import {initializeTestEnvironment,assertFails,assertSucceeds} from '@firebase/rules-unit-testing';
import {doc,getDoc,setDoc,serverTimestamp} from 'firebase/firestore';
import {readFileSync} from 'node:fs';
const env=await initializeTestEnvironment({projectId:'demo-vinnas',firestore:{rules:readFileSync('firestore.rules','utf8')}});
try{
await env.withSecurityRulesDisabled(async c=>{
 const db=c.firestore();
 for(const [uid,unit,role,status] of [['a','102','resident','approved'],['b','103','resident','approved'],['adm','101','administrative','approved'],['rev','104','resident','revoked']]){
 await setDoc(doc(db,'users',uid),{email:uid+'@example.test',name:uid,unit,role,status});
 await setDoc(doc(db,'residents',unit),{owner:uid});
 await setDoc(doc(db,'finance_units',unit,'months','2026-11'),{paymentSchema:1,authorizedUid:uid});
 await setDoc(doc(db,'unit_notices',unit,'messages','n1'),{subject:'Teste'});
 }
 await setDoc(doc(db,'finance_admin','2026-11'),{statementSchema:2});
});
const ctx=(uid,verified=true)=>env.authenticatedContext(uid,{email:uid+'@example.test',email_verified:verified}).firestore();
const a=ctx('a'),adm=ctx('adm'),rev=ctx('rev'),anon=env.unauthenticatedContext().firestore();
const tests=[
['own resident',()=>assertSucceeds(getDoc(doc(a,'residents','102')))],
['other resident',()=>assertFails(getDoc(doc(a,'residents','103')))],
['own finance',()=>assertSucceeds(getDoc(doc(a,'finance_units','102','months','2026-11')))],
['other finance',()=>assertFails(getDoc(doc(a,'finance_units','103','months','2026-11')))],
['admin finance denied resident',()=>assertFails(getDoc(doc(a,'finance_admin','2026-11')))],
['admin finance allowed',()=>assertSucceeds(getDoc(doc(adm,'finance_admin','2026-11')))],
['financial write denied admin',()=>assertFails(setDoc(doc(adm,'finance_admin','2026-11'),{statementSchema:2}))],
['revoked denied',()=>assertFails(getDoc(doc(rev,'residents','104')))],
['anonymous denied',()=>assertFails(getDoc(doc(anon,'residents','102')))],
['unverified denied',()=>assertFails(getDoc(doc(ctx('a',false),'residents','102')))],
['own notice',()=>assertSucceeds(getDoc(doc(a,'unit_notices','102','messages','n1')))],
['other notice',()=>assertFails(getDoc(doc(a,'unit_notices','103','messages','n1')))],
['forged receipt',()=>assertFails(setDoc(doc(a,'unit_notices','102','messages','n1','receipts','b'),{uid:'b',name:'b',confirmedAt:serverTimestamp()}))],
['own receipt',()=>assertSucceeds(setDoc(doc(a,'unit_notices','102','messages','n1','receipts','a'),{uid:'a',name:'a',confirmedAt:serverTimestamp()}))],
['audit read denied',()=>assertFails(getDoc(doc(a,'portal_audit','test')))]];
for(const [name,run] of tests){await run();console.log('PASS',name);}
}finally{await env.cleanup();}
