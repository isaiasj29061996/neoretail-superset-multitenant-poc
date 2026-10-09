export function runAnnualBlankContract(transform, beforeTransform) {
 let checks=0;const proofs=[];
 const eq=(a,b,label)=>{if(JSON.stringify(a)!==JSON.stringify(b))throw new Error(label+': '+JSON.stringify(a)+' != '+JSON.stringify(b));checks++;};
 const members=Array.from({length:12},(_,i)=>new Date(Date.UTC(2025,10+i,1)).toISOString().slice(0,7));
 const form={x_axis:'data',metrics:['Sell','Cost','Stock'],metric_labels:'ROI',semantic_profile:'roi',
   semantic_anchor_date:'2026-10-07',card_variant:'bars',groupby:['activity_level'],
   pbip_sellout_u3m:true,pbip_dax_zero_guard:true,pbip_roi_annual_blank:true,pbip_roi_annual_members:members};
 const rows=values=>values.map((v,i)=>({data:members[i]+'-01',Sell:v==null?201:200+v,Cost:200,Stock:v==null?null:100}));
 const aux={data:'2026-10-07',Sell:300,Cost:200,Stock:100};
 const calc=(fn,values,extra={})=>fn({width:100,height:100,rawFormData:{...form,...extra},queriesData:[{data:rows(values)},{data:[]},{data:[aux]}]});
 const cases=[['all12_blank',Array(12).fill(null),null],['12_existing_all_blank',Array(12).fill(null),null],
 ['blank_and_values',[1,null,2,null,3,null,null,null,null,null,null,null],6],
 ['blank_and_zero',[0,...Array(11).fill(null)],0],['all_zero',Array(12).fill(0),0],
 ['one_value_other_blank',[7,...Array(11).fill(null)],7],['positive_values',Array(12).fill(2),24],
 ['negative_values',Array(12).fill(-2),-24],['positive_negative_blank',[8,-3,null,...Array(9).fill(null)],5]];
 for(const [name,values,expected] of cases){
  const before=calc(beforeTransform,values),after=calc(transform,values);
  eq(after.indicators[0].annual,expected,name+' SUMX final');
  eq(after.timeline,before.timeline,name+' intermediate values and components unchanged');
  for(const key of ['current','previous','average','lastYear'])eq(after.indicators[0][key],before.indicators[0][key],name+' ROI '+key+' unchanged');
  eq(calc(transform,values,{semantic_profile:'markup',metric_labels:'Markup'}),calc(beforeTransform,values,{semantic_profile:'markup',metric_labels:'Markup'}),name+' entire Markup unchanged');
  proofs.push({case:name,members,monthly_intermediates:values,before:before.indicators[0].annual,dax_contract:expected,after:after.indicators[0].annual,pbi_value:null});
 }
 const emptyIterator=calc(transform,[],{pbip_roi_annual_members:[]});
 eq(emptyIterator.indicators[0].annual,null,'VALUES empty => BLANK');
 eq(emptyIterator.timeline.length,0,'empty iterator no facts inserted');
 proofs.push({case:'no_calendar_members',members:[],monthly_intermediates:[],before:calc(beforeTransform,[],{pbip_roi_annual_members:[]}).indicators[0].annual,dax_contract:null,after:emptyIterator.indicators[0].annual});
 const emptyFacts=calc(transform,[]);eq(emptyFacts.indicators[0].annual,0,'12 calendar members, no fact => monthly IF zeros');
 eq(emptyFacts.timeline.length,0,'no fabricated timeline');eq(emptyFacts.hasData,false,'no-fact provenance');
 proofs.push({case:'no_facts_calendar_members_exist',members,fact_rows:0,monthly_intermediates:Array(12).fill(0),before:calc(beforeTransform,[]).indicators[0].annual,dax_contract:0,after:emptyFacts.indicators[0].annual});
 eq(calc(transform,Array(12).fill(null),{pbip_roi_annual_members:undefined}).indicators[0].annual,0,'default partial prior month adds real C16 empty-context zero');
 eq(calc(transform,Array(12).fill(null),{pbip_roi_annual_members:[...members,'2024-01',members[0]]}).indicators[0].annual,null,'VALUES unique and existing frozen window intersection');
 eq(calc(transform,[null],{pbip_roi_annual_members:[members[0],members[1]]}).indicators[0].annual,0,'blank fact month plus missing fact month zero');
 eq(calc(transform,[],{semantic_anchor_date:undefined,pbip_roi_annual_members:[]}).indicators[0].annual,null,'no anchor/no members => BLANK');
 return {annual_blank_contract:'passed',checks,proofs};
}
