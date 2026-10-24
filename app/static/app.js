const $ = (s) => document.querySelector(s);
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = (d) => (d ? String(d).replace('T', ' ').slice(0, 16) : '—');
const money = (v) => '₹' + Number(v || 0).toLocaleString('en-IN', {maximumFractionDigits: 2});
const today = () => new Date().toLocaleDateString('en-CA');
const dateLocal = () => {let d=new Date();return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');};
const dateTimeLocal = () => {const d=new Date();return dateLocal() + 'T' + String(d.getHours()).padStart(2,'0') + ':' + String(d.getMinutes()).padStart(2,'0');};
const status = (s) => `<span class="tag ${esc(String(s||'').toLowerCase().replace(/\s/g,'_'))}">${esc(String(s||'—').replaceAll('_',' '))}</span>`;
const person = (p) => p ? `<span class="person-cell"><span class="person-mini">${esc(p.name[0])}</span><span><b>${esc(p.name)}</b><small>${esc(p.mrn)}</small></span></span>` : '<span>—</span>';
const navGroups = [
  {title:'WORKSPACE',items:[['dashboard','Overview','◫']]},
  {title:'CLINICAL CARE',items:[['patients','Patients','♙'],['encounters','Dental encounters','▤'],['chart','Dental chart','♧'],['care-plans','Treatment plans','☷'],['appointments','Appointments','▦'],['procedures','Procedures','✚'],['imaging','Imaging / X-rays','▧'],['lab-orders','Prosthetic lab','⬡']]},
  {title:'CLINICAL RESEARCH',items:[['trials','Clinical trials','◈'],['consents','Informed consent','▣'],['screenings','Screening','◎'],['enrollments','Participants','♧'],['research-visits','Study visits / eCRF','▥'],['safety-events','AE / SAE safety','⚑']]},
  {title:'OPERATIONS',items:[['invoices','Billing','₹'],['stock','Materials stock','▤']]},
  {title:'ADMINISTRATION',items:[['users','User permissions','♙'],['audit','Audit trail','◷']]},
];
const titles = Object.fromEntries(navGroups.flatMap(g => g.items.map(x => [x[0],x[1]])));
const description = {
  patients:'Register patients and access their longitudinal care record.', encounters:'Chief complaints, diagnoses, and clinical examination notes.',
  chart:'Record tooth-specific conditions using the FDI numbering system.', 'care-plans':'Sequence treatments and connect procedures with clinical diagnoses.',
  appointments:'Manage upcoming dental visits and appointment progress.', procedures:'Document treatments against an approved care plan.',
  imaging:'Store imaging metadata and interpretation notes.', 'lab-orders':'Coordinate crowns, dentures, and other prosthetic lab work.',
  trials:'Manage dental study protocols and documented external approval references.', consents:'Track verified externally signed consent; this is not an e-signature system.',
  screenings:'Record clinician-reviewed inclusion / exclusion criteria after consent.', enrollments:'Assign study-specific subject IDs after eligible screening.',
  'research-visits':'Capture dental outcomes and protocol visit measurements.', 'safety-events':'Record adverse events, serious events and review status.',
  invoices:'Create invoices and record balances received.', stock:'Track materials, batches, expiration dates, and use.',
  audit:'Immutable-by-UI activity history of create / workflow actions (not a validated audit trail).',
  users:'Approve new registrations, assign staff roles and configure module access per user.'
};
const F = (name,label,type='text',extra={})=>({name,label,...(typeof type==='object'?{type:'text',...type}:{type,...extra})});
const FDI = [...[1,2,3,4].flatMap(a => Array.from({length:8},(_,i)=>String(a)+String(i+1))),
             ...[5,6,7,8].flatMap(a => Array.from({length:5},(_,i)=>String(a)+String(i+1)))];
const tooth = F('tooth','FDI tooth','select',{options:[['','General / none'],...FDI.map(x=>[x,x])],required:false});
const patient = F('patient_id','Patient','patient');
const trial = F('trial_id','Study protocol','trial');
const plan = F('plan_id','Linked care plan','plan');
const visitDay = F('visit_on','Visit date','date',{value:dateLocal()});
const defaultDate = dateLocal();
const formConfigs = {
  patients:[F('name','Full name'),F('dob','Date of birth','date'),F('gender','Gender','select',{options:['Female','Male','Other','Not specified']}),
           F('phone','Phone'),F('allergies','Allergies','textarea',{wide:true,required:false}),F('medical_alerts','Medical alerts','textarea',{wide:true,required:false}),F('medical_history','Medical history','textarea',{wide:true,required:false})],
  encounters:[patient,F('seen_on','Encounter date','date',{value:defaultDate}),F('dentist','Dentist / clinician',{value:'Dr. A. Mehta'}),
              F('complaint','Chief complaint','textarea',{wide:true}),F('diagnosis','Working diagnosis','textarea',{wide:true,required:false}),
              F('vital_notes','Vitals and relevant history','textarea',{wide:true,required:false}),F('clinical_notes','Clinical examination notes','textarea',{wide:true,required:false})],
  findings:[patient,{...tooth,required:true},F('surface','Surface','select',{options:['All','Occlusal','Mesial','Distal','Buccal','Lingual','Palatal','Incisal']}),
            F('finding','Dental finding','select',{options:['Caries','Periodontal pocket','Gingivitis','Pulpitis','Missing tooth','Restored','Fracture','Impaction','Tooth mobility','Healthy']}),
            F('severity','Severity','select',{options:['Mild','Moderate','Severe','Not applicable']}),F('probing_mm','Probing depth (mm)','number',{required:false,min:0,max:15}),
            F('bleeding','Bleeding on probing','check',{required:false}),F('notes','Finding notes','textarea',{wide:true,required:false})],
  'care-plans':[patient,tooth,F('diagnosis','Diagnosis'),F('procedure','Planned treatment','select',{options:['Composite restoration','Root canal treatment','Scaling and root planing','Dental extraction','Crown preparation','Dental implant','Complete denture','Partial denture','Orthodontic treatment','Periodontal surgery','Fluoride application','Preventive cleaning','Other']}),
                F('sequence','Treatment phase','select',{options:['Emergency care','Disease control','Definitive care','Rehabilitation','Maintenance / recall']}),
                F('priority','Priority','select',{options:['Routine','Urgent','Emergency']}),F('estimated_cost','Estimated cost (INR)','number',{value:0,min:0}),
                F('trial_id','Research protocol (optional)','trial',{required:false})],
  appointments:[patient,F('scheduled_at','Date & time','datetime-local',{value:dateTimeLocal()}),F('provider','Dentist / clinician',{value:'Dr. A. Mehta'}),
                F('purpose','Visit purpose','select',{options:['Consultation','Restoration','Root canal','Periodontal care','Implant','Oral surgery','Follow-up','Research review','Other']}),
                F('notes','Notes','textarea',{wide:true,required:false})],
  procedures:[patient,plan,F('performed_on','Treatment date','date',{value:defaultDate}),F('clinician','Operator',{value:'Dr. A. Mehta'}),
              F('performed','Procedure description'),F('outcome','Outcome','select',{options:['Completed','In progress','Deferred','Complication']}),
              F('follow_up_on','Follow-up date','date',{required:false}),F('instructions','Post-operative instructions','textarea',{wide:true,required:false})],
  imaging:[patient,tooth,F('modality','Imaging modality','select',{options:['Periapical X-ray','Bitewing X-ray','Panoramic OPG','CBCT','Intraoral photograph','Extraoral photograph','Other']}),
           F('captured_on','Capture date','date',{value:defaultDate}),F('reference','Secure file / PACS reference',{required:false}),
           F('impression','Clinical image interpretation','textarea',{wide:true,required:false})],
  'lab-orders':[patient,plan,F('work_type','Lab work / appliance','select',{options:['Zirconia crown','PFM crown','Complete denture','Partial denture','Bridge','Clear aligner','Night guard','Implant prosthesis','Other']}),
                F('laboratory','Lab name',{value:'Dental Lab'}),F('due_on','Due date','date',{value:defaultDate}),F('shade','Shade',{value:'A2',required:false})],
  invoices:[patient,F('plan_id','Related plan (optional)','plan',{required:false}),F('description','Charge / service'),
            F('amount','Amount (INR)','number',{min:1}),F('paid','Amount received','number',{min:0,value:0}),F('created_on','Invoice date','date',{value:defaultDate})],
  stock:[F('name','Material name'),F('category','Category','select',{options:['Consumables','Restorative','Endodontic','Orthodontic','Sterilization','Surgical','Other']}),
         F('batch','Batch / lot number',{required:false}),F('quantity','Quantity','number',{min:0}),F('reorder_point','Reorder threshold','number',{min:0}),
         F('unit','Unit',{value:'packs'}),F('expiry','Expiry date','date',{required:false})],
  trials:[F('code','Protocol code'),F('title','Protocol title','textarea',{wide:true}),F('indication','Dental indication'),
          F('intervention','Study intervention'),F('design','Study design','select',{options:['Interventional','Observational','Device study','Diagnostic study']}),
          F('primary_endpoint','Primary dental endpoint','textarea',{wide:true,required:false}),
          F('ec_reference','EC approval reference (external)',{required:false}),F('registry_reference','CTRI / registry ID (external)',{required:false}),
          F('regulatory_required','Regulatory authorization required','check',{required:false}),F('regulatory_reference','Regulator permission reference (if applicable)',{required:false})],
  consents:[patient,trial,F('document_version','Approved ICF version',{value:'v1.0'}),F('signed_on','Signature date','date',{value:defaultDate}),
            F('obtained_by','Consent discussion conducted by'),F('document_reference','External signed ICF record ID'),
            F('verified','Confirm externally signed and verified','check',{required:true})],
  screenings:[patient,trial,F('screened_on','Protocol screening date','date',{value:defaultDate}),F('eligibility','Eligibility assessment','select',{options:['PENDING','ELIGIBLE','INELIGIBLE']}),
              F('reviewer','Investigator / reviewer'),F('inclusion_exclusion_notes','Document inclusion / exclusion assessment','textarea',{wide:true})],
  enrollments:[patient,trial,F('enrolled_on','Enrollment date','date',{value:defaultDate})],
  'research-visits':[F('enrollment_id','Study subject','enrollment'),F('visit_name','Study visit','select',{options:['Baseline','Week 1','Week 2','Week 4','Week 8','Week 12','Unscheduled','End of Study']}),visitDay,
                     F('probing_mm','Mean probing depth (mm)','number',{required:false,min:0,max:15}),
                     F('plaque_index','Plaque index','number',{required:false,min:0}),
                     F('bleeding_pct','Bleeding on probing (%)','number',{required:false,min:0,max:100}),
                     F('dmft','DMFT score','number',{required:false,min:0,max:32}),F('pain_score','Pain score (0–10)','number',{required:false,min:0,max:10}),
                     F('notes','Outcome notes','textarea',{wide:true,required:false})],
  'safety-events':[F('enrollment_id','Study subject','enrollment'),F('onset_on','Event onset date','date',{value:defaultDate}),
                   F('description','Event description','textarea',{wide:true}),F('serious','Serious adverse event (SAE)','check',{required:false}),
                   F('severity','Severity','select',{options:['Mild','Moderate','Severe']}),
                   F('relatedness','Relatedness to intervention','select',{options:['Not assessed','Unrelated','Unlikely','Possible','Probable','Definite']}),
                   F('outcome','Outcome','select',{options:['Unknown','Recovering','Recovered','Not recovered','Fatal']})]
};
const tableCols = {
  patients:[['name','Patient'],['mrn','MRN'],['dob','Birth date'],['gender','Gender'],['allergies','Allergies']],
  encounters:[['patient_id','Patient'],['seen_on','Date'],['complaint','Complaint'],['diagnosis','Diagnosis'],['dentist','Dentist']],
  findings:[['patient_id','Patient'],['tooth','Tooth'],['surface','Surface'],['finding','Finding'],['severity','Severity'],['probing_mm','Pocket depth']],
  'care-plans':[['patient_id','Patient'],['tooth','Tooth'],['procedure','Treatment'],['sequence','Phase'],['estimated_cost','Estimate'],['status','Status']],
  appointments:[['patient_id','Patient'],['scheduled_at','Scheduled'],['purpose','Purpose'],['provider','Clinician'],['status','Status']],
  procedures:[['patient_id','Patient'],['performed_on','Date'],['performed','Performed'],['clinician','Clinician'],['outcome','Outcome'],['plan_id','Plan']],
  imaging:[['patient_id','Patient'],['captured_on','Taken'],['modality','Modality'],['tooth','Tooth'],['impression','Impression'],['reference','Reference']],
  'lab-orders':[['patient_id','Patient'],['work_type','Lab item'],['laboratory','Laboratory'],['shade','Shade'],['due_on','Due'],['status','Status']],
  invoices:[['patient_id','Patient'],['description','Description'],['amount','Billed'],['paid','Received'],['balance','Balance'],['created_on','Date']],
  stock:[['name','Item'],['category','Category'],['batch','Batch'],['quantity','On hand'],['reorder_point','Reorder'],['expiry','Expiry']],
  trials:[['code','Protocol'],['title','Title'],['indication','Indication'],['design','Study type'],['registry_reference','Registry'],['status','Status']],
  consents:[['patient_id','Patient'],['trial_id','Trial'],['document_version','ICF version'],['signed_on','Signed on'],['document_reference','Document reference'],['withdrawn','State']],
  screenings:[['patient_id','Patient'],['trial_id','Trial'],['screened_on','Screened'],['eligibility','Eligibility'],['reviewer','Reviewer']],
  enrollments:[['subject_code','Subject ID'],['patient_id','Patient'],['trial_id','Trial'],['enrolled_on','Enrolled'],['status','Status']],
  'research-visits':[['enrollment_id','Subject'],['visit_name','Visit'],['visit_on','Date'],['probing_mm','Pocket mm'],['plaque_index','Plaque'],['bleeding_pct','BOP %'],['pain_score','Pain']],
  'safety-events':[['enrollment_id','Subject'],['onset_on','Onset'],['description','Event description'],['serious','Serious?'],['relatedness','Relatedness'],['status','Status']],
  audit:[['timestamp','Timestamp'],['actor','User'],['action','Action'],['entity','Table'],['entity_id','ID'],['detail','Description']]
};
let store={}, user=null, view='dashboard', patientId=null, searchValue='', formMode='', modalExtras={};
const canView=(module)=>!!user?.permissions?.[module]?.view;
const canWrite=(module)=>!!user?.permissions?.[module]?.write;
const canVisit=(id)=>id==='chart'?(canView('patients')&&canView('findings')):canView(id);
const firstPage=()=>navGroups.flatMap(g=>g.items).map(x=>x[0]).find(canVisit)||'dashboard';
async function api(path, opts={}) {
  const res=await fetch('/api/'+path, {credentials:'same-origin',headers:{'Content-Type':'application/json'},...opts});
  if(!res.ok){let err;try{err=await res.json();}catch{err={}};
    const detail = Array.isArray(err.detail) ? err.detail.map(x=>x.msg).join('; ') : (err.detail||'Request failed');
    if(res.status===401 && path!=='login') showLogin();
    throw new Error(detail);
  }
  return await res.json();
}
const post=(url,obj)=>api(url,{method:'POST',body:JSON.stringify(obj)});
let toastTimer;
function toast(msg,fail=false){let el=$('#toast');el.textContent=msg;el.className=(fail?'fail ':'')+'show';clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.className='',3900);}
function showLogin(){user=null;store={};$('#app-shell').classList.add('hidden');$('#login-view').classList.remove('hidden');}
function showApp(){ $('#login-view').classList.add('hidden');$('#app-shell').classList.remove('hidden');$('#user-label').textContent=user.display_name;$('#role-label').textContent=user.role;$('#avatar').textContent=user.display_name[0];$('#top-avatar').textContent=user.display_name[0];$('#date-label').textContent=new Date().toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'});renderNav();}
async function refresh(){
 const keys=['patients','encounters','findings','care-plans','appointments','procedures','imaging','lab-orders','invoices','stock','trials','consents','screenings','enrollments','research-visits','safety-events','audit'].filter(canView);
 const results=await Promise.all(keys.map(async k=>[k,await api(k)]));
 store=Object.fromEntries(results);
 store.summary=canView('dashboard')?await api('summary'):{};
 if(canView('users')){
   store.users=await api('admin/users');
   store.catalog=await api('admin/catalog');
 }
}
function renderNav(){const nav=$('#nav');nav.innerHTML=navGroups.map(g=>{
 const items=g.items.filter(x=>canVisit(x[0]));
 if(!items.length)return '';
 return `<div class="nav-group">${esc(g.title)}</div>${items.map(x=>`<button data-nav="${x[0]}" class="${view===x[0]?'active':''}"><span class="nav-ico">${x[2]}</span>${esc(x[1])}</button>`).join('')}`;
}).join('');}
function go(id){
 if(!canVisit(id)){toast('You do not have access to this page',true);return;}
 view=id;searchValue='';renderNav();render();$('#sidebar').classList.remove('open');window.scrollTo({top:0,behavior:'instant'});
}
function heading(name,desc,action='',label='New record'){
 return `<div class="page-heading"><div><div class="overline">${name==='Overview'?'CENTRE PERFORMANCE':'DENTAL CENTRE WORKSPACE'}</div><h1>${esc(name)}</h1><p>${esc(desc)}</p></div>${action?`<button class="primary" data-action="${esc(action)}">＋ ${esc(label)}</button>`:''}</div>`;
}
function pById(id){return (store.patients||[]).find(p=>p.id===Number(id));}
function tById(id){return (store.trials||[]).find(t=>t.id===Number(id));}
function planById(id){return (store['care-plans']||[]).find(t=>t.id===Number(id));}
function eById(id){return (store.enrollments||[]).find(t=>t.id===Number(id));}
function colValue(k,row){
 const v=k==='balance'? Number(row.amount||0)-Number(row.paid||0) : row[k];
 if(k==='patient_id')return person(pById(v));
 if(k==='trial_id')return esc(tById(v)?.code||'—');
 if(k==='plan_id')return esc(planById(v)?.procedure||'—');
 if(k==='enrollment_id')return esc(eById(v)?.subject_code||'—');
 if(['status','severity','eligibility'].includes(k))return status(v);
 if(k==='withdrawn')return status(v?'WITHDRAWN':'ACTIVE');
 if(k==='serious')return v?status('SERIOUS'):status('NON-SERIOUS');
 if(['estimated_cost','amount','paid','balance'].includes(k))return esc(money(v));
 if(k==='name')return `<b>${esc(v)}</b>`;
 if(k==='probing_mm'&&v!==null&&v!==undefined)return esc(v)+' mm';
 if(typeof v==='boolean')return v?'Yes':'No';
 const shown=String(v??'—');return `<span title="${esc(shown)}">${esc(shown.length>68?shown.slice(0,66)+'…':shown)}</span>`;
}
function actionButtons(resource,row){const id=row.id;let acts=[];
 if(resource==='patients'&&canVisit('chart'))acts.push(['open-patient','View']);
 if(resource==='care-plans'&&canWrite(resource)){
   const next={DRAFT:'APPROVED',APPROVED:'IN_PROGRESS',IN_PROGRESS:'COMPLETED'}[row.status];
   if(next)acts.push(['plan-status',next.replaceAll('_',' ')]);
 }
 if(resource==='appointments'&&canWrite(resource)&&row.status!=='Completed')acts.push(['appointment-status','Update']);
 if(resource==='trials'&&user.role==='admin'){
   const next={DRAFT:'EC_APPROVED',EC_APPROVED:'ACTIVE',ACTIVE:'CLOSED'}[row.status];
   if(next)acts.push(['trial-status',next.replaceAll('_',' ')]);
 }
 if(resource==='consents'&&canWrite(resource)&&!row.withdrawn)acts.push(['withdraw-consent','Withdraw']);
 if(resource==='invoices'&&canWrite(resource)&&row.amount>row.paid)acts.push(['invoice-pay','Record payment']);
 if(resource==='stock'&&canWrite(resource))acts.push(['stock-use','Use stock']);
 if(resource==='safety-events'&&canWrite('safety-events')&&row.status!=='CLOSED')acts.push(['safety-status','Review']);
 return acts.map(a=>`<button class="record-action" data-row-action="${a[0]}" data-id="${id}">${esc(a[1])}</button>`).join('');
}
function table(resource, rows, max=500){const cols=tableCols[resource];
 if(!rows.length)return `<div class="empty-state"><div class="empty-icon">◌</div><strong>No records found</strong>Use the new record action to get started, or change your search.</div>`;
 return `<div class="table-wrap"><table class="data-table"><thead><tr>${cols.map(c=>`<th>${esc(c[1])}</th>`).join('')}<th></th></tr></thead><tbody>${rows.slice(0,max).map(row=>`<tr>${cols.map(c=>`<td>${colValue(c[0],row)}</td>`).join('')}<td>${actionButtons(resource,row)}</td></tr>`).join('')}</tbody></table></div>`;
}
function renderListing(resource){const name=titles[resource];const rows=store[resource]||[];
 const needle=searchValue.toLowerCase();const list=rows.filter(x=>JSON.stringify(x).toLowerCase().includes(needle)|| (x.patient_id&&pById(x.patient_id)?.name.toLowerCase().includes(needle)));
 let intro='';
 if(resource==='trials')intro=`<div class="info-banner"><strong>Governance first:</strong> An active protocol requires documented ethics approval and trial registration references, plus regulator authorization when applicable. This demo does not verify those references or replace approvals.</div><div class="trial-flow">${['Protocol','EC approval','Registration','Consent + screening','Enrollment + safety'].map((x,i)=>`<div class="flow-box"><span>${['①','②','③','④','⑤'][i]}</span>${x}</div>`).join('')}</div>`;
 if(resource==='consents')intro=`<div class="info-banner warning-banner"><strong>Consent safeguard:</strong> Record only metadata after an actual consent discussion and offline signed ICF. A checkbox here is not a legally valid electronic signature.</div>`;
 if(resource==='safety-events')intro=`<div class="info-banner warning-banner"><strong>Serious adverse events:</strong> These require immediate qualified investigator review and assessment of applicable timelines. This application does not automatically submit safety reports or calculate regulatory deadlines.</div>`;
 if(resource==='research-visits')intro=`<div class="info-banner"><strong>Dentistry-specific eCRF:</strong> Capture probing depth, plaque index, bleeding on probing, DMFT, pain, and protocol-specific visit notes.</div>`;
 if(resource==='audit')intro=`<div class="info-banner warning-banner"><strong>Demonstration log:</strong> These application entries are not tamper-proof, certified electronic records or 21 CFR Part 11-compliant audit trails.</div>`;
 return heading(name,description[resource],canWrite(resource)?resource:'',resource==='patients'?'Register patient':'New '+name.toLowerCase().replace(/s$/,'')) + intro +
 `<div class="table-card"><div class="table-toolbar"><div><b>All ${esc(name.toLowerCase())}</b> <span class="table-count" id="record-count">${list.length} records</span></div><input id="search" type="search" placeholder="Search records..." value="${esc(searchValue)}" autocomplete="off"></div><div id="table-list">${table(resource,list)}</div></div>`;
}
function metric(title,val,foot,icon){return `<div class="metric-card"><div class="metric-title">${esc(title)}</div><div class="metric-icon">${icon}</div><div class="metric-value">${esc(val)}</div><div class="metric-foot">${esc(foot)}</div></div>`;}
function overview(){const s=store.summary||{};
 const visible=(m)=>canView(m);
 const count=(v)=>v===null||v===undefined?'Restricted':String(v);
 const metrics=[
   visible('patients')&&metric('Registered patients',count(s.patients),'Longitudinal clinical records','♙'),
   visible('care-plans')&&metric('Active care plans',count(s.open_plans),'Approved / being treated','☷'),
   visible('trials')&&metric('Clinical trial protocols',count(s.trials),'Dental research projects','◈'),
   visible('safety-events')&&metric('Open safety events',count(s.open_safety),'Requires investigator assessment','⚑'),
   visible('appointments')&&metric('Dental appointments',count(s.appointments),'Scheduling workspace','▦'),
   visible('invoices')&&metric('Invoices',count((store.invoices||[]).length),'Billing records','₹'),
 ].filter(Boolean);
 const next=(store.appointments||[]).filter(a=>a.status==='Scheduled').sort((a,b)=>a.scheduled_at.localeCompare(b.scheduled_at)).slice(0,5);
 const quick=[['patients','Register patient'],['findings','Chart a tooth'],['care-plans','Plan treatment'],['appointments','Book appointment'],['trials','Create protocol'],['safety-events','Document AE']].filter(x=>canWrite(x[0]));
 return heading('Overview',`Your ${user.role} workspace, showing modules you are authorized to use.`,canWrite('patients')?'patients':'','Register patient')+
 `<div class="info-banner"><strong>Demo environment:</strong> Synthetic data only. Your menu and API access follow your individual permissions, which the centre administrator can change.</div>`+
 `<div class="metric-grid">${metrics.join('')||'<p>No dashboard metrics permitted.</p>'}</div>`+
 `<div class="split"><section class="surface"><div class="surface-header"><div><h3>${visible('appointments')?'Upcoming dental appointments':'Your access'}</h3><p class="surface-sub">${visible('appointments')?'Scheduled visits and follow-ups':'Permissions assigned to your account'}</p></div>${visible('appointments')?'<button class="small-link" data-nav="appointments">View all →</button>':''}</div>`+
 (visible('appointments')?(next.length?`<div class="table-wrap"><table class="mini-table"><thead><tr><th>Patient</th><th>When</th><th>Service</th></tr></thead><tbody>${next.map(a=>`<tr><td>${visible('patients')?person(pById(a.patient_id)):'Restricted'}</td><td>${esc(fmt(a.scheduled_at))}</td><td>${esc(a.purpose)}</td></tr>`).join('')}</tbody></table></div>`:'<div class="empty-state">No scheduled appointments.</div>'):
 `<div class="permission-chips">${navGroups.flatMap(g=>g.items).filter(x=>canVisit(x[0])&&x[0]!=='dashboard').map(x=>`<span class="permission-chip">${esc(x[1])}</span>`).join('')||'No additional modules granted.'}</div>`)+
 `</section><section class="surface"><div class="surface-header"><div><h3>Quick actions</h3><p class="surface-sub">Tools you can create records in</p></div></div><div class="quick-buttons">${quick.map(x=>`<button data-action="${x[0]}">＋ ${esc(x[1])}</button>`).join('')||'<p class="extra-note">You currently have view-only access.</p>'}</div></section></div>`+
 (canView('users')?`<div class="info-banner" style="margin-top:22px"><strong>Access administration:</strong> ${(store.users||[]).filter(x=>x.status==='PENDING').length} registration(s) waiting for review. <button class="small-link" data-nav="users">Manage staff access →</button></div>`:'');
}
function chart(){let patients=store.patients||[];if(!patients.length)return heading('Dental chart','Register a patient to create tooth findings.',canWrite('patients')?'patients':'');
 if(!patients.some(p=>p.id===patientId))patientId=patients[patients.length-1].id;
 const p=pById(patientId);const findings=(store.findings||[]).filter(f=>f.patient_id===patientId);
 const plans=(store['care-plans']||[]).filter(x=>x.patient_id===patientId);
 const permanentUpper=['18','17','16','15','14','13','12','11','21','22','23','24','25','26','27','28'];
 const permanentLower=['48','47','46','45','44','43','42','41','31','32','33','34','35','36','37','38'];
 const row=arr=>`<div class="fdi-chart">${arr.map(code=>{let f=findings.filter(x=>x.tooth===code);return `<button class="tooth ${f.length?'marked':''}" data-chart-tooth="${code}" title="FDI ${code}: ${esc(f.map(x=>x.finding).join(', ')||'No finding documented')}"><span class="tooth-icon">♧</span>${code}</button>`;}).join('')}</div>`;
 return heading('Dental chart','Interactive FDI odontogram and periodontal observations.',canWrite('findings')?'findings':'','Record finding')+
 `<div class="surface" style="margin-bottom:18px"><div class="surface-header"><div><h3>Patient odontogram</h3><p class="surface-sub">Permanent dentition · select a tooth to add a clinical finding</p></div><div class="patient-picker"><select id="chart-patient">${patients.map(x=>`<option value="${x.id}" ${x.id===patientId?'selected':''}>${esc(x.name)} · ${esc(x.mrn)}</option>`).join('')}</select></div></div>`+
 `<div class="chart-label">UPPER ARCH · RIGHT → LEFT</div>${row(permanentUpper)}<div class="chart-label">LOWER ARCH · RIGHT → LEFT</div>${row(permanentLower)}`+
 `<div class="chart-legend"><span><i class="legend-dot"></i>Documented finding</span><span><i class="legend-dot grey"></i>No finding recorded (not proof of health)</span></div>`+
 `<div class="eyebrow-tile">FDI numbering is used. Primary teeth (51–85) are supported in the finding form, but only permanent dentition is pictured here. This is a teaching chart, not clinical decision support.</div></div>`+
 `<div class="section-grid"><div class="surface"><div class="surface-header"><div><h3>Clinical findings</h3><p class="surface-sub">${findings.length} observations for ${esc(p.name)}</p></div></div><div class="table-wrap"><table class="mini-table"><tbody>${findings.map(f=>`<tr><td><b>${esc(f.tooth)}</b></td><td>${esc(f.finding)} · ${esc(f.surface)}</td><td>${status(f.severity)}</td></tr>`).join('')||'<tr><td>No findings yet</td></tr>'}</tbody></table></div></div>`+
 `<div class="surface"><div class="surface-header"><div><h3>Treatment pathway</h3><p class="surface-sub">Active and planned dental care</p></div></div><div class="table-wrap"><table class="mini-table"><tbody>${plans.map(x=>`<tr><td><b>${esc(x.tooth||'General')}</b></td><td>${esc(x.procedure)}</td><td>${status(x.status)}</td></tr>`).join('')||'<tr><td>No treatment plans yet</td></tr>'}</tbody></table></div></div></div>`;
}
const accessLabel=(level)=>({default:'Use role default',none:'No access',read:'View only',write:'View & edit'})[level]||level;
const roleOptions=['admin','dentist','researcher','coordinator','receptionist'];
function usersPage(){
 const accounts=store.users||[],catalog=store.catalog||{modules:[],role_defaults:{}};
 const pending=accounts.filter(a=>a.status==='PENDING').length;
 const panels=accounts.map(a=>{
   const isAdmin=a.role==='admin',isSelf=a.id===user.id,locked=isAdmin||isSelf;
   const name=esc(a.display_name),handle=esc(a.username);
   const actions=locked?'<span class="permission-note">Protected administrator account</span>':
     `<div class="staff-review-row"><label>Assigned role <select id="role-${a.id}" data-role-user="${a.id}">${roleOptions.map(r=>`<option value="${r}" ${a.role===r?'selected':''}>${esc(r==='receptionist'?'Front desk':r)}</option>`).join('')}</select></label>`+
     `<label>Account status <select id="status-${a.id}">${['ACTIVE','PENDING','SUSPENDED'].map(st=>`<option value="${st}" ${a.status===st?'selected':''}>${esc(st)}</option>`).join('')}</select></label>`+
     `<button class="primary" data-review-user="${a.id}">Save account</button>${a.status==='PENDING'?`<button class="secondary" data-approve-user="${a.id}">Approve & activate</button>`:''}</div>`;
   const permissionLines=catalog.modules.map(module=>{
     const inherited=catalog.role_defaults[a.role]?.[module]||'none';
     const override=a.overrides?.[module]||'default';
     const opts=[['default',`Role default (${accessLabel(inherited)})`],['none','No access'],['read','View only'],['write','View & edit']];
     return `<div class="permission-row"><div><strong>${esc(titles[module]||module)}</strong><small>${esc(accessLabel(inherited))} by role</small></div><select data-permission-user="${a.id}" data-module="${esc(module)}" ${locked?'disabled':''} aria-label="Permission for ${esc(module)} for ${name}">${opts.map(([value,label])=>`<option value="${value}" ${value===override?'selected':''}>${esc(label)}</option>`).join('')}</select></div>`;
   }).join('');
   return `<article class="staff-card"><div class="staff-top"><span class="person-mini">${name[0]||'U'}</span><div class="staff-id"><b>${name}</b><small>@${handle} · Registered ${esc(fmt(a.created_at))} · Requested: ${esc(a.requested_role)}</small></div><span class="tag ${esc(a.status.toLowerCase())}">${esc(a.status)}</span></div>${actions}`+
   `<details class="staff-permission-details"><summary>Module permissions <span class="permission-note">${locked?'Full administrator access':`${catalog.modules.filter(m=>a.permissions?.[m]?.view).length} modules visible`}</span></summary><div class="permission-list">${permissionLines}</div></details></article>`;
 }).join('');
 return heading('User permissions','Review sign-ups, assign account roles, and customize module-level access for every staff member.')+
 `<div class="info-banner"><strong>Account approval:</strong> New sign-ups remain PENDING and cannot sign in until activated. Changing a staff member’s role, status or permission revokes their existing login sessions. Only administrators can manage users and view the audit trail.</div>`+
 `<div class="metric-grid">${metric('Total accounts',accounts.length,'Registered staff','♙')}${metric('Pending approvals',pending,'Review access requests','◎')}${metric('Active accounts',accounts.filter(a=>a.status==='ACTIVE').length,'Approved staff','✓')}${metric('Suspended',accounts.filter(a=>a.status==='SUSPENDED').length,'Access disabled','⊘')}</div>`+
 `<div class="staff-toolbar"><h3>Staff directory</h3><input id="staff-search" type="search" placeholder="Find a staff member..." value="${esc(searchValue)}" /></div><div class="staff-list">${panels||'<div class="empty-state">No staff accounts found</div>'}</div>`;
}
function render(){ if(!canVisit(view)){view=firstPage();renderNav();} $('#crumb').textContent=titles[view]||'Overview';$('#page').innerHTML=view==='dashboard'?overview():view==='chart'?chart():view==='users'?usersPage():renderListing(view);}
function makeSelectOptions(f){let opts=[];
 if(f.type==='patient')opts=(store.patients||[]).map(x=>[x.id,`${x.mrn} — ${x.name}`]);
 else if(f.type==='trial')opts=(store.trials||[]).map(x=>[x.id,`${x.code} · ${x.status}`]);
 else if(f.type==='plan')opts=(store['care-plans']||[]).map(x=>[x.id,`#${x.id} ${x.procedure} · ${pById(x.patient_id)?.name||''}`]);
 else if(f.type==='enrollment')opts=(store.enrollments||[]).map(x=>[x.id,`${x.subject_code} · ${x.status}`]);
 else opts=(f.options||[]).map(x=>Array.isArray(x)?x:[x,x]);
 return opts;
}
function inputField(f, pref={}){
 const selected = Object.prototype.hasOwnProperty.call(pref,f.name)?pref[f.name]:f.value;
 const required=f.required===false?'':'required';const wide=f.wide?'wide':'';
 if(f.type==='check')return `<label class="${wide} check"><input type="checkbox" name="${f.name}" ${selected?'checked':''} ${required} />${esc(f.label)}</label>`;
 let html;
 if(['select','patient','trial','plan','enrollment'].includes(f.type)){
   const options=makeSelectOptions(f);
   html=`<select name="${f.name}" ${required}><option value="">${f.required===false?'None / optional':'Select '+esc(f.label.toLowerCase())}</option>${options.map(([v,label])=>`<option value="${esc(v)}" ${String(selected)===String(v)?'selected':''}>${esc(label)}</option>`).join('')}</select>`;
 } else if(f.type==='textarea')html=`<textarea name="${f.name}" ${required}>${esc(selected||'')}</textarea>`;
 else html=`<input name="${f.name}" type="${f.type==='number'?'number':f.type==='date'?'date':f.type==='datetime-local'?'datetime-local':'text'}" ${f.type==='number'?'step="any"':''} ${f.min!==undefined?`min="${f.min}"`:''} ${f.max!==undefined?`max="${f.max}"`:''} value="${esc(selected??'')}" ${required} />`;
 return `<label class="${wide}">${esc(f.label)}${html}</label>`;
}
function openForm(resource,pre={}){
 if(!canWrite(resource)){toast('Your role does not allow this action',true);return;}
 formMode=resource;modalExtras={};$('#modal-eyebrow').textContent='NEW CLINICAL / RESEARCH RECORD';
 $('#modal-title').textContent='New '+(titles[resource]||'Finding').replace(/s$/,'');
 $('#form-fields').innerHTML=(formConfigs[resource]||[]).map(f=>inputField(f,pre)).join('');
 $('#modal-error').textContent='';$('#modal-submit').textContent='Save record →';$('#dialog').showModal();
}
function actionForm(type,row){formMode='!'+type;modalExtras={row};$('#modal-eyebrow').textContent='RECORD WORKFLOW';
 let fields=[];let title='Update record';
 if(type==='plan-status'){let next={DRAFT:'APPROVED',APPROVED:'IN_PROGRESS',IN_PROGRESS:'COMPLETED'}[row.status];title='Move care plan to '+next;fields=[F('status','Next status','select',{options:[next]})];}
 if(type==='appointment-status'){title='Update appointment';fields=[F('status','Appointment state','select',{options:['Scheduled','Checked in','Completed','No show','Cancelled']})];}
 if(type==='trial-status'){let next={DRAFT:'EC_APPROVED',EC_APPROVED:'ACTIVE',ACTIVE:'CLOSED'}[row.status];title='Study state: '+next;fields=[F('status','Next trial state','select',{options:[next]}),
   F('ec_reference','EC approval reference',{required:false,value:row.ec_reference}),F('registry_reference','Prospective registration reference',{required:false,value:row.registry_reference}),
   F('regulatory_reference','Regulator authorization (if required)',{required:false,value:row.regulatory_reference})];}
 if(type==='withdraw-consent'){title='Withdraw participation consent';fields=[F('confirmation','Type WITHDRAW to proceed')];}
 if(type==='invoice-pay'){title='Record an invoice payment';fields=[F('amount',`Amount received (outstanding ${money(row.amount-row.paid)})`,'number',{min:.01})];}
 if(type==='stock-use'){title='Record material usage';fields=[F('amount',`Amount used (${row.quantity} ${row.unit} available)`,'number',{min:.01}),F('purpose','Clinical use or reason')];}
 if(type==='safety-status'){title='Safety review / reporting';fields=[F('status','Current safety state','select',{options:['OPEN','UNDER_REVIEW','REPORTED','CLOSED'],value:row.status}),
   F('reported_on','External safety report date, if applicable','date',{required:false,value:row.reported_on}),
   F('outcome','Event outcome','select',{options:['Unknown','Recovering','Recovered','Not recovered','Fatal'],value:row.outcome})];}
 $('#modal-title').textContent=title;$('#form-fields').innerHTML=fields.map(x=>inputField(x)).join('');
 $('#modal-error').textContent='';$('#modal-submit').textContent=type==='withdraw-consent'?'Confirm withdrawal →':'Update record →';$('#dialog').showModal();
}
function collectForm(){const fd=new FormData($('#modal-form'));const out={};$('#form-fields').querySelectorAll('[name]').forEach(el=>{
  if(el.type==='checkbox')out[el.name]=el.checked;
  else if(el.type==='number')out[el.name]=el.value===''?null:Number(el.value);
  else if(['patient_id','trial_id','plan_id','enrollment_id'].includes(el.name))out[el.name]=el.value===''?null:Number(el.value);
  else out[el.name]=el.value.trim();
 });return out;}
async function saveModal(e){e.preventDefault();const btn=$('#modal-submit');btn.disabled=true;$('#modal-error').textContent='';
 try {const v=collectForm();if(!formMode.startsWith('!')){
   const resource=formMode;if(resource==='patients')delete v.mrn;
   if(resource==='findings'&&!v.tooth)throw new Error('Choose a valid FDI tooth');
   if(resource==='consents'&&!v.verified)throw new Error('Verify the externally signed informed-consent documentation first.');
   if(resource==='care-plans'&&!v.trial_id)delete v.trial_id;
   if(resource==='invoices'&&!v.plan_id)delete v.plan_id;
   await post(resource,v);toast('Record saved successfully');
 }else{
   let type=formMode.slice(1),row=modalExtras.row;
   if(type==='plan-status')await post(`care-plans/${row.id}/status`,v);
   if(type==='appointment-status')await post(`appointments/${row.id}/status`,v);
   if(type==='trial-status')await post(`trials/${row.id}/status`,v);
   if(type==='withdraw-consent'){if(v.confirmation!=='WITHDRAW')throw new Error('Type WITHDRAW exactly to confirm');await post(`consents/${row.id}/withdraw`,{});}
   if(type==='invoice-pay')await post(`invoices/${row.id}/pay`,v);
   if(type==='stock-use')await post(`stock/${row.id}/use`,v);
   if(type==='safety-status')await post(`safety-events/${row.id}/status`,v);
   toast('Workflow updated');
 }
 $('#dialog').close();await refresh();render();
 }catch(error){$('#modal-error').textContent=error.message;toast(error.message,true);}finally{btn.disabled=false;}
}
async function boot(){try{user=await api('me');showApp();await refresh();go(firstPage());}catch{showLogin();}}
$('#login-form').addEventListener('submit',async(e)=>{e.preventDefault();let fd=new FormData(e.target);$('#login-error').textContent='';
 try{user=await post('login',Object.fromEntries(fd.entries()));showApp();await refresh();go(firstPage());}catch(error){$('#login-error').textContent=error.message;}});
$('#show-signup').addEventListener('click',()=>{
 $('#signup-panel').classList.remove('hidden');$('#login-form').classList.add('hidden');$('#show-signup').parentElement.classList.add('hidden');$('.demo-logins').classList.add('hidden');
 $('.login-content h2').textContent='Join the team';
});
$('#back-login').addEventListener('click',()=>{
 $('#signup-panel').classList.add('hidden');$('#login-form').classList.remove('hidden');$('#show-signup').parentElement.classList.remove('hidden');$('.demo-logins').classList.remove('hidden');
 $('.login-content h2').textContent='Welcome back';
});
$('#signup-form').addEventListener('submit',async(e)=>{
 e.preventDefault();const form=e.target, button=form.querySelector('[type=submit]');
 $('#signup-error').textContent='';const input=Object.fromEntries(new FormData(form));
 if(input.password!==input.confirm_password){$('#signup-error').textContent='Passwords do not match';return;}
 button.disabled=true;
 try{const reply=await post('signup',input);form.reset();$('#back-login').click();$('#login-error').textContent=reply.message;$('#login-error').classList.add('success-text');toast('Registration sent to the administrator');}
 catch(ex){$('#signup-error').textContent=ex.message;}
 finally{button.disabled=false;}
});
document.querySelectorAll('[data-login]').forEach(btn=>btn.addEventListener('click',()=>{$('#login-form [name=username]').value=btn.dataset.login;$('#login-form [name=password]').value='';$('#login-form [name=password]').focus();}));
$('#logout').addEventListener('click',async()=>{try{await post('logout',{});}catch{}showLogin();});
$('#menu-toggle').addEventListener('click',()=>$('#sidebar').classList.toggle('open'));
$('#modal-form').addEventListener('submit',saveModal);
$('#close-dialog').addEventListener('click',()=>$('#dialog').close());
$('#cancel-dialog').addEventListener('click',()=>$('#dialog').close());
document.addEventListener('click',(e)=>{
 let item=e.target.closest('[data-nav]');if(item){go(item.dataset.nav);return;}
 item=e.target.closest('[data-review-user], [data-approve-user]');if(item){
   const id=Number(item.dataset.reviewUser||item.dataset.approveUser), role=$('#role-'+id)?.value;
   const status=item.dataset.approveUser?'ACTIVE':$('#status-'+id)?.value;
   if(!role||!status)return;
   item.disabled=true;
   post(`admin/users/${id}/review`,{role,status}).then(async()=>{await refresh();render();toast('Account access updated; old sessions revoked');})
     .catch(err=>toast(err.message,true)).finally(()=>item.disabled=false);
   return;
 }
 item=e.target.closest('[data-action]');if(item){openForm(item.dataset.action,item.dataset.action==='findings'&&patientId?{patient_id:patientId}:{});return;}
 item=e.target.closest('[data-chart-tooth]');if(item){openForm('findings',{patient_id:patientId,tooth:item.dataset.chartTooth});return;}
 item=e.target.closest('[data-row-action]');if(item){const action=item.dataset.rowAction,id=Number(item.dataset.id);if(action==='open-patient'){patientId=id;go('chart');return;}
 const row=(store[view]||[]).find(x=>x.id===id);if(row)actionForm(action,row);return;}
});
document.addEventListener('change',async e=>{
 if(e.target.id==='chart-patient'){patientId=Number(e.target.value);render();return;}
 if(e.target.matches('[data-permission-user]')){
   const el=e.target, prev=el.dataset.previous||'';el.disabled=true;
   try{await post(`admin/users/${Number(el.dataset.permissionUser)}/permission`,{module:el.dataset.module,access:el.value});await refresh();render();toast('Permission saved; user will need to sign in again');}
   catch(err){toast(err.message,true);el.disabled=false;if(prev)el.value=prev;}
 }
});
document.addEventListener('input',e=>{if(e.target.id==='staff-search'){searchValue=e.target.value;document.querySelectorAll('.staff-card').forEach(card=>{card.style.display=card.textContent.toLowerCase().includes(searchValue.toLowerCase())?'':'none';});return;}if(e.target.id!=='search')return;searchValue=e.target.value;let rows=(store[view]||[]).filter(x=>JSON.stringify(x).toLowerCase().includes(searchValue.toLowerCase())||(x.patient_id&&pById(x.patient_id)?.name.toLowerCase().includes(searchValue.toLowerCase())));$('#table-list').innerHTML=table(view,rows);$('#record-count').textContent=rows.length+' records';});
boot();
