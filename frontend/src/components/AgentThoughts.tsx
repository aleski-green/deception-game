import React, { useState, useEffect, useRef } from "react";
import type { ThoughtEntry, NightAction, Player } from "../types/game";

const PLAYER_COLORS: Record<number, string> = {
  0: "#e74c3c",
  1: "#3498db",
  2: "#2ecc71",
  3: "#f39c12",
  4: "#9b59b6",
};

interface Props {
  thoughts: ThoughtEntry[];
  nightActions: NightAction[];
  players: Player[];
}

export const AgentThoughts: React.FC<Props> = ({ thoughts, nightActions, players }) => {
  const [selectedAgent, setSelectedAgent] = useState<number>(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  const filtered = thoughts.filter((t) => t.agentId === selectedAgent);
  const filteredNight = nightActions.filter((a) => a.agentId === selectedAgent);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [filtered.length, filteredNight.length]);

  const selectedPlayer = players.find((p) => p.id === selectedAgent);

  return (
    <div className="panel agent-thoughts">
      <div className="panel-header">
        <h3>Agent Thoughts</h3>
        <select
          value={selectedAgent}
          onChange={(e) => setSelectedAgent(Number(e.target.value))}
          className="agent-select"
        >
          {players.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} {p.alive === false ? "(dead)" : ""}
            </option>
          ))}
        </select>
      </div>

      {selectedPlayer && (
        <div className="agent-info">
          <span style={{ color: PLAYER_COLORS[selectedAgent] }}>
            {selectedPlayer.name}
          </span>
          <span className="role-tag">{selectedPlayer.role}</span>
          {selectedPlayer.alive === false && <span className="dead-tag">ELIMINATED</span>}
        </div>
      )}

      <div className="panel-body" ref={scrollRef}>
        {filtered.length === 0 && filteredNight.length === 0 && (
          <div className="empty-state">No thoughts yet. Start a game!</div>
        )}

        {filtered.map((t, i) => (
          <div key={`t-${i}`} className="thought-entry">
            <div className="thought-meta">
              Round {t.round} &middot; {t.phase}
            </div>
            <div className="thought-text">{t.thought}</div>
            {t.strategy && (
              <div className="thought-strategy">
                Strategy: {t.strategy}
              </div>
            )}
            {Object.keys(t.suspicions).length > 0 && (
              <div className="suspicion-bars">
                {Object.entries(t.suspicions).map(([pid, level]) => {
                  const player = players.find((p) => p.id === Number(pid));
                  const pct = Math.round(Number(level) * 100);
                  return (
                    <div key={pid} className="suspicion-row">
                      <span className="suspicion-name">
                        {player?.name || `#${pid}`}
                      </span>
                      <div className="suspicion-bar-bg">
                        <div
                          className="suspicion-bar-fill"
                          style={{
                            width: `${pct}%`,
                            background:
                              pct > 70 ? "#e74c3c" : pct > 40 ? "#f39c12" : "#2ecc71",
                          }}
                        />
                      </div>
                      <span className="suspicion-pct">{pct}%</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}

        {filteredNight.map((a, i) => (
          <div key={`n-${i}`} className="thought-entry night-action">
            <div className="thought-meta">
              Round {a.round} &middot; Night &middot; {a.action}
            </div>
            <div className="thought-text">
              {a.action === "kill" && `Chose to eliminate ${a.targetName}`}
              {a.action === "heal" && `Protected ${a.targetName}`}
              {a.action === "investigate" && (
                <>
                  Investigated {a.targetName}
                  {a.result && <span className="investigate-result"> &mdash; {a.result}</span>}
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
