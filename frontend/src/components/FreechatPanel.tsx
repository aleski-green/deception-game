import React, { useState, useEffect, useRef } from "react";
import { ChatBubble } from "./ChatBubble";
import type { FreechatMsg, Player } from "../types/game";

interface Props {
  freechats: FreechatMsg[];
  players: Player[];
  currentRound: number;
}

export const FreechatPanel: React.FC<Props> = ({ freechats, players, currentRound }) => {
  const [selectedRound, setSelectedRound] = useState<number>(1);
  const [selectedPair, setSelectedPair] = useState<string>("all");
  const scrollRef = useRef<HTMLDivElement>(null);

  // Update selected round to latest
  useEffect(() => {
    if (currentRound > 0) setSelectedRound(currentRound);
  }, [currentRound]);

  const rounds = [...new Set(freechats.map((f) => f.round))].sort();

  const roundMsgs = freechats.filter((f) => f.round === selectedRound);

  // Get unique pairs for this round
  const pairs = new Set<string>();
  roundMsgs.forEach((m) => {
    const key = [Math.min(m.senderId, m.receiverId), Math.max(m.senderId, m.receiverId)].join("-");
    pairs.add(key);
  });

  const filtered =
    selectedPair === "all"
      ? roundMsgs
      : roundMsgs.filter((m) => {
          const key = [Math.min(m.senderId, m.receiverId), Math.max(m.senderId, m.receiverId)].join("-");
          return key === selectedPair;
        });

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [filtered.length]);

  return (
    <div className="panel freechat-panel">
      <div className="panel-header">
        <h3>P2P Chats</h3>
        <div className="filter-row">
          <select
            value={selectedRound}
            onChange={(e) => setSelectedRound(Number(e.target.value))}
            className="round-select"
          >
            {rounds.map((r) => (
              <option key={r} value={r}>
                Round {r}
              </option>
            ))}
            {rounds.length === 0 && <option value={1}>Round 1</option>}
          </select>
          <select
            value={selectedPair}
            onChange={(e) => setSelectedPair(e.target.value)}
            className="pair-select"
          >
            <option value="all">All Pairs</option>
            {[...pairs].map((pair) => {
              const [a, b] = pair.split("-").map(Number);
              const nameA = players.find((p) => p.id === a)?.name || `#${a}`;
              const nameB = players.find((p) => p.id === b)?.name || `#${b}`;
              return (
                <option key={pair} value={pair}>
                  {nameA} & {nameB}
                </option>
              );
            })}
          </select>
        </div>
      </div>

      <div className="panel-body" ref={scrollRef}>
        {filtered.length === 0 && (
          <div className="empty-state">No conversations yet.</div>
        )}
        {filtered.map((msg, i) => (
          <ChatBubble
            key={i}
            senderId={msg.senderId}
            senderName={msg.senderName}
            content={msg.content}
          />
        ))}
      </div>
    </div>
  );
};
