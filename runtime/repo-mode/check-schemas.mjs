import {readFileSync} from 'node:fs';
const read=name=>JSON.parse(readFileSync(new URL(name,import.meta.url),'utf8'));
const canonical=x=>Array.isArray(x)?x.map(canonical):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,canonical(x[k])])):x;
const expected=read('./expected-schemas.json'),actual=read('./linux-tools.json');
const mismatched=expected.filter(e=>JSON.stringify(canonical(e.inputSchema))!==JSON.stringify(canonical(actual.find(a=>a.name===e.name)?.inputSchema))).map(e=>e.name);
console.log(JSON.stringify({expected:expected.length,actual:actual.length,matched:expected.length-mismatched.length,mismatched}));
if(mismatched.length)process.exitCode=1;
