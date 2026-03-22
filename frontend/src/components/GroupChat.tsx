import React, { useEffect, useRef } from "react";
import { ChatBubble } from "./ChatBubble";
import type { PitchMsg, VoteResult, NightResult, Player } from "../types/game";

interface Props {
  pitches: PitchMsg[];
  voteResults: VoteResult[];
  nightResults: NightResult[];
  players: Player[];
}

type TimelineItem =
  | { kind: "pitch"; data: PitchMsg; order: number }
  | { kind: "vote_result"; data: VoteResult; order: number }
  | { kind: "night_result"; data: NightResult; order: number };

export const GroupChat: React.FC<Props> = ({ pitches, voteResults, nightResults, players }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Build a timeline of all public events
  const items: TimelineItem[] = [];
  let order = 0;

  // Interleave by round
  const maxRound = Math.max(
    ...pitches.map((p) => p.round),
    ...voteResults.map((v) => v.round),
    ...nightResults.map((n) => n.round),
    0
  );

  for (let r = 1; r <= maxRound; r++) {
    const roundPitches = pitches.filter((p) => p.round === r);
    const roundVotes = voteResults.filter((v) => v.round === r);
    const roundNights = nightResults.filter((n) => n.round === r);

    for (const p of roundPitches) {
      items.push({ kind: "pitch", data: p, order: order++ });
    }
    for (const v of roundVotes) {
      items.push({ kind: "vote_result", data: v, order: order++ });
    }
    for (const n of roundNights) {
      items.push({ kind: "night_result", data: n, order: order++ });
    }
  }

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [items.length]);

  return (
    <div className="panel group-chat">
      <div className="panel-header">
        <h3>Group Chat</h3>
        <span className="subtitle">Pitches, votes & events</span>
      </div>

      <div className="panel-body" ref={scrollRef}>
        {items.length === 0 && (
          <div className="empty-state">Game events will appear here.</div>
        )}
        {items.map((item) => {
          if (item.kind === "pitch") {
            return (
              <ChatBubble
                key={`p-${item.order}`}
                senderId={item.data.speakerId}
                senderName={item.data.speakerName}
                content={item.data.content}
                badge={`R${item.data.round}`}
              />
            );
          }

          if (item.kind === "vote_result") {
            const vr = item.data;
            const text = vr.eliminatedId != null
              ? `Vote result: ${vr.eliminatedName} was eliminated! Revealed role: ${vr.revealedRole?.toUpperCase()}`
              : "Vote result: No majority reached. Nobody was eliminated.";
            return (
              <ChatBubble
                key={`vr-${item.order}`}
                senderId={-1}
                senderName="System"
                content={text}
                isSystem
              />
            );
          }

          if (item.kind === "night_result") {
            const nr = item.data;
            let text: string;
            if (nr.killedId != null) {
              text = `Morning: ${nr.killedName} was found dead during the night.`;
            } else if (nr.saved) {
              text = "Morning: Someone was attacked but the doctor saved them!";
            } else {
              text = "Morning: A peaceful night. Nobody was harmed.";
            }
            return (
              <ChatBubble
                key={`nr-${item.order}`}
                senderId={-1}
                senderName="System"
                content={text}
                isSystem
              />
            );
          }

          return null;
        })}
      </div>
    </div>
  );
};
