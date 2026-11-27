const WATCH = {
 "BHP.AX":["BHP","BHP Group"],"RIO.AX":["RIO","Rio Tinto"],"FMG.AX":["FMG","Fortescue"],
 "CBA.AX":["CBA","Commonwealth Bank"],"NAB.AX":["NAB","National Australia Bank"],"WBC.AX":["WBC","Westpac"],"ANZ.AX":["ANZ"],"MQG.AX":["MQG","Macquarie"],
 "CSL.AX":["CSL"],"XRO.AX":["Xero"],"REA.AX":["REA Group"],"GMG.AX":["Goodman Group"],"TCL.AX":["Transurban"],"STO.AX":["Santos"],"WDS.AX":["Woodside"],"PLS.AX":["Pilbara Minerals"],"MIN.AX":["Mineral Resources"],
 "AAPL":["Apple"],"MSFT":["Microsoft"],"NVDA":["Nvidia"],"AMZN":["Amazon"],"GOOGL":["Google","Alphabet"],"META":["Meta"],"TSLA":["Tesla"],"AMD":["AMD"],"AVGO":["Broadcom"],"ORCL":["Oracle"],"XOM":["Exxon"]
};
const CATEGORIES = {
 earnings:["earnings","results","profit","revenue","quarterly","half-year","full-year"],
 guidance:["guidance","outlook","forecast","expects","downgrade","upgrade"],
 contracts:["contract","agreement","deal","tender","award","partnership","order"],
 corporate:["acquisition","merger","takeover","buyback","dividend","capital raising"],
 regulatory:["regulator","regulatory","court","lawsuit","investigation","approval","licence","license"],
 macro:["rba","reserve bank","inflation","cpi","rates","interest rate","fed","federal reserve","bond yield"],
 commodities:["iron ore","lithium","gold","oil","copper","coal","gas","commodity"],
 analyst:["broker","analyst","price target","rating","research note"],
 risk:["warning","halt","recall","breach","fraud","default","restructuring"]
};
function decode(s=""){return s.replace(/<!\\[CDATA\\[|\\]\\]>/g,"").replace(/&amp;/g,"&").replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/&quot;/g,'"').replace(/&#39;/g,"'").trim();}
function tag(block, name){const m=block.match(new RegExp("<"+name+"(?:\\s[^>]*)?>([\\s\\S]*?)</"+name+">","i"));return m?decode(m[1]):"";}
function enrich(item){
 const text=(item.title+" "+item.source).toLowerCase();
 const categories=Object.entries(CATEGORIES).filter((entry)=>entry[1].some(w=>text.includes(w))).map(entry=>entry[0]);
 const matches=Object.entries(WATCH).filter(entry=>entry[1].some(term=>text.includes(term.toLowerCase()))).map(entry=>entry[0]);
 return {...item,categories,matchedSymbols:matches,classification:categories.length?"keyword match":"unclassified",relevance:matches.length?"ticker/entity match":categories.length?"topic match":"general"};
}
export async function onRequestGet({request}){
 const url=new URL(request.url);const q=url.searchParams.get("q")||"ASX Australia markets OR US stocks OR RBA";
 const rss="https://news.google.com/rss/search?q="+encodeURIComponent(q)+"&hl=en-AU&gl=AU&ceid=AU:en";
 try{
  const response=await fetch(rss,{headers:{"User-Agent":"MarketMind/1.0"}});
  if(!response.ok)return Response.json({ok:false,error:"News upstream unavailable",items:[]},{status:502});
  const xml=await response.text();
  const items=[...xml.matchAll(/<item>([\\s\\S]*?)<\\/item>/g)].slice(0,20).map(m=>{const b=m[1];return{title:tag(b,"title"),link:tag(b,"link"),pubDate:tag(b,"pubDate"),source:tag(b,"source")};}).filter(x=>x.title).map(enrich);
  return Response.json({ok:true,updatedAt:new Date().toISOString(),query:q,provider:"Google News RSS",classification:"Heuristic keyword/entity matches; not verified",items},{headers:{"Cache-Control":"public, max-age=120"}});
 }catch(error){return Response.json({ok:false,error:String(error),items:[]},{status:502});}
}
