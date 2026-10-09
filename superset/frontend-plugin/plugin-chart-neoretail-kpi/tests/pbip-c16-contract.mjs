export function runC16Contract(transform, beforeTransform, witnesses = []) {
  let checks = 0; const proof = [];
  const eq = (a, b, label) => { if (a !== b) throw new Error(`${label}: ${a} != ${b}`); checks++; };
  const values = [null, undefined, 0, 8, -8];
  const contract = (profile, sell, cost, stock) => sell == null || sell === 0 || cost == null || cost === 0
    ? 0 : profile === 'markup' ? 100 * sell / cost : stock == null || stock === 0 ? null : 100 * (sell - cost) / stock;
  const form = profile => ({x_axis:'data', metrics:['Sell','Cost','Stock'], metric_labels:profile,
    semantic_profile:profile, semantic_anchor_date:'2026-10-07', card_variant:'bars', groupby:['activity_level'],
    pbip_sellout_u3m:true, pbip_dax_zero_guard:true});
  const calc = (fn, profile, rows, auxiliary, extra = {}) => fn({width:100,height:100,
    rawFormData:{...form(profile),...extra}, queriesData:[{data:rows},{data:[]},{data:auxiliary}]});
  for (const profile of ['markup','roi']) for (const sell of values) for (const cost of values) for (const stock of values) {
    const row = {data:'2026-10-01',Sell:sell,Cost:cost,Stock:stock};
    const prev = {...row,data:'2026-09-01'};
    const result = calc(transform,profile,[prev,row],[row]); const expected = contract(profile,sell,cost,stock);
    eq(result.indicators[0].current,expected,profile+' MTD conditional');
    eq(result.indicators[0].previous,expected,profile+' previous conditional');
    eq(result.indicators[0].average,expected,profile+' full U3M conditional');
    eq(result.timeline[1].components[0],sell == null ? null : sell,'preserve SQL Sell');
    eq(result.timeline[1].components[1],cost == null ? null : cost,'preserve SQL Cost');
    eq(result.timeline[1].components[2],stock == null ? null : stock,'preserve SQL Stock');
    // Annual iterates monthly ROI; known all-DIVIDE-BLANK SUMX issue is separate from C16.
    if(profile==='roi' && expected !== null) eq(result.indicators[0].annual,2*expected,'annual IF branch sum');
    proof.push({profile,input:[sell??null,cost??null,stock??null],source_missing:[sell===undefined,cost===undefined,stock===undefined],
      branch: sell==null||sell===0||cost==null||cost===0?'IF_ZERO':'DIVIDE',dax_contract:expected,
      before:calc(beforeTransform,profile,[prev,row],[row]).indicators[0].average,after:result.indicators[0].average});
  }
  for(const profile of ['markup','roi']) {
    const empty=calc(transform,profile,[],[{data:'2026-10-07',Sell:null,Cost:null,Stock:null}]);
    eq(empty.timeline.length,0,'no fabricated fact row');eq(empty.hasData,false,'absence provenance');
    eq(empty.indicators[0].current,0,'empty fact M0 context IF');eq(empty.indicators[0].previous,0,'empty fact previous IF');
    eq(empty.indicators[0].average,0,'empty fact auxiliary scalar IF');
    eq(calc(transform,profile,[],[]).indicators[0].average,null,'missing auxiliary response not fabricated');
    const noFlag=calc(transform,profile,[{data:'2026-09-01',Sell:null,Cost:null,Stock:null}],[],{pbip_dax_zero_guard:false});
    eq(noFlag.indicators[0].previous,null,'legacy opt-out unchanged');
    const basic=calc(transform,profile,[],[],{pbip_sellout_u3m:false});
    eq(basic.indicators[0].average,0,'missing components aggregate IF scoped');
    const direct=calc(transform,'direct_average',[{data:'2026-10-01',Sell:null}],[],{pbip_sellout_u3m:false});
    eq(direct.indicators[0].current,null,'flag does not affect unrelated profiles');
  }
  for (const w of witnesses) for(const profile of ['markup','roi']) {
    const r=w.after[0];const row={data:r.data,Sell:r.sellout_sum,Cost:r.sales_cost_sum,Stock:r.stock_cost_sum};
    const a=calc(transform,profile,[row],[row]); const b=calc(beforeTransform,profile,[row],[row]);
    const expected=contract(profile,row.Sell,row.Cost,row.Stock);
    eq(a.indicators[0].average,expected,'Gold witness AFTER');
    proof.push({real_gold:true,context:w.context,filters:w.filters,input:[row.Sell,row.Cost,row.Stock],profile,
      before:b.indicators[0].average,dax_contract:expected,after:a.indicators[0].average,pbi_value:null});
  }
  const annualRows=Array.from({length:12},(_,i)=>({data:new Date(Date.UTC(2025,10+i,1)).toISOString().slice(0,10),Sell:8,Cost:4,Stock:null}));
  const annualBlank=calc(transform,'roi',annualRows,[]);
  eq(annualBlank.indicators[0].previous,null,'DIVIDE stock BLANK not zero guard');
  eq(annualBlank.indicators[0].annual,0,'frozen annual reduction documented separately');
  return {c16_contract:'passed',checks,proof,annual_residual:{input:annualRows,dax_contract:null,frontend:annualBlank.indicators[0].annual,
    reason:'All monthly ROI values BLANK: annual reduce initial 0 differs from SUMX all BLANK; outside IF guard C16'}};
}
