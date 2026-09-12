# Política de assinatura de código

Quem pode fazer um build ser assinado, e o que uma assinatura cobre. Esta página existe
porque os termos da SignPath Foundation exigem que um leitor consiga responder as duas
perguntas sem perguntar a ninguém — e porque quem baixa um instalador merece a mesma
resposta.

A escolha da rota e a comparação das alternativas estão em [SIGNING.md](SIGNING.md).

## Quem pode pedir uma assinatura

**Uma pessoa: Alexandre Oliveira**, mantenedor e único titular de permissão de escrita em
[github.com/alegauss/roadkeep-gui](https://github.com/alegauss/roadkeep-gui). É o `author`
declarado no `package.json`, e é quem responde pela conta que solicita assinaturas — com
autenticação multifator ativa, como os mesmos termos exigem.

Não há outro caminho. Uma contribuição de terceiro chega por pull request, é revisada e só
vira artefato assinado depois de entrar no `main` e de a pessoa acima empurrar uma tag.

## O que é assinado

Só o que sai de uma **tag `v<versão>`** empurrada para este repositório. Nada de um push
comum, nada de um branch, nada de um fork.

| Artefato                        | Plataforma | Assinado |
| ------------------------------- | ---------- | -------- |
| `roadkeep.exe` dentro do pacote | Windows    | sim      |
| Instalador NSIS `.exe`          | Windows    | sim      |
| `.AppImage`                     | Linux      | não      |

São **duas assinaturas no Windows, nessa ordem**: primeiro o executável do diretório
empacotado, depois o instalador construído a partir dele. Assinar só o instalador deixaria
o `roadkeep.exe` de dentro sem assinatura, e o Windows avisaria de novo na primeira vez que
o app abrisse — depois de uma instalação que pareceu confiável.

O AppImage não é assinado: assinatura Authenticode é um mecanismo do Windows, e no Linux o
que vale é o checksum publicado junto da release.

## Como acontece

Um único workflow, [`.github/workflows/ci.yml`](../.github/workflows/ci.yml), no job
`package`. Ele roda **apenas** quando a referência é uma tag `v*`, e antes de construir
qualquer coisa confere que:

1. a suíte de testes passou — nada é empacotado de uma árvore vermelha;
2. o gate do roadkeep passou;
3. a tag nomeia exatamente a versão que o `package.json` carrega.

Falhando qualquer um, nenhum artefato existe e nada é assinado.

O job `release` publica o resultado como **rascunho**. Uma release é uma decisão que uma
pessoa toma, não efeito colateral de empurrar uma tag: até alguém publicar, quem consulta
`releases/latest` não vê nada.

## Como conferir

Num build assinado, o Windows mostra o publicador nas propriedades do arquivo, aba
_Assinaturas digitais_. Por linha de comando:

```powershell
Get-AuthenticodeSignature .\roadkeep.exe | Format-List Status, SignerCertificate
```

`Status` deve dizer `Valid`. Confira **os dois** arquivos: o instalador e o `roadkeep.exe`
que ele instala.

A tela _Sobre_ do app diz qual build está rodando e de onde ele veio. Enquanto não houver
certificado, ela diz `unsigned` — sem rodeio, porque um app que mente sobre a própria
assinatura é pior que um app sem assinatura.

## Onde reportar um problema

Um artefato assinado que você não consegue relacionar a uma tag deste repositório, ou uma
assinatura que não confere:
[abra uma issue](https://github.com/alegauss/roadkeep-gui/issues).
