document.querySelectorAll(".eye").forEach(b=>b.onclick=()=>{const i=b.previousElementSibling;i.type=i.type==="password"?"text":"password"});
const tg=window.Telegram?.WebApp;if(tg){tg.ready();tg.expand();const el=document.querySelector("#tg-data");if(el)el.value=tg.initData||""}
setTimeout(()=>document.querySelectorAll(".toast").forEach(x=>x.remove()),3500);
const root=document.querySelector("#wizard");
if(root){
 const step=+root.dataset.step,form=document.querySelector("#wizard-form"),section=document.querySelector(`.step[data-step="${step}"]`);
 section.classList.add("active");const titles=["","Joylashuv","Kategoriya","Tavsif","Rasm va video","Aloqa","Tekshirish"];document.querySelector("#step-title").textContent=titles[step];
 const storageKey=`ariza-draft-${root.dataset.draft}`;
 const storageGet=()=>{try{return sessionStorage.getItem(storageKey)}catch(e){return null}};
 const storageSet=value=>{try{sessionStorage.setItem(storageKey,value)}catch(e){}};
 const storageRemove=()=>{try{sessionStorage.removeItem(storageKey)}catch(e){}};
 let data={};try{data=JSON.parse(document.querySelector("#draft-data").textContent)||{};const cached=JSON.parse(storageGet()||"null");if(cached)data={...data,...cached}}catch(e){}
 const field=(n)=>form.elements[n],set=(n,v)=>{const e=field(n);if(!e||v==null)return;if(e.type==="file")return;if(e.type==="checkbox")e.checked=!!v;else if(typeof RadioNodeList!=="undefined"&&e instanceof RadioNodeList){[...e].forEach(x=>x.checked=x.value===v)}else if(typeof e.length==="number"&&!e.tagName){[...e].forEach(x=>x.checked=x.value===v)}else e.value=v};
 Object.entries(data).forEach(([k,v])=>{try{set(k,v)}catch(e){}});
 let timer;const serialize=()=>{const out={...data};section.querySelectorAll("[name]").forEach(input=>{if(!input.name||input.type==="file")return;if(input.type==="checkbox"){out[input.name]=input.checked;return}if(input.type==="radio"){if(input.checked)out[input.name]=input.value;return}out[input.name]=input.value});return out};
 const save=async(show=false,keepalive=false)=>{data=serialize();if(data.neighborhood_name)data.neighborhood_name=data.neighborhood_name.trim().replace(/\s+/g," ");storageSet(JSON.stringify(data));try{const r=await fetch(root.dataset.save,{method:"POST",keepalive,headers:{"X-CSRFToken":window.CSRF_TOKEN,"Content-Type":"application/json"},body:JSON.stringify({current_step:step,form_data:data})});if(r.ok)storageRemove();if(show&&r.ok){const b=document.querySelector("#manual-save");b.textContent="✓ Saqlandi";setTimeout(()=>b.textContent="Xomaki saqlash",1600)}return r.ok}catch(e){return false}};
 form.addEventListener("input",()=>{clearTimeout(timer);timer=setTimeout(()=>save(),700)});document.querySelector("#manual-save").onclick=()=>save(true);
 const loadOptions=async(type,id,target,selected)=>{if(!id)return;const r=await fetch(`/api/location-options/?${type}=${id}`),j=await r.json();target.innerHTML='<option value="">Tanlang</option>'+j.items.map(x=>`<option value="${x.id}">${x.name}</option>`).join("");if(selected)target.value=selected};
 const region=field("region"),district=field("district");
 region.onchange=()=>loadOptions("region",region.value,district);
 if(data.region)loadOptions("region",data.region,district,data.district);
 const catScript=document.querySelector("#category-data");let cats=[];if(catScript){cats=JSON.parse(catScript.textContent).categories;const selectCat=id=>{field("main_category").value=id;field("subcategory").value="";document.querySelectorAll(".category-card").forEach(x=>x.classList.toggle("selected",x.dataset.category===id));const c=cats.find(x=>x.id===id),box=document.querySelector("#subcategories");box.innerHTML=(c?.subs||[]).map(s=>`<button type="button" class="chip" data-sub="${s.id}">${s.name}</button>`).join("");document.querySelector("#subheading").classList.toggle("hidden",!c?.subs.length);box.querySelectorAll(".chip").forEach(b=>b.onclick=()=>{field("subcategory").value=b.dataset.sub;box.querySelectorAll(".chip").forEach(x=>x.classList.toggle("selected",x===b));save()})};document.querySelectorAll("[data-category]").forEach(b=>b.onclick=()=>selectCat(b.dataset.category));document.querySelector("#show-other").onclick=()=>document.querySelector("#other-box").classList.toggle("hidden");if(data.main_category){selectCat(String(data.main_category));setTimeout(()=>{field("subcategory").value=data.subcategory||"";document.querySelectorAll(".chip").forEach(x=>x.classList.toggle("selected",x.dataset.sub===String(data.subcategory)))},0)}}
 document.querySelectorAll("[data-choice]").forEach(b=>{b.onclick=()=>{field("urgency").value=b.dataset.choice;document.querySelectorAll("[data-choice]").forEach(x=>x.classList.toggle("selected",x===b));save()};b.classList.toggle("selected",b.dataset.choice===(data.urgency||"normal"))});
 document.querySelectorAll("[maxlength]").forEach(x=>{const c=x.parentElement.querySelector(".counter");if(!c)return;const upd=()=>c.textContent=`${x.value.length} / ${x.maxLength}`;x.addEventListener("input",upd);upd()});
 const geo=document.querySelector("#geolocate");if(geo)geo.onclick=()=>navigator.geolocation?.getCurrentPosition(p=>{field("latitude").value=p.coords.latitude.toFixed(6);field("longitude").value=p.coords.longitude.toFixed(6);document.querySelector("#map-note").textContent=`Tanlandi: ${field("latitude").value}, ${field("longitude").value}`;save()},()=>alert("Joylashuv ruxsati berilmadi."));
 document.querySelectorAll('.upload-grid input[type="file"]').forEach(inp=>inp.onchange=async()=>{for(const f of inp.files){const fd=new FormData();fd.append("file",f);const box=document.querySelector("#previews"),row=document.createElement("div");row.className="draft-card";row.textContent=`${f.name} — yuklanmoqda...`;box.append(row);const r=await fetch(`/api/drafts/${root.dataset.draft}/upload/`,{method:"POST",headers:{"X-CSRFToken":window.CSRF_TOKEN},body:fd}),j=await r.json();row.textContent=r.ok?`${f.name} — ✓`:j.error;if(r.ok){const del=document.createElement("button");del.type="button";del.className="link danger";del.textContent="O‘chirish";del.onclick=async()=>{await fetch(`/api/drafts/${root.dataset.draft}/files/${j.id}/delete/`,{method:"POST",headers:{"X-CSRFToken":window.CSRF_TOKEN}});row.remove()};row.append(del)}}});
 const names=()=>({region:region?.selectedOptions[0]?.text,district:district?.selectedOptions[0]?.text,category:cats.find(x=>x.id===String(field("main_category")?.value))?.name,subcategory:cats.reduce((all,x)=>all.concat(x.subs||[]),[]).find(x=>x.id===String(field("subcategory")?.value))?.name});
 const escapeHtml=value=>String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[char]));
 const summary=()=>{const d=serialize(),n=names(),box=document.querySelector("#summary");if(box)box.innerHTML=[["Joylashuv",`${n.region||""}, ${n.district||""}, ${d.neighborhood_name||""}, ${d.street||""}, ${d.house||""}`,1],["Kategoriya",`${n.category||""} → ${n.subcategory||""}`,2],["Tavsif",`${d.title||""} — ${(d.description||"").slice(0,180)}`,3],["Fayllar","Ilova qilingan fayllar",4],["Aloqa",`${d.preferred_contact_method||"telegram"}`,5]].map(x=>`<div><h4>${escapeHtml(x[0])}</h4><p>${escapeHtml(x[1])}</p><a href="/drafts/${root.dataset.draft}/step/${x[2]}/">✎</a></div>`).join("")};if(step===6)summary();
 const valid=()=>{const d=serialize();if(step===1){const name=(d.neighborhood_name||"").trim();return ["region","district","street","house"].every(k=>d[k])&&name.length>=2&&name.length<=150}if(step===2)return d.main_category&&d.subcategory;if(step===3)return d.title?.trim().length>=5&&d.description?.trim().length>=20&&d.urgency;if(step===5)return d.consent;if(step===6)return d.confirm;return true};
 const nextButton=document.querySelector("#next");
 form.addEventListener("submit",event=>{
   if(!valid()){
     event.preventDefault();
     if(step===1){
       const name=(field("neighborhood_name").value||"").trim(),error=document.querySelector('[data-error-for="neighborhood_name"]');
       if(!name)error.textContent="Mahalla / MFY nomini kiritish majburiy.";
       else if(name.length<2)error.textContent="Mahalla / MFY nomi kamida 2 ta belgidan iborat bo‘lishi kerak.";
       else if(name.length>150)error.textContent="Mahalla / MFY nomi 150 ta belgidan oshmasligi kerak.";
       else error.textContent="";
     }
     alert("Majburiy maydonlarni to‘g‘ri to‘ldiring.");
     return;
   }
   clearTimeout(timer);
   storageSet(JSON.stringify(serialize()));
   nextButton.disabled=true;
   nextButton.textContent=step===6?"Yuborilmoqda...":"Saqlanmoqda...";
 });
 if(tg?.BackButton){tg.BackButton.show();tg.BackButton.onClick(()=>history.back())}
}
