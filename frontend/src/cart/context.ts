import { createContext, useContext } from "react";

export type CartItem = {
  productId: string;
  name: string;
  imageUrl: string;
  price: number;
  size: string;
  qty: number;
};

export type CartState = {
  items: CartItem[];
  isOpen: boolean;
  add: (item: Omit<CartItem, "qty">, qty?: number) => void;
  remove: (productId: string, size: string) => void;
  setQty: (productId: string, size: string, qty: number) => void;
  clear: () => void;
  open: () => void;
  close: () => void;
  count: number;
  subtotal: number;
};

export const CartContext = createContext<CartState | null>(null);
export const CART_STORAGE_KEY = "campus-customs-cart";

export function useCart(): CartState {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
}
