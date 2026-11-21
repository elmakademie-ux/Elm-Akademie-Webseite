const D=window.ELM_DATA,$=s=>document.querySelector(s),main=$('#main');
const store={get(k,d){try{return JSON.parse(localStorage.getItem('elm_'+k))??d}catch{return d}},set(k,v){try{localStorage.setItem('elm_'+k,JSON.stringify(v))}catch{}}};
const esc=s=>s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function say(t){if(!('speechSynthesis' in window))return;speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(t.replace(/\*/g,''));u.lang='de-DE';u.rate=.85;speechSynthesis.speak(u)}
window.say=say;
const art=w=>w.split(' ')[0],noun=w=>w.split(' ').slice(1).join(' ');
const shuffle=a=>{a=[...a];for(let i=a.length-1;i>0;i--){const j=Math.random()*(i+1)|0;[a[i],a[j]]=[a[j],a[i]]}return a};
const hi=t=>{let h=esc(t);const rx=l=>new RegExp('(^|[^\\p{L}])('+l.join('|')+')(?=[^\\p{L}]|$)','giu');
 h=h.replace(rx(D.konnektoren),'$1<span class=kon>$2</span>');return h.replace(rx(D.modalverben),'$1<span class=mod>$2</span>')};
const stats=()=>store.get('stats',{xp:0,mails:[],quiz:{r:0,n:0}});
const addXp=n=>{const s=stats();s.xp+=n;store.set('stats',s)};

const V={
home(){const s=stats();return `<div class=card><div class=m>Dein Fortschritt</div><div class=big>${s.xp} XP</div>
 <div class=m>${s.mails.length}/15 Muster-E-Mails gelesen · Quiz: ${s.quiz.r}/${s.quiz.n} richtig</div>
 <div class=bar><i style="width:${s.mails.length/15*100}%"></i></div></div>
 <a class="card tile" href="#/mail"><b>✉️ DTZ B1 – Muster-E-Mails</b><span>5 Aufgaben · 15 Beispiele · Konnektoren &amp; Modalverben</span></a>
 <a class="card tile" href="#/wort"><b>📚 Wortschatz „Meine Wohnung“</b><span>Karteikarten &amp; Artikel-Quiz (der · die · das)</span></a>
 <a class="card tile" href="#/tag"><b>⏰ Mein Tagesablauf</b><span>Uhrzeiten &amp; trennbare Verben</span></a>
 <p class=m style="text-align:center">Folge der ELM Akademie für neue Lernvideos!<br>Die Mustertexte sind Übungshilfen, keine offiziellen Prüfungslösungen.</p>`},

mail(a){ // a: "", "1".., "1-2"
 if(a&&a.includes('-')){const[t,b]=a.split('-'),e=D.emails.find(e=>e.aufgabe==t&&e.beispiel==b),A=D.aufgaben[t],st=stats();
  if(!st.mails.includes(a)){st.mails.push(a);st.xp+=10;store.set('stats',st)}
  const pc=i=>i==null?'pn':'p'+i;
  return `<a href="#/mail/${t}">← Aufgabe ${t}</a><div class=card><b>Aufgabe ${t}: ${A.thema}</b><p>${A.text}</p>
  ${A.punkte.map((p,i)=>`<div class="pt p${i}">${i+1}. ${p}</div>`).join('')}</div>
  <div class=row><button onclick="say(mailText(${D.emails.indexOf(e)}))">🔊 Vorlesen</button><button class=alt onclick="document.getElementById('em').classList.toggle('hide')">👁 Text verdecken</button></div>
  <div class=card id=em><div class=m>Betreff: <b>${e.betreff}</b></div><p>${e.anrede}</p>
  ${e.absaetze.map(([x,p])=>`<div class="para ${pc(p)}"><small>${p==null?'':(p+1)+'. '+A.punkte[p]}</small><span>${hi(x)}</span></div>`).join('')}
  <p>${e.gruss},<br>${e.name}</p></div>
  <p class=m><span class=kon>Konnektoren</span> · <span class=mod>Modalverben</span></p>`}
 if(a){const A=D.aufgaben[a];return `<a href="#/mail">← Alle Aufgaben</a><div class=card><b>Aufgabe ${a}: ${A.thema}</b><p>${A.text}</p>${A.punkte.map((p,i)=>`<div class="pt p${i}">${i+1}. ${p}</div>`).join('')}</div>
  ${D.emails.filter(e=>e.aufgabe==a).map(e=>`<a class="card tile" href="#/mail/${a}-${e.beispiel}"><b>Beispiel ${e.beispiel}</b><span>${e.betreff}${stats().mails.includes(a+'-'+e.beispiel)?' ✅':''}</span></a>`).join('')}`}
 return `<p class=m>Wähle eine Aufgabe:</p>`+Object.entries(D.aufgaben).map(([k,A])=>`<a class="card tile" href="#/mail/${k}"><b>Aufgabe ${k}: ${A.thema}</b><span>${A.text}</span></a>`).join('')+
 `<div class=card><b>Konnektoren</b><p class=kon>${D.konnektoren.join(' · ')}</p><b>Modalverben</b><p class=mod>${D.modalverben.join(' · ')}</p></div>`},

wort(a){
 if(a==='karten')return cards();if(a==='quiz')return quiz();
 return `<a class="card tile" href="#/wort/karten"><b>🃏 Karteikarten</b><span>${D.vokabeln.length} Wörter · Aussprache anhören</span></a>
 <a class="card tile" href="#/wort/quiz"><b>🎯 Artikel-Quiz</b><span>der, die oder das?</span></a>
 <div class=card><b>Alle Wörter</b><p>${D.vokabeln.map(w=>`<div onclick="say('${w}')" style="cursor:pointer"><span class=${art(w)}>${art(w)}</span> ${noun(w)} 🔊</div>`).join('')}</p></div>
 <div class=card><b>Sätze</b>${D.wohnung_szenen.map(s=>s.saetze.map(x=>`<div onclick="say('${x}')" style="cursor:pointer">🔊 ${x}</div>`).join('')).join('')}</div>`},

tag(){return `<p class=m>Tippe auf einen Satz zum Anhören.</p>`+D.tag.map(s=>`<div class=card onclick="say('${s.satz.replace(/'/g,'’')}')" style="cursor:pointer"><span class=big style="font-size:32px">${s.zeit}</span> <span class=m>${s.sprech}</span>
 <div>${esc(s.satz).replace(/\*(.+?)\*/g,'<b class=mod>$1</b>')} 🔊</div><div class=m>Verb: ${s.verb}</div></div>`).join('')}
};
window.mailText=i=>{const e=D.emails[i];return [e.anrede,...e.absaetze.map(a=>a[0]),e.gruss,e.name].join(' ')};

