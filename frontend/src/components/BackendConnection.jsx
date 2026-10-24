import {useState} from 'react';
import {API,STATIC_HOST} from '../services/client';

export default function BackendConnection(){
 const[url,setUrl]=useState(API);const[busy,setBusy]=useState(false);const[error,setError]=useState('');
 async function connect(e){
  e.preventDefault();setError('');setBusy(true);
  try{
   const parsed=new URL(url.trim());
   if(!['http:','https:'].includes(parsed.protocol)||parsed.username||parsed.password||parsed.search||parsed.hash)throw Error('Enter an HTTP(S) backend URL without credentials, query parameters or fragments.');
   if(location.protocol==='https:'&&parsed.protocol!=='https:')throw Error('This HTTPS website requires an HTTPS backend URL.');
   const base=parsed.href.replace(/\/$/,'');
   const response=await fetch(base+'/health',{signal:AbortSignal.timeout(12000)});
   if(!response.ok||!response.headers.get('content-type')?.includes('application/json'))throw Error('That URL did not return a valid backend health response.');
   const data=await response.json();
   if(data.status!=='healthy'||data.service!=='WebTrace backend')throw Error('That endpoint is not a healthy WebTrace backend.');
   localStorage.setItem('webtrace-api-url',base);location.reload();
  }catch(e){setError(e.name==='TypeError'?'Unable to connect. Check the URL, HTTPS and backend CORS configuration.':e.message)}finally{setBusy(false)}
 }
 return <section className="card settings backend-settings"><h3>Testing backend connection</h3><p>{STATIC_HOST?'GitHub Pages hosts this interface. Connect an HTTPS WebTrace backend to execute browser tests and load reports.':'The website uses the backend on this origin by default. You can connect a different WebTrace backend.'}</p><form onSubmit={connect}><label htmlFor="backend-url">Backend URL</label><input id="backend-url" type="url" required value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://your-webtrace-backend.example.com"/><p className="field-note">Set CORS_ORIGINS on the backend to allow {location.origin}. This browser stores only the backend URL; do not enter an API key here.</p>{error&&<div className="alert" role="alert">{error}</div>}<div className="form-actions"><button className="button primary" disabled={busy}>{busy?'Checking backend…':'Connect backend'}</button>{localStorage.getItem('webtrace-api-url')&&<button className="button" type="button" onClick={()=>{localStorage.removeItem('webtrace-api-url');location.reload()}}>Reset connection</button>}</div></form></section>
}
