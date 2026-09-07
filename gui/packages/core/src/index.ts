export { BRIDGE_CHANNELS, BRIDGE_KEY } from './bridge'
export type { BridgeIdentity, RendererBridge, TransportName } from './bridge'
export {
  flagsFor,
  readCapabilities,
  readCommandArgument,
  readCommandsPayload,
  readPublishedCommand,
  withheld,
} from './capabilities'
export type {
  Capability,
  CapabilityReport,
  CommandArgument,
  CommandsPayload,
  PublishedCommand,
} from './capabilities'
export {
  CATALOGUE_VERSION,
  catalogueFrom,
  EMPTY_CATALOGUE,
  present,
  readCatalogue,
  reconcile,
  rowsFrom,
} from './catalogue'
export type {
  CatalogueChange,
  ChangeKind,
  ProjectCatalogue,
  Reconciled,
  RecordedProject,
} from './catalogue'
export { coldStart } from './cold-start'
export type { ColdStartProgress, ColdStartStage } from './cold-start'
export { candidateBoard, inTier } from './candidates'
export type { Candidate, CandidateBoard } from './candidates'
export { createCachingTransport } from './cache'
export type { CachingOptions, CachingTransport } from './cache'
export { groupProjects, isFamily } from './families'
export {
  createGateLedger,
  gateHealth,
  needsGate,
  recordGate,
  UNKNOWN_GATE,
} from './gate'
export type { GateHealth, GateLedger, GateRecord, GateVerdict } from './gate'
export type { ProjectFamily, ProjectMember, ProjectSite } from './families'
export { attemptRead, DEFAULT_LIMITS, withLimits } from './limits'
export type { ProjectRead, ReadLimits, Unreadable } from './limits'
export { createPooledTransport } from './pool'
export type { PoolOptions } from './pool'
export { folderName, pendingRow, readRow, tally, unreadableRow } from './portfolio'
export type {
  PortfolioTally,
  ProjectRow,
  RowCounts,
  RowEngine,
  RowGate,
  RowNext,
  RowReads,
  RowState,
} from './portfolio'
export {
  addRoot,
  checkRoot,
  coveredBy,
  DEFAULT_DEPTH,
  DEPTH_CEILING,
  NO_DEFAULT_ROOTS,
  removeRoot,
  walkable,
  withPresence,
} from './roots'
export type { KeyOf, KnownRoot, RootCheck, RootPresence, RootProblem, ScanRoot } from './roots'
export { coversEverything, search } from './search'
export type { Hit, SearchableProject, SearchAnswer, SearchField } from './search'
export { DEFAULT_POLICY, mayEnter, scan } from './scanning'
export type { Found, Listing, Look, ScanPolicy, ScanResult } from './scanning'
export { buildArgv, createClient } from './client'
export type { CallOptions, Client } from './client'
export { disagrees, isModified, resolveEngine } from './engine-resolution'
export type {
  EngineResolution,
  ResolvedEngine,
  ResolveOptions,
  TransportFor,
} from './engine-resolution'
export { readEnginesPayload, splitCommandLine } from './engines'
export type { EngineProvenance, EnginesPayload } from './engines'
export {
  governedFiles,
  narrowingOfBrief,
  narrowingOfList,
  narrowingOfStats,
  readBriefPayload,
  readConfigPayload,
  readListPayload,
  readLintPayload,
  readPickPayload,
  readSection,
  readShowPayload,
  readStatsPayload,
  readTaskLine,
  readUnblocks,
} from './payloads'
export type {
  AbsentRequirement,
  BlockCount,
  BriefPayload,
  ConfigKey,
  ConfigPayload,
  ListPayload,
  LintFinding,
  LintPayload,
  Narrowing,
  PickedLine,
  PickPayload,
  RationaleSection,
  ShowPayload,
  Standing,
  Startable,
  StatsPayload,
  TaskLine,
  Unblocks,
} from './payloads'
export { explainFailure, readPayload } from './reading'
export type { Parsed, PayloadFailure, Reader } from './reading'
export {
  fieldsRefused,
  offerable,
  readAnswer,
  readDoor,
  readExplanation,
  readRefusal,
  readRefusedField,
  readRemedy,
} from './refusals'
export type { Answer, Door, Explanation, Refusal, RefusedField, Remedy } from './refusals'
export { PACKAGES, RESPONSIBILITY } from './packages'
export type { PackageName } from './packages'
export { EngineCallFailed } from './transport'
export type {
  CancelSignal,
  EngineFailure,
  EngineRequest,
  EngineResult,
  Transport,
} from './transport'
export { EVERY_INPUT, VERBS } from './verbs'
export type { VerbInputs, VerbName } from './verbs'
