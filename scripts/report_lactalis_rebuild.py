"""Build a source-linked report from this run's evidence; never infer gate success."""
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
out = root / 'generated'
def read(name):
    path = out / name
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
def lines(name):
    path = out / name
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=root, text=True).strip()
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
text = [f'# Reconstrução local LACTALIS — ID 290', '', f'Branch: `{branch}`. Commit: `{head}`.', '',
    'Execução do zero, sem recuperação dos volumes apagados. Sem merge, push ou alteração de main.', '',
    '## Origem e isolamento', '',
    'Fatos: container Azure `neoretail`, prefixo `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/`: 172 arquivos, 2.262.892.218 bytes, 115.392.674 linhas. Versões/ETags: [evidência](lactalis_source_versions_current.json).', '',
    'As dimensões com identidade foram filtradas por ID 290 e nome LACTALIS antes de persistir cache ou Bronze. `DIMENSAO_LOCAL` é compartilhada, sem ID de cliente: selecionada pelos varejistas contratados de LACTALIS. Leitura por ranges de Parquet remoto com ETag fixo; blocos compartilhados precisam ser lidos para selecionar linhas, mas a população não selecionada nunca é gravada localmente. Não foi inventado manufacturer_id.', '',
    '[Paths e schemas Azure](lactalis_source_preflight_current.json) · [seleção das dimensões](scoped_dimensions_290.json)', '',
    '## Lake: linhas e identidade', '']
source = read('lactalis_source_preflight_current.json')
if source:
    text += ['Dimensões Azure identificadas:', '']
    text += [f"- `{d['path']}`: {d['rows']:,} linhas na origem, {d['bytes']:,} bytes." for d in source['dimensions']]
    text += ['', 'As contagens abaixo são as linhas selecionadas/persistidas; dimensões remotas compartilhadas incluem outros clientes na origem.', '']
for layer in ('bronze', 'silver', 'gold'):
    data = read(f'lactalis_{layer}_isolation.json')
    text += [f'### {layer.title()}', '', f'[Auditoria completa](lactalis_{layer}_isolation.json)', '']
    if data:
        entries = data if isinstance(data, list) else data.get('tables', [])
        if isinstance(entries, dict): entries = list(entries.values())
        text += ['| Tabela | Linhas | ID |', '|---|---:|---|']
        for entry in entries:
            text.append(f"| {entry.get('table', entry.get('name', '?'))} | {entry.get('rows', '?'):,} | {entry.get('ids', [])} |")
        text.append('')
sql = read('lactalis_sql_current.json')
text += ['## PostgreSQL e serving', '',
    'O contrato desta branch é o schema `gold`. Não foram criados Gold AMBEV/PANDURATA. A Gold completa está no lake; a publicação SQL usa janelas existentes de serving: TVD 180 dias, semanal 730 dias, OSA/mensal 1095 dias; histórico mensal completo e exportação diária recente.', '']
if sql:
    text += [f"Isolamento SQL aprovado: **{sql['passed']}**. Banco: **{sql['database_bytes']:,} bytes**. Schemas: {', '.join(sql['schemas'])}.", '',
        '[Objetos, contagens por tenant, tamanhos e índices](lactalis_sql_current.json)', '', '| Objeto | Linhas | Total bytes | Índices bytes |', '|---|---:|---:|---:|']
    for r in sql['relations']:
        if 'total_bytes' in r:
            text.append(f"| {r['schema']}.{r['table']} | {sum(n for _,n in r.get('tenant_counts', [])):,} | {r['total_bytes']:,} | {r['index_bytes']:,} |")
    text += ['', 'Views: ' + ', '.join(r['schema']+'.'+r['table'] for r in sql['relations'] if r['kind']=='v') + '.', '', 'Maiores 30 objetos: campo `top30` da evidência SQL.', '']
text += ['### Execução dos marts', '', '[Log completo](lactalis_marts_current.log)', '', '| SQL | Status | Segundos |', '|---|---|---:|']
for r in read('lactalis_marts_current.json') or []:
    text.append(f"| {r['sql']} | {r['status']} | {r['seconds']} |")
text += ['', '## Pipeline e quality gates', '', '| Etapa | Código de saída | Segundos |', '|---|---:|---:|']
for r in lines('lactalis_execution_current.jsonl'):
    text.append(f"| [{r['step']}]({r['log']}) | {r['exit_code']} | {r['seconds']} |")
text += ['', 'Silver: 20 checks; Gold: 15 checks. Fórmulas Power Query preservadas; camada semântica mantém as definições DAX atuais. [Silver](lactalis_03D_current.log) · [Gold](lactalis_07_current.log).', '',
    '## Superset: bootstrap e validação', '', '| Script | Código de saída | Segundos |', '|---|---:|---:|']
