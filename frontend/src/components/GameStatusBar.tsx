import React from "react";
import type { GameState } from "../types/game";

const API = "http://localhost:8000/api";

const ROLE_COLORS: Record<string, string> = {
  impostor: "#e74c3c",
  detective: "#58a6ff",
  doctor: "#3fb950",
  civilian: "#8b949e",
};

const ROLE_EMOJI: Record<string, string> = {
  impostor: "\u{1F5E1}",
  detective: "\u{1F50D}",
  doctor: "\u{1FA7A}",
  civilian: "\u{1F464}",
};

interface Props {
  state: GameState;
}

export const GameStatusBar: React.FC<Props> = ({ state }) => {
  const startGame = async () => {
    await fetch(`${API}/game/start`, { method: "POST" });
    await fetch(`${API}/game/run`, { method: "POST" });
  };

  const pauseGame = () => fetch(`${API}/game/pause`, { method: "POST" });
  const resumeGame = () => fetch(`${API}/game/run`, { method: "POST" });
  const stopGame = () => fetch(`${API}/game/stop`, { method: "POST" });

  const phaseLabel: Record<string, string> = {
    waiting: "Waiting",
    started: "Ready",
    freechat: "Free Chat",
    pitch: "Public Pitch",
    vote: "Voting",
    night: "Night",
    game_over: "Game Over",
  };

  const phaseColor: Record<string, string> = {
    waiting: "#666",
    started: "#3498db",
    freechat: "#2ecc71",
    pitch: "#f39c12",
    vote: "#e74c3c",
    night: "#2c3e50",
    game_over: "#9b59b6",
  };

  return (
    <div className="status-bar">
      <div className="status-left">
        <span
          className="connection-dot"
          style={{ background: state.connected ? "#2ecc71" : "#e74c3c" }}
        />
        <span className="status-label">
          Round {state.round} &mdash;{" "}
          <span style={{ color: phaseColor[state.phase] || "#fff" }}>
            {phaseLabel[state.phase] || state.phase}
          </span>
        </span>
      </div>

      <div className="status-center">
        {state.players.map((p) => (
          <span
            key={p.id}
            className={`player-chip ${p.alive === false ? "dead" : "alive"}`}
            style={{
              borderColor: ROLE_COLORS[p.role] || "#8b949e",
              borderWidth: "2px",
              borderStyle: "solid",
            }}
            title={`${p.name} - ${p.role}${p.alive === false ? " (eliminated)" : ""}`}
          >
            <span className="role-icon">{ROLE_EMOJI[p.role] || ""}</span>
            {p.name}
            {p.alive === false && (
              <span className="role-reveal"> ({p.role})</span>
            )}
          </span>
        ))}
      </div>

      <div className="status-right">
        {state.winner && (
          <span className="winner-badge">
            {state.winner === "civilians" ? "Civilians Win!" : "Impostor Wins!"}
          </span>
        )}
        {state.phase === "waiting" || state.phase === "game_over" ? (
          <button className="btn btn-start" onClick={startGame}>
            {state.phase === "game_over" ? "New Game" : "Start Game"}
          </button>
        ) : (
          <>
            <button className="btn btn-pause" onClick={pauseGame}>
              Pause
            </button>
            <button className="btn btn-stop" onClick={stopGame}>
              Stop
            </button>
          </>
        )}
      </div>
    </div>
  );
};
