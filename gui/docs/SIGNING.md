# Assinar o executável do Windows

O procedimento que a RG49 espera: como se obtém um certificado de assinatura de código e
como ele entra neste build. Nenhuma linha de código substitui o certificado — ele é
comprado (ou concedido) e fica guardado onde o build alcança. Levantado em setembro de
2026; preços e regras mudam, então confira as fontes no fim antes de pagar.

## O que a assinatura resolve, e o que não resolve

Sem assinatura, o Windows mostra _"O Windows protegeu o computador"_ e _editor
desconhecido_ antes de o app abrir. Assinado, o nome do publicador aparece no UAC e nas
propriedades do arquivo, e o arquivo não pode ser alterado sem invalidar a assinatura.

**O aviso do SmartScreen não some no primeiro dia.** O SmartScreen dá reputação a um
certificado conforme os downloads acontecem sem problemas. Até 2024 um certificado EV
ganhava reputação imediata; a Microsoft acabou com isso, e hoje OV e EV constroem
reputação do mesmo jeito. Pagar a mais por EV só por causa do SmartScreen não compensa mais.

## A regra que mudou em 2023

Desde 1º de junho de 2023, a chave privada de todo certificado de assinatura de código (OV
e EV) precisa ficar em hardware certificado: um token USB ou um HSM na nuvem. Não se emite
mais um `.pfx` para guardar num arquivo. A consequência prática: **para assinar no CI, o
caminho é um serviço de assinatura em nuvem**. Um token USB só assina na máquina onde está
espetado.

## As opções, para quem é pessoa física no Brasil com um projeto MIT público

| Opção                                                                                           | Custo            | Publicador que aparece                       | Assina no CI?                                                                                        | Observações                                                                                                                          |
| ----------------------------------------------------------------------------------------------- | ---------------- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **SignPath Foundation**                                                                         | grátis           | `SignPath Foundation`                        | sim, integração oficial com GitHub Actions                                                           | Só open source: licença reconhecida, nenhum componente proprietário, projeto já lançado. O publicador não é você.                    |
| **Certum Open Source Code Signing** (nuvem, SimplySign)                                         | ~US$ 50/ano      | `Open Source Developer, Alexandre Oliveira`  | difícil: o SimplySign pede o celular a cada sessão, então na prática assina-se localmente no Windows | Só pessoa física, proibido para distribuição comercial, 5.000 assinaturas/mês.                                                       |
| **OV comercial com assinatura em nuvem** (SSL.com eSigner, DigiCert KeyLocker, GlobalSign etc.) | ~US$ 200–500/ano | seu nome (validação individual) ou a empresa | sim, pela ferramenta de linha de comando da CA, com segredos no Actions                              | Validação de identidade mais demorada. O caminho se o app um dia for comercial.                                                      |
| **Azure Artifact Signing** (antigo Trusted Signing)                                             | ~US$ 10/mês      | seu nome ou a empresa                        | sim, o electron-builder tem `azureSignOptions`                                                       | **Indisponível hoje**: pessoa física só nos EUA e no Canadá, e empresa só nos países da lista da Microsoft, que não inclui o Brasil. |

**Recomendação.** O SignPath, se o publicador `SignPath Foundation` for aceitável: é
grátis e assina no próprio CI. Se o publicador tiver de ser o seu nome e o custo baixo, o
Certum Open Source, assinando localmente. OV em nuvem só quando houver distribuição
comercial ou uma empresa por trás.

## Passo a passo

### 1. O que o repositório precisa antes

- **Um arquivo `LICENSE`.** O `package.json` declara MIT, mas o GitHub não detecta licença
  nenhuma porque o arquivo não existe — e o SignPath exige uma licença reconhecida.
- **O mesmo nome em todo lugar.** O `author` do `package.json` (RG139) já diz
  `Alexandre Oliveira`; o certificado deve dizer o mesmo, ou o `CompanyName` e o publicador
  vão discordar.
- **Uma release publicada** (RG50). O SignPath só aceita projetos que já distribuem o
  artefato que vai ser assinado, e descrito na página de download.
- **Só para o SignPath, mais duas coisas que os termos exigem:** uma página pública de
  política de assinatura de código (quem pode pedir uma assinatura, e o que é assinado) e
  autenticação multifator na conta de quem assina. Sem as duas a candidatura não passa. A
  página é [CODE-SIGNING-POLICY.md](CODE-SIGNING-POLICY.md) (RG194), e é o endereço que a
  candidatura aponta; o MFA é de quem tem a conta.

### 2. Obter o certificado

**SignPath Foundation.** Preencha o formulário de candidatura em signpath.org e mande por
e-mail. Aprovado, cria-se o projeto no painel da SignPath, apontando o artefato (o
instalador `.exe`) e o repositório do GitHub como origem verificada.

