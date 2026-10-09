# Restauração em outra máquina

1. Instalar Git, Docker Desktop/WSL2 e ferramentas indicadas nos Dockerfiles. Autenticar na conta com acesso ao repositório PRIVADO. Não colocar token na URL.
2. Clonar e obter a branch principal de backup:

```powershell
git clone https://github.com/isaiasj29061996/neoretail-superset-multitenant-poc.git NeoRetail
Set-Location NeoRetail
git fetch origin
git switch --create restore/osa-industry origin/backup/osa-industry-pre-format-20261009
```

3. Conferir SHA do commit e arquivos usando o inventário desta pasta. Outras linhas de trabalho precisam de checkout próprio; não misturar arquivos de branches:

```powershell
git worktree add ../NeoRetail-fasttrack -b restore/fasttrack origin/backup/multitenant-fasttrack-pre-format-20261009
```

4. Restaurar `.env` e chaves de backup privado, mantendo-os fora do Git. Comparar requisitos com `.env.example`. Restaurar fixtures reais e PBIP/evidências integrais nos caminhos esperados pelos testes; preservar os originais arquivados.
5. Para manter o estado materializado: restaurar os dumps e volumes do backup externo em ambiente isolado e com versões PostgreSQL/Superset compatíveis. Preservar SUPERSET_SECRET_KEY antiga. Somente depois conectar aplicação e validar metadata, dashboards, tenant/RLS/Guest e data de corte.
6. Com Docker pronto, usar `./start.ps1 -Rebuild` conforme README e opções da branch. Esse comando faz bootstrap de metadata; revisar a ordem quando houver metadata DB restaurada para não substituir configurações preservadas. Não executar refresh/pipeline automaticamente.
7. Rodar health e contratos pertinentes à branch. Os testes com fixtures reais exigem backup externo; outros testes e dependências devem rodar conforme instruções locais. O clone validado prova recuperação de arquivos, não prova recuperação dos bancos nem nova certificação funcional.
8. Se optar por reconstruir dados futuramente, isso depende de credenciais e disponibilidade/versão das fontes Azure. Não substitui o backup do estado exato de 08/10 e não deve ser presumido como garantia de recuperação.
