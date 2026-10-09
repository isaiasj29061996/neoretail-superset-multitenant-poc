export function runC14Contract(transform) {
  let checks=0;
  const eq=(actual,expected,label)=>{
    if(JSON.stringify(actual)!==JSON.stringify(expected))throw new Error(label+': '+JSON.stringify(actual)+' != '+JSON.stringify(expected));
    checks++;
  };
  const form={x_axis:'data',metrics:['Cost','Quantity'],metric_labels:'Cost|Quantity',semantic_profile:'direct_average',semantic_anchor_date:'2026-10-07',card_variant:'multi'};
  const rows=[{data:'2026-07-01',Cost:6,Quantity:10},{data:'2026-08-01',Cost:null,Quantity:20},{data:'2026-09-01',Cost:0,Quantity:30},{data:'2026-10-01',Cost:null,Quantity:40}];
  const calc=(p,data,extra=[])=>transform({width:100,height:100,rawFormData:p,queriesData:[{data},...extra]});
  for(const profile of ['direct_average','stock_bundle']) {
    const p={...form,semantic_profile:profile};
    const r=calc(p,rows);
    eq(r.indicators[0].current,null,profile+' MTD BLANK');
    eq(r.indicators[0].previous,0,profile+' previous real zero');
    eq(r.indicators[0].average,2,profile+' U3M total /3');
    eq(calc(p,rows.map(r=>({...r,Cost:null}))).indicators[0].average,null,profile+' all BLANK U3M');
    eq(calc(p,[]).indicators[0].current,null,profile+' no rows');
  }
  for(const profile of ['markup','roi']) {
    const p={...form,metrics:['Sell','Cost','Stock'],metric_labels:profile,semantic_profile:profile,pbip_sellout_u3m:true};
    const monthly=rows.map(r=>({...r,Sell:12,Stock:6}));
    const full={data:'2026-10-07',Sell:36,Cost:null,Stock:18};
    const r=calc(p,monthly,[{data:[full]}]);
    eq(r.indicators[0].current,null,profile+' consumes nullable MTD cost, C16 unchanged');
    eq(r.indicators[0].previous,0,profile+' zero guard unchanged');
    eq(r.indicators[0].average,null,profile+' consumes nullable full U3M cost');
    const zero=calc(p,monthly,[{data:[{...full,Cost:0}]}]);
    eq(zero.indicators[0].average,0,profile+' real zero differs from BLANK');
  }
  return {c14_contract:'passed',checks};
}