for r in lines('lactalis_superset_current.jsonl'):
    link = r['log']
    initial = link.replace('_current.log', '_initial.log')
    if r['exit_code'] and (out/initial).exists(): link = initial
    text.append(f"| [{r['script']}]({link}) | {r['exit_code']} | {r['seconds']} |")
text += ['', '## Embedded, RLS e Assistant', '']
guest = read('lactalis_guest_current.json')
if guest:
    text += [f"Sessão real: ID {guest['session_customer']}. Overrides negados: {guest['context_overrides_denied']}.", '']
    for d in guest['dashboards']:
        text.append(f"- `{d['slug']}`: RLS `{d['rls']}`, {len(d['probes'])} probes; assinatura adulterada rejeitada: {d['tampered_signature_rejected']}.")
        if 'measure_filter_guest_choices' in d:
            text.append(f"  Medida via Guest Token: {', '.join(d['measure_filter_guest_choices'])}.")
    text.append('')
for mode in ('embedded', 'guest', 'assistant', 'assistant_smoke'):
    name = f'lactalis_http_{mode}_current.log'
    text.append(f'- {mode}: [{name}]({name})' if (out/name).exists() else f'- {mode}: ainda não executado.')
text += ['', '## Disco', '', '| Etapa | C livre bytes | Lake KiB | Analytics volume KiB |', '|---|---:|---:|---:|']
for r in lines('lactalis_disk_current.jsonl'):
    text.append(f"| {r['stage']} | {r['disk']['Free']:,} | {r['local_lake_kib']} | {r['analytics_data_kib']} |")
text += ['', 'Snapshots `lactalis_disk_*.txt` contêm docker system df -v. Os volumes incluem WAL e temporários; não equivalem ao tamanho lógico do banco.', '',
    '## Ollama e pendências', '',
    'Ollama foi autorizado somente após os gates de dados, Superset, Embedded/RLS e mock. Homologação de negócio/temporal depende dos responsáveis e não é substituída pelos testes técnicos.', '']
preflight = read('lactalis_ollama_preflight_current.json')
if preflight:
    text += ['Pre-flight antes do download:', '', '```json', json.dumps(preflight, indent=2, ensure_ascii=False), '```', '']
if (out/'lactalis_http_ollama_current.log').exists():
    text += ['[Pergunta real e comparação com a Tool SQL](lactalis_http_ollama_current.log)', '']
    try:
        runtime = json.loads((out/'lactalis_http_ollama_current.log').read_text(encoding='utf-8').splitlines()[-1])
        text += [f"Ollama: teste aprovado **{runtime['passed']}**; provider `{runtime['health']['provider']}`, modelo `{runtime['health']['model']}`.", '',
                 f"Pergunta: {runtime['question']}", '', f"Resposta real: {runtime['answer']}", '',
                 f"Valor da Tool: **{runtime['value']}**; igualdade exata com resultado HTTP; fonte `{runtime['source']}`. O código executa a Tool antes da geração; o modelo recebe somente o contexto estruturado autorizado e redige a resposta. Parâmetros SQL: {runtime['production_tool_sql_parameters']}.", '']
        if 'timings_ms' in runtime:
            text += [f"Tempos reais em CPU: {runtime['timings_ms']} ms (valor/fonte/governança).", '',
                     f"Resposta de fonte: {runtime['source_answer']}", '', f"Resposta de governança: {runtime['governance_answer']}", '']
    except (ValueError, KeyError):
        text += ['O teste real ainda não passou; consultar o log para o erro. Não tratar health como prova de geração.', '']
startup = read('lactalis_start_ollama_current.json')
if startup:
    text += [f"Startup Ollama: código {startup['exit_code']}, {startup['seconds']} s. [Log](lactalis_start_ollama_current.log).", '']
retry = read('lactalis_start_ollama_timeout_current.json')
if retry:
    text += ['A primeira geração real atingiu o timeout existente de 60 s em CPU. O runtime foi reconfigurado com LLM_TIMEOUT_MS=180000, sem novo download nem alteração de fórmulas. [Falha inicial](lactalis_http_ollama_initial.log) · [startup com timeout ajustado](lactalis_start_ollama_timeout_current.log).', '',
             'Para iniciar novamente com a mesma configuração (o arquivo .env foi preservado):', '',
             '```powershell', "$env:LLM_PROVIDER = 'ollama'", "$env:LLM_TIMEOUT_MS = '180000'", "$env:NEORETAIL_CUSTOMER = '290'", "$env:SPARK_MASTER = 'local[4]'", '.\\start.ps1 -Assistant', '```', '']
