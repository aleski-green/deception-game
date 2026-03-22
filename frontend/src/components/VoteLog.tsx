import React, { useState } from "react";
import type { VoteEntry, VoteResult, Player } from "../types/game";

const PLAYER_COLORS: Record<number, string> = {
  0: "#e74c3c",
  1: "#3498db",
  2: "#2ecc71",
  3: "#f39c12",
  4: "#9b59b6",
};

interface Props {
  votes: VoteEntry[];
  voteResults: VoteResult[];
  players: Player[];
  currentRound: number;
}

export const VoteLog: React.FC<Props> = ({ votes, voteResults, players, currentRound }) => {
  const rounds = [...new Set(votes.map((v) => v.round))].sort();
  const [selectedRound, setSelectedRound] = useState<number>(currentRound || 1);

  // Update to latest round
  React.useEffect(() => {
    if (currentRound > 0) setSelectedRound(currentRound);
  }, [currentRound]);

  const roundVotes = votes.filter((v) => v.round === selectedRound);
  const roundResult = voteResults.find((vr) => vr.round === selectedRound);

  // Tally
  const tally: Record<number, number> = {};
  roundVotes.forEach((v) => {
    tally[v.targetId] = (tally[v.targetId] || 0) + 1;
  });

  return (
    <div className="panel vote-log">
      <div className="panel-header">
        <h3>Vote Log</h3>
        <select
          value={selectedRound}
          onChange={(e) => setSelectedRound(Number(e.target.value))}
          className="round-select"
        >
          {rounds.map((r) => (
            <option key={r} value={r}>Round {r}</option>
          ))}
          {rounds.length === 0 && <option value={1}>Round 1</option>}
        </select>
      </div>

      <div className="panel-body">
        {roundVotes.length === 0 && (
          <div className="empty-state">No votes yet.</div>
        )}

        {roundVotes.length > 0 && (
          <>
            <table className="vote-table">
              <thead>
                <tr>
                  <th>Voter</th>
                  <th>Voted For</th>
                </tr>
              </thead>
              <tbody>
                {roundVotes.map((v, i) => (
                  <tr key={i}>
                    <td style={{ color: PLAYER_COLORS[v.voterId] }}>
                      {v.voterName}
                    </td>
                    <td style={{ color: PLAYER_COLORS[v.targetId] }}>
                      {v.targetName}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="vote-tally">
              <h4>Tally</h4>
              {Object.entries(tally)
                .sort(([, a], [, b]) => b - a)
                .map(([pid, count]) => {
                  const player = players.find((p) => p.id === Number(pid));
                  return (
                    <div key={pid} className="tally-row">
                      <span style={{ color: PLAYER_COLORS[Number(pid)] }}>
                        {player?.name || `#${pid}`}
                      </span>
                      <span className="tally-count">
                        {"X".repeat(count)} ({count})
                      </span>
                    </div>
                  );
                })}
            </div>

            {roundResult && (
              <div className={`vote-result-box ${roundResult.eliminatedId != null ? "eliminated" : "no-elim"}`}>
                {roundResult.eliminatedId != null
                  ? `${roundResult.eliminatedName} eliminated - was ${roundResult.revealedRole?.toUpperCase()}`
                  : "No majority - nobody eliminated"}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
