// Run inside the actual Embedded container; never log credentials or JWTs.
import assert from 'node:assert/strict';
const base = `http://localhost:${process.env.PORT || 3000}`;
let cookie = '';
async function request(path, body) {
  const response = await fetch(base + path, {method:body ? 'POST':'GET',
    headers:{'Content-Type':'application/json', ...(cookie ? {Cookie:cookie}: {})},
    ...(body ? {body:JSON.stringify(body)}:{})});
  const setCookie = response.headers.get('set-cookie');
  if (setCookie) cookie = setCookie.split(';')[0];
  return {status:response.status, body:await response.json()};
}
assert.equal((await request('/api/context', {idCustomer:17066})).status, 401);
assert.equal((await request('/api/login', {username:'demo.multitenant', password:process.env.DEMO_USER_PASSWORD})).status, 200);
const session = await request('/api/session');
assert.equal(session.status, 200);
assert.equal(session.body.idCustomer, 17066);
assert.deepEqual(session.body.availableCustomers.map(c=>c.idCustomer), [17066,290,16868]);
const report = [];
for (const tenant of [17066,290,16868,17066]) {
  assert.equal((await request('/api/context', {idCustomer:tenant})).status, 200);
  assert.equal((await request('/api/session')).body.idCustomer, tenant);
  const catalog = await request('/api/catalog');
  assert.equal(catalog.status, 200);
  const token = await request('/api/guest-token', {dashboardKey:'overview', idCustomer:142});
  assert.equal(token.status, 200);
  const payload = JSON.parse(Buffer.from(token.body.token.split('.')[1], 'base64url').toString());
  assert.deepEqual(payload.rls_rules.map(r=>r.clause), [`id_customer = ${tenant}`]);
  report.push({tenant, context:true, catalog:true, guestJWT:true, bodyTamperingIgnored:true});
}
for (const denied of [142,999999,-1,'17066 OR 1=1',null]) {
  assert.equal((await request('/api/context', {idCustomer:denied})).status, 403);
  assert.equal((await request('/api/session')).body.idCustomer, 17066);
}
assert.equal((await request('/api/guest-token', {dashboardKey:'unknown'})).status, 403);
assert.equal((await request('/api/logout', {})).status, 200);
console.log(JSON.stringify({checks:report, deniedContexts:5, unknownDashboardDenied:true}));
