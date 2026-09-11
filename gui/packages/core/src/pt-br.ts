/**
 * Brazilian Portuguese, the second locale this build ships.
 *
 * A translation is a file and a file is a release: nothing here is read from disk, so adding
 * a language means editing this repository and shipping it, and a person cannot drop a
 * half-finished locale beside their settings and have the window speak it.
 *
 * The type is `Wording`, which is `Partial`, and that is not an accident about this file: a
 * translation in progress falls back per key and is worth shipping. What holds *this* one
 * complete is the suite, which runs `untranslated` over every locale the build lists — so a
 * new English string is a red run and not a Portuguese screen with an English sentence in
 * the middle of it.
 *
 * **The product name is not translated.** `app.name` is an identifier that happens to be a
 * word, and a locale that renamed it would be naming a different program.
 */

import type { Wording } from './wording'

/** The tag this file is written in, spelled as BCP-47 spells it. */
export const PT_BR_LOCALE = 'pt-BR'

export const PT_BR: Wording = {
  'app.name': 'roadkeep',

  'transport.absent': 'sem ponte - rodando como uma página comum de navegador',

  'portfolio.kicker': 'Portfólio',
  'portfolio.title': '{count} projetos nesta máquina',
  'portfolio.title.unknown': 'Projetos nesta máquina',
  'portfolio.tally': '{read} lidos · {pending} ainda lendo · {unreadable} ilegíveis',
  'portfolio.progress': '{stage}: {done} de {total}',
  'portfolio.stage.counting': 'contando cada backlog',
  'portfolio.stage.next': 'pedindo a próxima linha de cada um',
  'portfolio.asking': 'Procurando sob as raízes que as configurações nomeiam.',
  'portfolio.failed': 'A ponte não disse quais projetos existem: {reason}',
  'portfolio.none': 'Nenhum projeto foi encontrado sob as raízes que as configurações nomeiam.',
  'portfolio.none.hint':
    'Uma pasta com um roadkeep.toml sob uma dessas raízes aparece aqui na próxima vez que a janela perguntar.',
  'portfolio.filter.all': 'Todos {count}',
  'portfolio.filter.drifted': 'Verificação divergente {count}',
  'portfolio.filter.disagrees': 'Motor em desacordo {count}',
  'portfolio.filter.unreadable': 'Ilegíveis {count}',
  'portfolio.filter.label': 'Estreitar a lista',
  'portfolio.order': 'ordem: a do registro',
  'portfolio.column.project': 'Projeto',
  'portfolio.column.backlog': 'Pendências',
  'portfolio.column.next': 'Próxima linha pronta',
  'portfolio.column.gate': 'Verificação',
  'portfolio.column.engine': 'Motor',
  'portfolio.worktree': 'worktree do git',
  'portfolio.pending': 'ainda lendo',
  'portfolio.open': '{count} abertas',
  'portfolio.startable': '{startable} prontas para começar · {waiting} esperando',
  'portfolio.uncounted': '{count} não contadas',
  'portfolio.tier': 'nível: {tier}',
  'portfolio.next.none': 'nada pronto · {blocked} bloqueadas',
  'portfolio.next.missing': 'a próxima linha não chegou',
  'portfolio.gate.unknown': 'desconhecido',
  'portfolio.gate.clean': 'limpo',
  'portfolio.gate.drifted': 'divergente',
  'portfolio.gate.never': 'nunca rodou aqui',
  'portfolio.gate.findings': '{count} achados',
  'portfolio.gate.stale': 'desatualizado',
  'portfolio.engine.modified': 'árvore de trabalho',
  'portfolio.unreadable': 'ilegível',
  'portfolio.tried': 'o que foi tentado',
  'portfolio.kept': 'continua na lista',
  'portfolio.footnote':
    'Cada número nesta tela foi impresso por um verbo. Nada é somado entre projetos.',

  'settings.reset': 'Algumas configurações não puderam ser lidas e voltaram aos valores padrão.',
  'settings.unsaved': 'Essa escolha não pôde ser salva, então a próxima abertura não a terá.',

  'settings.lost.unparsable': '{file} não pode ser lido como JSON, então ele fica intacto',
  'settings.lost.file':
    'o arquivo de configurações não é um objeto, então tudo voltou ao valor padrão',
  'settings.lost.unversioned':
    'o arquivo de configurações não diz sua versão, então ele é lido como esta build escreve',
  'settings.lost.version':
    'o arquivo de configurações é da versão {found} e esta build lê {reads}, então ele fica intacto',
  'settings.lost.roots': 'as raízes não eram uma lista, então nenhuma foi lida',
  'settings.lost.dropped': '{count} raiz(es) não puderam ser lidas e foram descartadas',
  'settings.lost.skip': 'a lista de nomes a ignorar não era uma lista, então vale a lista padrão',
  'settings.lost.width': 'a largura do pool não era um número inteiro, então voltou para {width}',
  'settings.lost.theme': 'o fundo não é um que esta build conhece, então voltou para {theme}',
  'settings.lost.locale': 'o idioma não era um texto, então o sistema decide',

  'shell.home': 'Início',
  'shell.palette': 'Encontre uma linha em qualquer backlog',
  'shell.shortcuts': 'Atalhos de teclado',
  'shell.notices': 'Notificações',

  'menu.help': 'Ajuda',
  'update.check': 'Procurar atualizações…',
  'update.title': 'Atualizações',
  'update.newer': 'Você está na {current}. A mais recente publicada é a {latest}.',
  'update.current': 'Você está na {current}, que é a mais recente publicada.',
  'update.none': 'Você está na {current}. Nenhuma versão foi publicada ainda.',
  'update.failed': 'Você está na {current}. A verificação não obteve resposta: {reason}',
  'update.open': 'Abrir a página da versão',
  'update.close': 'Fechar',

  'ground.system': 'fundo: seguindo o sistema',
  'ground.light': 'fundo: claro',
  'ground.dark': 'fundo: escuro',
  'ground.action': 'Mudar o fundo',
}
