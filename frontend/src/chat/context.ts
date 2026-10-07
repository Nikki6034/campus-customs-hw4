import { createContext, useContext } from "react";
import type { ChatProductCard } from "../api/client";

// Shared store for the chat-driven product search. The chat widget writes the
// matches the agent returned; the Products page reads them and renders the grid,
// so a question in chat updates the page.
export type ChatResultsState = {
  query: string | null;
  products: ChatProductCard[];
  setResults: (query: string, products: ChatProductCard[]) => void;
  clear: () => void;
};

export const ChatResultsContext = createContext<ChatResultsState | null>(null);

export function useChatResults(): ChatResultsState {
  const ctx = useContext(ChatResultsContext);
  if (!ctx) throw new Error("useChatResults must be used within ChatResultsProvider");
  return ctx;
}
