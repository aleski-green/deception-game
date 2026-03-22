export interface Player {
  id: number;
  name: string;
  role: string;
  alive?: boolean;
  eliminatedRound?: number | null;
  eliminatedPhase?: string | null;
}

export interface ThoughtEntry {
  agentId: number;
  agentName: string;
  round: number;
  phase: string;
  thought: string;
  suspicions: Record<string, number>;
  strategy: string;
}

export interface FreechatMsg {
  round: number;
  senderId: number;
  senderName: string;
  receiverId: number;
  receiverName: string;
  content: string;
}

export interface PitchMsg {
  round: number;
  speakerId: number;
  speakerName: string;
  content: string;
}

export interface VoteEntry {
  round: number;
  voterId: number;
  voterName: string;
  targetId: number;
  targetName: string;
}

export interface VoteResult {
  round: number;
  eliminatedId: number | null;
  eliminatedName: string | null;
  revealedRole: string | null;
  votes: Record<string, number>;
}

export interface NightAction {
  round: number;
  action: string;
  agentId: number;
  agentName: string;
  targetId: number;
  targetName: string;
  result?: string;
}

export interface NightResult {
  round: number;
  killedId: number | null;
  killedName: string | null;
  saved: boolean;
}

export interface GameState {
  gameId: number | null;
  round: number;
  phase: string;
  players: Player[];
  thoughts: ThoughtEntry[];
  freechats: FreechatMsg[];
  pitches: PitchMsg[];
  votes: VoteEntry[];
  voteResults: VoteResult[];
  nightActions: NightAction[];
  nightResults: NightResult[];
  winner: string | null;
  connected: boolean;
}

export type WSEvent =
  | { type: "game_start"; data: { gameId: number; players: Player[] } }
  | { type: "phase_change"; data: { round: number; phase: string; alivePlayers: { id: number; name: string }[] } }
  | { type: "thought"; data: ThoughtEntry }
  | { type: "freechat"; data: FreechatMsg }
  | { type: "pitch"; data: PitchMsg }
  | { type: "vote"; data: VoteEntry }
  | { type: "vote_result"; data: VoteResult }
  | { type: "night_action"; data: NightAction }
  | { type: "night_result"; data: NightResult }
  | { type: "game_over"; data: { winner: string; players: Player[] } };
