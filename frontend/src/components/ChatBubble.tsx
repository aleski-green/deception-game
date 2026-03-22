import React from "react";

const PLAYER_COLORS: Record<number, string> = {
  0: "#e74c3c",
  1: "#3498db",
  2: "#2ecc71",
  3: "#f39c12",
  4: "#9b59b6",
};

interface ChatBubbleProps {
  senderId: number;
  senderName: string;
  content: string;
  isSystem?: boolean;
  align?: "left" | "right";
  badge?: string;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({
  senderId,
  senderName,
  content,
  isSystem,
  align = "left",
  badge,
}) => {
  if (isSystem) {
    return (
      <div className="chat-bubble system">
        <span className="system-text">{content}</span>
      </div>
    );
  }

  const color = PLAYER_COLORS[senderId] || "#888";

  return (
    <div className={`chat-bubble ${align}`}>
      <div className="bubble-header">
        <span className="sender-name" style={{ color }}>
          {senderName}
        </span>
        {badge && <span className="role-badge">{badge}</span>}
      </div>
      <div className="bubble-content">{content}</div>
    </div>
  );
};
