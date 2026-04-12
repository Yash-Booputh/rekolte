import{W as s,P as r,Q as a,R as i,S as m}from"./index-GjU6wvin.js";/*!
 * (C) Ionic http://ionicframework.com - MIT License
 */const c=()=>{const t=window;t.addEventListener("statusTap",()=>{s(()=>{const n=document.elementFromPoint(t.innerWidth/2,t.innerHeight/2);if(!n)return;const e=r(n);e&&new Promise(o=>a(e,o)).then(()=>{i(async()=>{e.style.setProperty("--overflow","hidden"),await m(e,300),e.style.removeProperty("--overflow")})})})})};export{c as startStatusTap};
