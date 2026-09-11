---
name: audit
description: Auditoria completa do roadkeep-gui — roda os gates, varre as sete partições em paralelo com o agente scanner, deduplica, verifica com o agente verifier e registra os CONFIRMADOS no roadkeep. Use quando pedirem auditar, revisar o repositório inteiro, caçar dívida ou procurar defeitos fora de uma mudança específica.
---

Uma auditoria deste repositório, do gate ao registro. O `/code-review` olha um diff; isto
olha o projeto parado. Não conserta nada: o produto é um backlog, não um patch.

## 1. Os gates primeiro

Rode, nesta ordem, e **guarde a saída como linha de base**:

```
node -v                # exige >= 26. Abaixo disso os projetos ui morrem por outra causa
npm run typecheck
npm run lint
npm test
```

`npm run test:live` e `npm run build` só se a auditoria for incluir spawn, bundle ou
caminho de asset — são os caros e precisam de python e de um build no disco.

O que já falhava aqui é linha de base e não achado. Se `node -v` for menor que 26, diga isso
uma vez agora: todo resultado de `ui` e `ui-live` desta rodada é inconclusivo.

## 2. Um `scanner` por partição, em paralelo

Sete chamadas ao `scanner` **numa única mensagem**, para rodarem juntas. Cada uma recebe a
lista de caminhos da sua partição e nada mais — nenhum scanner conhece os achados dos outros.

| #   | Partição              | Escopo                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| --- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `core/seam`           | `transport.ts` `verbs.ts` `writes.ts` `payloads.ts` `reading.ts` `rows.ts` `answers.ts` `bridge.ts` `client.ts` `refusals.ts` `gate.ts` + testes                                                                                                                                                                                                                                                                                                                       |
| 2   | `core/rules`          | `acts` `backlog` `budgeting` `candidates` `correcting` `design` `detail` `families` `filters` `graph` `limiting` `limits` `markers` `marking` `policy` `repairing` `search` `sections` + testes                                                                                                                                                                                                                                                                        |
| 3   | `core/session`        | `agent` `binding` `build` `cache` `capabilities` `cold-start` `engines` `engine-resolution` `handover` `memory` `pauses` `pool` `reloading` `session` `tools` `transcript` `updates` `watching` + testes                                                                                                                                                                                                                                                               |
| 4   | `core/view`           | `catalogue` `contrast` `ground` `index` `landing` `leaving` `locales` `opening` `packages` `portfolio` `pt-br` `roots` `scanning` `settings` `wording` `writing` + testes                                                                                                                                                                                                                                                                                              |
| 5   | `ui`                  | todo `packages/ui/src` (`.ts`, `.tsx`, `index.css`) + `vite.config.ts`, `vitest.live.config.ts`, `components.json`                                                                                                                                                                                                                                                                                                                                                     |
| 6   | `shell/electron`      | `main` `window` `preload` `posture` `menu` `menu-template` `navigation` `guard` `content-policy` `open-here` `machine` `locale` `launch` `dev` `start` `live` `live-setup` `built` `built-setup` `updates` `advisories` `settings-file` + testes                                                                                                                                                                                                                       |
| 7   | `shell/engines+build` | `process-transport` `mcp-transport` `http-transport` `bridge` `engine-handler` `engine-candidates` `agent-candidates` `session-process` `scan-fs` `root-paths` `source-watch` `governed-watch` `governed-stamp` `freshness` `git-worktree` `scratch` `fixture` `fixture-cache` `fake-claude` `compiler` `probing` `running-app` `stamp` `stamp-build` `audit` + testes + `vite.main.config.ts`, `vite.preload.config.ts`, `electron-builder.yml`, `.github/workflows/` |

## 3. Deduplique

Mesmo arquivo e mesmo defeito vindo de duas partições → uma entrada só, com as duas
reproduções. Mesmo defeito em arquivos diferentes → mantenha separado, mas anote que é o
mesmo padrão: isso vira uma linha de backlog, não sete. Ordene do mais grave para o menos.

## 4. Um `verifier`, com a lista inteira

Uma chamada só, recebendo todos os achados deduplicados mais a linha de base do passo 1.
Ele precisa da lista completa para fechar achados em lote por comando; sete `verifier`s
rodariam `npm test` sete vezes e julgariam cada achado sem ver o resto.

## 5. Registre os CONFIRMADOS

Este projeto é governado pelo roadkeep (`roadkeep.toml`, prefixo `RG`), então o registro é
por comando — **nunca editando `docs/ROADMAP.md` ou `docs/IMPROVEMENTS.md` à mão**, que um
hook recusa. Leia a skill `roadkeep` para a gramática exata antes de escrever.

- Prefira as ferramentas `mcp__roadkeep__*` (`add`, `brief`, `lint`).
- O alternativo de terminal é `python .claude/hooks/roadkeep-launch.py`.
- Um achado por linha: `--symptom` diz **o que não funciona** (nunca o nome da correção, ou
  a linha nunca pode ser falsificada) e `--why` é **uma frase**. Marcador `💭` quando o
  desenho ainda está por escrever, que é o caso de quase todo achado de auditoria.
- Feche com `roadkeep lint`.

Se em algum outro repositório o roadkeep não estiver configurado, o destino é
`docs/AUDIT.md`, uma seção por rodada, datada. Aqui ele está — use o comando.

FALSO POSITIVO e NÃO VERIFICÁVEL **não** entram no backlog. Um NÃO VERIFICÁVEL que se repita
rodada após rodada é sinal de máquina mal configurada (Node abaixo de 26, python sem
roadkeep), não de dívida.

## 6. Reporte só as contagens

```
partições varridas: 7 · achados brutos: N · após dedupe: N
CONFIRMADOS: N (registrados: RG###, RG###) · FALSOS POSITIVOS: N · NÃO VERIFICÁVEIS: N
linha de base: <o que já falhava antes, ou "gates limpos">
```

Sem despejar os achados de novo — eles estão no roadmap. Se algum CONFIRMADO for pequeno e
óbvio, ofereça consertá-lo como tarefa seguinte; não conserte dentro da auditoria, porque
uma tarefa é um commit e uma auditoria não é tarefa nenhuma.
