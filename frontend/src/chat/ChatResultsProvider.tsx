import { useMemo, useState, type ReactNode } from "react";
import type { ChatProductCard } from "../api/client";
import { ChatResultsContext, type ChatResultsState } from "./context";

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [query, setQuery] = useState<string | null>(null);
  const [products, setProducts] = useState<ChatProductCard[]>([]);

  const value = useMemo<ChatResultsState>(
    () => ({
      query,
      products,
      setResults: (q, p) => {
        setQuery(q);
        setProducts(p);
      },
      clear: () => {
        setQuery(null);
        setProducts([]);
      },
    }),
    [query, products],
  );

  return (
    <ChatResultsContext.Provider value={value}>
      {children}
    </ChatResultsContext.Provider>
  );
}