**Certum Open Source.** Compre na loja da Certum o _Open Source Code Signing in the Cloud_.
A validação é de pessoa física: documento com foto e, às vezes, uma chamada de vídeo. Ative
o SimplySign no celular e instale o SimplySign Desktop no Windows. Com a sessão aberta, o
certificado aparece no repositório de certificados do Windows.

**OV comercial em nuvem.** Compre o certificado de validação individual (ou da
organização, com CNPJ), passe pela validação e receba as credenciais do serviço de
assinatura em nuvem da CA.

### 3. Ligar no build

Hoje o `electron-builder.yml` produz, de propósito, um executável honestamente não
assinado: `signAndEditExecutable: true` grava o ícone e a versão, e a assinatura não
acontece porque nada nomeia um certificado. Cada opção entra de um jeito:

- **SignPath:** são **duas assinaturas, nesta ordem**. Assinar só o instalador NSIS deixa o
  `roadkeep.exe` de dentro dele sem assinatura nenhuma — o Windows avisa de novo na primeira
  vez que o app abre, depois de uma instalação que pareceu confiável. Então: o CI empacota
  sem instalador (`electron-builder --win --dir`), a ação da SignPath assina o `.exe` do
  diretório empacotado, o instalador é construído a partir dele
  (`electron-builder --win nsis --prepackaged release/win-unpacked`) e a ação assina o
  instalador também. O `signtool` local não participa de nenhuma das duas.
- **Certum com o SimplySign Desktop aberto:** o certificado está no repositório de
  certificados do Windows, então é só nomeá-lo pelo assunto — **na linha de comando da sua
  máquina, e não neste arquivo**:

  ```powershell
  npm run build
  npm run stamp
  npx electron-builder --config electron-builder.yml --publish never `
    --config.win.signtoolOptions.certificateSubjectName="Open Source Developer, Alexandre Oliveira"
  ```

  Commitado no `electron-builder.yml`, esse nome faz o job do Windows no CI procurar um
  certificado que o runner não tem: o `package` falha, e a release que ele rascunha não
  acontece. O certificado é local, então a configuração que o nomeia também é.

- **OV em nuvem:** `win.signtoolOptions.sign` apontando para um script que chama a
  ferramenta da CA, com as credenciais vindas de segredos do GitHub Actions — nunca do
  repositório.

Em todos os casos, **com carimbo de tempo RFC 3161** (o electron-builder usa um por padrão).
É ele que mantém a assinatura válida depois que o certificado vence.

### 4. Conferir

```powershell
Get-AuthenticodeSignature .\release\*.exe | Format-List Status, SignerCertificate
```

`Status` tem de ser `Valid`, e o `SignerCertificate` o nome que **aquela rota** assina: a
`SignPath Foundation` pelo SignPath, `Open Source Developer, Alexandre Oliveira` pelo Certum.
Nenhum dos dois é o `author` do `package.json`, e isso é a rota e não um defeito — pelo
SignPath o publicador é a fundação, e o Certum prefixa o nome de todo certificado open
source. Confira o instalador **e** o `roadkeep.exe` de dentro dele: são duas assinaturas.
As propriedades do arquivo, na aba _Assinaturas digitais_, dizem o mesmo.

### 5. Fechar a RG49

O build que assina roda com `ROADKEEP_GUI_SIGNED=signed`, e a linha de build do app deixa
de dizer `unsigned`. O comentário do topo do `electron-builder.yml` passa a nomear onde o
certificado está, e `roadkeep ship RG49` fecha a linha — com as duas assinaturas conferidas,
já que um instalador assinado com um `.exe` sem assinatura dentro é o aviso que a RG49
existe para tirar da frente da pessoa.

## Fontes

- [Code signing options for Windows app developers — Microsoft Learn](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options)
- [SmartScreen reputation for Windows app developers — Microsoft Learn](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)
- [Windows Apps PSA: EV certs do not grant immediate reputation anymore — ToDesktop](https://www.todesktop.com/blog/posts/windows-apps-psa-ev-certs-do-not-grant-immediate-reputation-anymore)
- [Azure Artifact Signing (formerly Trusted Signing) — Microsoft Azure](https://azure.microsoft.com/en-us/products/artifact-signing)
- [Trusted Signing: country not available for individual identity — Microsoft Q&A](https://learn.microsoft.com/en-nz/answers/questions/5810735/cant-create-a-new-trusted-signing-individual-ident)
- [SignPath Foundation conditions for Open Source projects](https://signpath.org/terms.html)
- [SignPath for the open source community](https://signpath.io/solutions/open-source-community)
- [Open Source Code Signing in the Cloud — Certum Store](https://certum.store/open-source-code-signing-on-simplysign.html)
- [Open Source Code Signing Certificates in 2026 — My-SSL](https://my-ssl.com/learn/open-source-code-signing-certificate)
