export function runTvdIvdContract(transform) {
 let checks=0;
 const eq=(actual,expected,label)=>{if(actual!==expected)throw new Error(label+': '+actual+' != '+expected);checks++;};
 const form={x_axis:'data',metrics:['TVD'],metric_labels:'TVD',semantic_profile:'direct_average',semantic_period:'month_last_nonblank',semantic_anchor_date:'2026-10-07',semantic_disable_ly:true};
 const calc=rows=>transform({width:100,height:100,rawFormData:form,queriesData:[{data:rows}]}).indicators[0];
 let r=calc([{data:'2026-07-15',TVD:9},{data:'2026-09-20',TVD:3},{data:'2026-10-04',TVD:0}]);
 eq(r.current,0,'zero MTD retained');eq(r.previous,3,'selected September date');eq(r.average,4,'monthly last values with fixed /3');
 r=calc([{data:'2026-07-15',TVD:null},{data:'2026-08-20',TVD:null},{data:'2026-09-20',TVD:null}]);
 eq(r.average,null,'all BLANK U3M');eq(r.current,null,'absent MTD not relabelled');
 r=calc([{data:'2026-09-20',TVD:0}]);eq(r.average,0,'zero plus missing months stays zero');
 r=calc([]);eq(r.current,null,'empty MTD');eq(r.previous,null,'empty previous');eq(r.average,null,'empty U3M');
 return {tvd_ivd_contract:'passed',checks};
}
