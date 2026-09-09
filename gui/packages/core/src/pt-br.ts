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
  'app.tagline': 'A janela abre e os três pacotes estão ligados. Nenhum backlog foi lido ainda.',

  'transport.asking': 'perguntando à ponte',
  'transport.absent': 'sem ponte - rodando como uma página comum de navegador',
  'transport.ipc': 'ligada por IPC',
  'transport.http': 'ligada por HTTP',

  'settings.reset': 'Algumas configurações não puderam ser lidas e voltaram aos valores padrão.',
  'settings.unsaved': 'Essa escolha não pôde ser salva, então a próxima abertura não a terá.',

  'shell.home': 'Início',
  'shell.palette': 'Encontre uma linha em qualquer backlog',
  'shell.shortcuts': 'Atalhos de teclado',

  'ground.system': 'fundo: seguindo o sistema',
  'ground.light': 'fundo: claro',
  'ground.dark': 'fundo: escuro',
  'ground.action': 'Mudar o fundo',

  'packages.core':
    'A interface de transporte, a tabela de verbos e os formatos de payload. Sem Electron, sem React.',
  'packages.ui':
    'React sobre Tailwind. Recebe payloads e os desenha, e não conhece caminho nem processo.',
  'packages.shell':
    'O processo principal do Electron. Ele executa processos, observa arquivos e guarda as configurações.',
}
