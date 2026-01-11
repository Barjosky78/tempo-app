const tempoDiv=document.getElementById("tempo");
const updatedDiv=document.getElementById("updated");

function dayLabel(dateStr,index){
  const d=new Date(dateStr);
  const jours=["dimanche","lundi","mardi","mercredi","jeudi","vendredi","samedi"];
  if(index===0) return "Aujourd’hui";
  if(index===1) return "Demain";
  return jours[d.getDay()].charAt(0).toUpperCase()+jours[d.getDay()].slice(1);
}

function sourceIcons(s){
  if(!s) return "";
  let icons="";
  if(s.reel) icons+="⚡ ";
  if(s.meteo) icons+="🌡️ ";
  if(s.rte) icons+="🔌 ";
  if(s.historique) icons+="📊 ";
  return `<div class="sources">${icons}</div>`;
}

fetch("meta.json?v="+Date.now())
.then(r=>r.json())
.then(m=>{
  updatedDiv.textContent="Dernière mise à jour : "+new Date(m.updatedAt).toLocaleString("fr-FR");
});

fetch("tempo.json?v="+Date.now())
.then(r=>r.json())
.then(days=>{
  tempoDiv.innerHTML="";
  days.forEach((d,i)=>{
    const c=document.createElement("div");
    c.className="day "+d.couleur;
    c.innerHTML=`
      <strong>${dayLabel(d.date,i)}</strong><br>
      <span class="date">${d.date}</span><br><br>
      <b>${d.couleur.toUpperCase()}</b>
      ${d.estimated?`<div class="tag">Estimation météo</div>`:""}
      <br><br>
      🔴 ${d.probabilites.rouge}%<br>
      ⚪ ${d.probabilites.blanc}%<br>
      🔵 ${d.probabilites.bleu}%
      ${sourceIcons(d.sources)}
    `;
    tempoDiv.appendChild(c);
  });
});
