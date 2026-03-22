import { useReducer } from "react";
import type { GameState, WSEvent, Player } from "../types/game";

const initialState: GameState = {
  gameId: null,
  round: 0,
  phase: "waiting",
  players: [],
  thoughts: [],
  freechats: [],
  pitches: [],
  votes: [],
  voteResults: [],
  nightActions: [],
  nightResults: [],
  winner: null,
  connected: false,
};

type Action =
  | { type: "WS_EVENT"; event: WSEvent }
  | { type: "SET_CONNECTED"; connected: boolean }
  | { type: "RESET" };

function reducer(state: GameState, action: Action): GameState {
  switch (action.type) {
    case "SET_CONNECTED":
      return { ...state, connected: action.connected };

    case "RESET":
      return { ...initialState, connected: state.connected };

    case "WS_EVENT": {
      const ev = action.event;
      switch (ev.type) {
        case "game_start":
          return {
            ...initialState,
            connected: state.connected,
            gameId: ev.data.gameId,
            players: ev.data.players.map((p) => ({ ...p, alive: true })),
            phase: "started",
          };

        case "phase_change":
          return {
            ...state,
            round: ev.data.round,
            phase: ev.data.phase,
            players: state.players.map((p) => ({
              ...p,
              alive: ev.data.alivePlayers.some((a) => a.id === p.id),
            })),
          };

        case "thought":
          return { ...state, thoughts: [...state.thoughts, ev.data] };

        case "freechat":
          return { ...state, freechats: [...state.freechats, ev.data] };

        case "pitch":
          return { ...state, pitches: [...state.pitches, ev.data] };

        case "vote":
          return { ...state, votes: [...state.votes, ev.data] };

        case "vote_result":
          return {
            ...state,
            voteResults: [...state.voteResults, ev.data],
            players: ev.data.eliminatedId != null
              ? state.players.map((p) =>
                  p.id === ev.data.eliminatedId
                    ? { ...p, alive: false, eliminatedPhase: "vote" }
                    : p
                )
              : state.players,
          };

        case "night_action":
          return { ...state, nightActions: [...state.nightActions, ev.data] };

        case "night_result":
          return {
            ...state,
            nightResults: [...state.nightResults, ev.data],
            players: ev.data.killedId != null
              ? state.players.map((p) =>
                  p.id === ev.data.killedId
                    ? { ...p, alive: false, eliminatedPhase: "night_kill" }
                    : p
                )
              : state.players,
          };

        case "game_over":
          return {
            ...state,
            winner: ev.data.winner,
            phase: "game_over",
            players: ev.data.players,
          };

        default:
          return state;
      }
    }

    default:
      return state;
  }
}

export function useGameState() {
  return useReducer(reducer, initialState);
}
