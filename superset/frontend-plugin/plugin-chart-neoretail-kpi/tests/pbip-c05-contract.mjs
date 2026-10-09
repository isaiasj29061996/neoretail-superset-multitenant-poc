export function runC05Contract(build,transform) {
 let checks=0;const eq=(a,b,label)=>{if(JSON.stringify(a)!==JSON.stringify(b))throw new Error(label+': '+JSON.stringify(a)+' != '+JSON.stringify(b));checks++;};
 const monthly=[7,8,9,10].map((m,i)=>({data:`2026-${String(m).padStart(2,'0')}-01`,Sell:10*(i+1),Cost:2,Stock:10}));
 const form={x_axis:'data',metrics:['Sell','Cost','Stock'],metric_labels:'Sell|Cost|Stock',semantic_profile:'direct_average',semantic_anchor_date:'2026-10-07',card_variant:'multi'};
 const old=transform({width:100,height:100,rawFormData:form,queriesData:[{data:monthly}]});
 const full={data:'2026-10-07',Sell:75,Cost:6,Stock:25};
 const now=transform({width:100,height:100,rawFormData:{...form,pbip_sellout_u3m:true},queriesData:[{data:monthly},{data:[full]}]});
 eq(old.indicators[0].average,20,'before monthly');eq(now.indicators[0].average,25,'after full context /3');
 eq(now.indicators[0].current,old.indicators[0].current,'MTD unchanged');eq(now.indicators[0].previous,old.indicators[0].previous,'previous unchanged');
 eq(now.indicators[1].average,old.indicators[1].average,'other sales component unchanged');
 for (const [profile,expected] of [['markup',1250],['roi',276]]) {
  const p={...form,metric_labels:profile,semantic_profile:profile,card_variant:'bars',groupby:['activity_level'],pbip_sellout_u3m:true};
  const r=transform({width:100,height:100,rawFormData:p,queriesData:[{data:monthly},{data:[]},{data:[full]}]});
  eq(r.indicators[0].average,expected,profile+' full component');
  const before=transform({width:100,height:100,rawFormData:{...p,pbip_sellout_u3m:false},queriesData:[{data:monthly},{data:[]}]});
  eq(r.indicators[0].current,before.indicators[0].current,profile+' MTD frozen');eq(r.indicators[0].previous,before.indicators[0].previous,profile+' previous frozen');
  const blank=transform({width:100,height:100,rawFormData:p,queriesData:[{data:monthly},{data:[]},{data:[{...full,Sell:null,Cost:null,Stock:null}]}]});
  eq(blank.indicators[0].average,null,profile+' C16 residual not corrected');
 }
 const missing=transform({width:100,height:100,rawFormData:{...form,pbip_sellout_u3m:true},queriesData:[{data:monthly}]});eq(missing.indicators[0].average,null,'missing auxiliary result must not use monthly fallback');
 const queries=build({...form,pbip_sellout_u3m:true},{buildQuery:undefined});
 eq(queries.length,2,'timeline plus U3M');eq(queries[1].filters.at(-1).val,['pbip_c05_u3m'],'per-query scope');
 const legacy=build(form,{});eq(legacy.length,1,'legacy query unchanged');
 return {c05_contract:'passed',checks};
}