let deck=[],di=0,flip=false;
function cards(){if(!deck.length){deck=shuffle(D.vokabeln);di=0}const w=deck[di];
 return `<a href="#/wort">← Wörter</a><div class=m style="text-align:center">${di+1}/${deck.length}</div><div class="card fc" onclick="flip=!flip;sayIf();route(1)">
 ${flip?`<span class=${art(w)}>${art(w)}</span> ${noun(w)}`:`${noun(w)}<span class=m>Artikel? Tippen zum Umdrehen</span>`}</div>
 <div class=row><button class=alt onclick="di=(di-1+deck.length)%deck.length;flip=false;route(1)">←</button><button onclick="say('${w}')">🔊</button><button onclick="di=(di+1)%deck.length;flip=false;route(1)">→</button></div>`}
window.sayIf=()=>{if(flip)say(deck[di])};

let q=null;
function quiz(){if(!q||q.i>=q.l.length)q=q&&q.i>=q.l.length?q:{l:shuffle(D.vokabeln).slice(0,10),i:0,r:0,a:null};
 if(q.i>=q.l.length){const r=q.r;q=null;return `<div class=card style="text-align:center"><div class=big>${r}/10</div><p>${r>=8?'Super! 🎉':'Weiter üben! 💪'}</p><button onclick="route(1)">Nochmal</button> <a class="btn alt" href="#/wort">Zurück</a></div>`}
 const w=q.l[q.i];return `<a href="#/wort">← Wörter</a><div class=bar><i style="width:${q.i*10}%"></i></div>
 <div class="card fc">${noun(w)}${q.a?`<div style="font-size:20px" class=${art(w)}>${q.a==art(w)?'✅ Richtig! ':'❌ '}${w}</div>`:''}</div>
 ${q.a?`<button onclick="say('${w}');q.i++;q.a=null;route(1)" style="width:100%">Weiter →</button>`:
 `<div class=row>${['der','die','das'].map(x=>`<button class=${x} style="background:var(--${x})" onclick="ans('${x}')">${x}</button>`).join('')}</div>`}`}
window.ans=x=>{const w=q.l[q.i];q.a=x;const s=stats();s.quiz.n++;if(x==art(w)){q.r++;s.quiz.r++;s.xp+=5}store.set('stats',s);route(1)};

function route(keep){const[,p='',a='']=location.hash.slice(1).split('/');const k=p||'home';
 if(!keep){flip=false;if(k!='wort')q=null}
 main.innerHTML=(V[k]||V.home)(a);scrollTo(0,keep?scrollY:0);
 document.querySelectorAll('nav a').forEach(n=>n.classList.toggle('on',n.dataset.t==k))}
window.route=route;addEventListener('hashchange',()=>route());route();
if('serviceWorker' in navigator&&location.protocol.startsWith('http'))navigator.serviceWorker.register('sw.js').catch(()=>{});
