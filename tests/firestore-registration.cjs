const {initializeTestEnvironment,assertFails,assertSucceeds}=require('@firebase/rules-unit-testing');
const {doc,setDoc,getDoc,serverTimestamp}=require('firebase/firestore');
const fs=require('node:fs');
(async()=>{
 const env=await initializeTestEnvironment({projectId:'demo-vinnas-registration',firestore:{rules:fs.readFileSync('firestore.rules','utf8')}});
 try{
 const resident=env.authenticatedContext('resident',{email:'resident@example.com',email_verified:true}).firestore();
 const stranger=env.authenticatedContext('stranger',{email:'other@example.com',email_verified:true}).firestore();
 const anonymous=env.unauthenticatedContext().firestore();
 const claim={cpf:'52998224725',phone:'85999990000',whatsapp:true,email:'resident@example.com',createdAt:serverTimestamp()};
 await assertFails(setDoc(doc(anonymous,'registration_claims','resident'),claim));
 await assertFails(setDoc(doc(stranger,'registration_claims','resident'),claim));
 await assertSucceeds(setDoc(doc(resident,'registration_claims','resident'),claim));
 await assertFails(getDoc(doc(stranger,'registration_claims','resident')));
 await assertFails(getDoc(doc(resident,'registration_review_private','resident')));
 await assertFails(setDoc(doc(resident,'registration_decisions','resident'),{decision:'approved',unit:'302'}));
 await assertFails(setDoc(doc(resident,'registration_claims','resident'),claim));
 console.log('7 registration authorization checks passed');
 }finally{await env.cleanup();}
})().catch(e=>{console.error(e);process.exitCode=1});
