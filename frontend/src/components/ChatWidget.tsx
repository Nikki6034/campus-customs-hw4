import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  sendChat,
  getChatHistory,
  formatPrice,
  type ChatProductCard,
} from "../api/client";
import { useChatResults } from "../chat/context";
import { useAuth } from "../auth/context";

type Message = {
  role: "user" | "assistant";
  content: string;
  products?: ChatProductCard[];
};

// Derive the product the shopper is viewing from the URL, so the agent can
// resolve "this"/"it" to the right item.
function currentProductIdFromPath(pathname: string): string | undefined {
  const match = pathname.match(/^\/products\/(.+)$/);
  return match ? decodeURIComponent(match[1]) : undefined;
}

// Calls the real backend chat route (the Pydantic AI shop agent). Sends the
// signed-in shopper's identity and the current page so the agent has memory and
// context; reloads saved history when a logged-in shopper opens the panel.
export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [historyLoadedFor, setHistoryLoadedFor] = useState<number | null>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { setResults } = useChatResults();
  const { user } = useAuth();

  function scrollToEnd() {
    requestAnimationFrame(() => {
      logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
    });
  }

  // When a logged-in shopper opens the panel, load their saved conversation
  // once so a returning customer sees where they left off.
  useEffect(() => {
    if (!open || !user || historyLoadedFor === user.id) return;
    let cancelled = false;
    getChatHistory(user.id, user.email)
      .then((past) => {
        if (cancelled) return;
        setMessages(
          past.map((m) => ({
            role: m.role,
            content: m.content,
            products: m.products,
          })),
        );
        setHistoryLoadedFor(user.id);
        scrollToEnd();
      })
      .catch(() => {
        /* a failed history load should not block chatting */
      });
    return () => {
      cancelled = true;
    };
  }, [open, user, historyLoadedFor]);

  // (Identity changes remount this component via its key in App, so there is no
  // need to reset state on logout here.)

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setDraft("");
    setBusy(true);
    scrollToEnd();

    try {
      const { reply, products } = await sendChat(text, {
        userId: user?.id,
        email: user?.email,
        currentProductId: currentProductIdFromPath(location.pathname),
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: reply, products },
      ]);
      // Push the matches onto the page and take the shopper to the grid, so a
      // question in chat updates the website — not just the chat bubble.
      if (products.length > 0) {
        setResults(text, products);
        navigate("/products");
      }
    } catch (err) {
      const detail = err instanceof Error ? err.message : String(err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Couldn't reach the shop assistant. ${detail}` },
      ]);
    } finally {
      setBusy(false);
      scrollToEnd();
    }
  }

  return (
    <div className="chat">
      {open && (
        <div className="chat-panel">
          <div className="chat-head">
            <span>Shop assistant</span>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </div>

          <div className="chat-log" ref={logRef}>
            {messages.length === 0 && (
              <p className="chat-empty">
                Ask about sizes, colours, or what to wear to The Game.
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`bubble-wrap ${m.role}`}>
                <div className={`bubble ${m.role}`}>{m.content}</div>
                {m.products && m.products.length > 0 && (
                  <div className="chat-cards">
                    {m.products.map((p) => (
                      <Link
                        key={p.product_id}
                        to={`/products/${p.product_id}`}
                        className="chat-card"
                        onClick={() => setOpen(false)}
                      >
                        <img src={p.image_url} alt={p.name} loading="lazy" />
                        <div className="chat-card-body">
                          <span className="chat-card-name">{p.name}</span>
                          <span className="chat-card-price">
                            {formatPrice(p.price)}
                            {!p.in_stock && <em className="chat-card-out"> · sold out</em>}
                          </span>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {busy && <div className="bubble assistant typing">…</div>}
          </div>

          <form className="chat-input" onSubmit={submit}>
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Ask about a product…"
              aria-label="Message"
            />
            <button type="submit" className="btn btn-solid" disabled={busy || !draft.trim()}>
              Send
            </button>
          </form>
        </div>
      )}

      <button type="button" className="chat-toggle" onClick={() => setOpen((v) => !v)}>
        {open ? "Close" : "Ask us anything"}
      </button>
    </div>
  );
}
