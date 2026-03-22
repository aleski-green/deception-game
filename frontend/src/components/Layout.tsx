import React from "react";
import type { GameState } from "../types/game";
import { GameStatusBar } from "./GameStatusBar";
import { AgentThoughts } from "./AgentThoughts";
import { FreechatPanel } from "./FreechatPanel";
import { GroupChat } from "./GroupChat";
import { VoteLog } from "./VoteLog";

interface Props {
  state: GameState;
}

export const Layout: React.FC<Props> = ({ state }) => {
  return (
    <div className="app-layout">
      <GameStatusBar state={state} />
      <div className="panels-grid">
        <AgentThoughts
          thoughts={state.thoughts}
          nightActions={state.nightActions}
          players={state.players}
        />
        <FreechatPanel
          freechats={state.freechats}
          players={state.players}
          currentRound={state.round}
        />
        <GroupChat
          pitches={state.pitches}
          voteResults={state.voteResults}
          nightResults={state.nightResults}
          players={state.players}
        />
        <VoteLog
          votes={state.votes}
          voteResults={state.voteResults}
          players={state.players}
          currentRound={state.round}
        />
      </div>
    </div>
  );
};