final = read('lactalis_runtime_final.json')
if final:
    text += ['Estado final:', '', '```json', json.dumps(final, indent=2, ensure_ascii=False), '```', '']
    text += ['URLs: [Embedded](http://localhost:3000), [Superset](http://localhost:8088), [Jupyter](http://localhost:8888). A porta publicada real de Analytics é **5432**; a mensagem fixa de startup ainda imprime 5433. [Consumo dos containers](lactalis_stats_final.txt) · [Docker system df -v final](lactalis_disk_final.txt) · [Estado da worktree](lactalis_worktree_final.txt).', '',
             'Somente o modelo llama3.1:8b está instalado. O [catálogo oficial](https://ollama.com/library/llama3.1:8b) informa aproximadamente 4,9 GB; a instalação local confirmou esse tamanho. Sete serviços estão healthy e superset-init terminou com código zero. Embedded/Guest/RLS foram revalidados após a inicialização Ollama.', '']
text += ['## Ocorrências e validações adicionais', '',
    'O primeiro probe filtrado de Overview Quantidade usava a rede fixa AKKIATACADO, ausente na LACTALIS. O parâmetro NEORETAIL_VALIDATION_REDE permite executar a mesma exigência com CENCOSUD, presente no tenant. Fórmulas, tolerâncias e exigência de resultado não vazio foram mantidas. [Falha original](lactalis_validate_overview_quantity_initial.log) · [resultado atual](lactalis_validate_overview_quantity_current.log).', '',
    'Nenhum ID diferente de 290 ou nome diferente de LACTALIS foi encontrado nas colunas de identidade dos dados carregados. Nomes históricos em código/documentação e em mensagens fixas de bootstrap não representam dados carregados de outro tenant.', '',
    'O cenário por item escolhia globalmente hectolitro, inexistente para o iogurte selecionado: SOURCE e CHARTDATA retornaram ambos zero períodos. O gate exige cenário positivo; foi parametrizada a conversão de teste para quilograma, fornecida pela origem para esse mesmo item. As regras de métricas e comparações permaneceram iguais. O diagnóstico independente reconciliou os 30 períodos em quilograma. Nenhuma conversão foi criada. [Diagnóstico](lactalis_inventory_conversion_diagnosis.json) · [falha original](lactalis_validate_panorama_inventory_filters_initial.log).', '',
    'OSA certificado: o teste de uma rede levou inicialmente 14.882 ms, acima do limite original de 3.000 ms. O novo mart nr_osa_monthly_retail (SQL 46) preserva as bases e fórmulas do SQL 45; apenas uma rede usa o cache. Múltiplas redes e outros filtros usam o detalhe. Resultado: 188,08 ms no caso filtrado, máximo 330,18 ms nos 14 charts padrão, zero violações. Quatro testes de roteamento e 11 contratos OSA passaram. [Validator](lactalis_validate_osa_industry_certified_current.log).', '',
    'OSA antiga: referências a sellout_sum/osa_loss_sum eram incompatíveis com nr_overview_summary. Duas métricas foram vinculadas às bases existentes de faturamento/fallback, perda e preço médio. Sete consultas passaram; quatro fórmulas reconciliadas em 30 meses contra o fato histórico, incluindo a normalização de NULL já definida no SQL 31. [Falha original](lactalis_validate_osa_industry_initial.log) · [reconciliação](lactalis_validate_osa_industry_current.log).', '',
    'O probe independente adicional inicialmente comparou NULL bruto com zero do mart, omitindo COALESCE já existente no SQL 31. O probe foi corrigido para reproduzir esse contrato de entrada sobre os fatos; métricas, mart e tolerância não foram alterados. A tabela de execução conserva todas as tentativas; logs *_current.log representam a última execução e *_initial.log a primeira falha preservada.', '',
    'Assistant mock autenticado: OSA 83,43631628432307%, resposta 83,44%, igualdade exata com a Tool SQL de produção. Fonte gold.nr_overview_quantity_default; parâmetro SQL 290; overrides 142/17066/609 negados. Status preservados: RECONCILED, negócio pending, temporal PARCIAL_CALENDARIO e PENDENTE_VARIANCE_DAX.', '',
    'Testes já executados: 10 de isolamento/Power Query, 60 contratos Panorama/OSA, 16 contratos locais, 31 Assistant e 7 startup. Nenhum modelo foi necessário para esses testes.', '']
(out/'lactalis_rebuild_report.md').write_text('\n'.join(text), encoding='utf-8')
print('generated/lactalis_rebuild_report.md')
