import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  CartContext,
  CART_STORAGE_KEY,
  type CartItem,
  type CartState,
} from "./context";

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>(() => {
    try {
      const raw = localStorage.getItem(CART_STORAGE_KEY);
      return raw ? (JSON.parse(raw) as CartItem[]) : [];
    } catch {
      return [];
    }
  });
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  const value = useMemo<CartState>(() => {
    const key = (id: string, size: string) => `${id}__${size}`;
    return {
      items,
      isOpen,
      add: (item, qty = 1) =>
        setItems((prev) => {
          const i = prev.findIndex(
            (p) => key(p.productId, p.size) === key(item.productId, item.size),
          );
          if (i === -1) return [...prev, { ...item, qty }];
          const next = [...prev];
          next[i] = { ...next[i], qty: next[i].qty + qty };
          return next;
        }),
      remove: (productId, size) =>
        setItems((prev) =>
          prev.filter((p) => key(p.productId, p.size) !== key(productId, size)),
        ),
      setQty: (productId, size, qty) =>
        setItems((prev) =>
          prev
            .map((p) =>
              key(p.productId, p.size) === key(productId, size)
                ? { ...p, qty: Math.max(1, qty) }
                : p,
            )
            .filter((p) => p.qty > 0),
        ),
      clear: () => setItems([]),
      open: () => setIsOpen(true),
      close: () => setIsOpen(false),
      count: items.reduce((n, p) => n + p.qty, 0),
      subtotal: items.reduce((s, p) => s + p.price * p.qty, 0),
    };
  }, [items, isOpen]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}
