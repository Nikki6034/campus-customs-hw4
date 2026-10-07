import { Link } from "react-router-dom";
import { formatPrice } from "../api/client";
import { useCart } from "./context";

// Slide-out bag. Opens when an item is added, lists the bag with quantity
// controls and a subtotal. Checkout is not part of this assignment, so the
// button is honest about that rather than being a dead control.
export default function CartDrawer() {
  const { items, isOpen, close, remove, setQty, subtotal, count } = useCart();

  if (!isOpen) return null;

  return (
    <div className="drawer-overlay" onClick={close}>
      <aside
        className="drawer"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Your bag"
      >
        <div className="drawer-head">
          <span>Your bag ({count})</span>
          <button type="button" onClick={close} aria-label="Close bag">
            ×
          </button>
        </div>

        {items.length === 0 ? (
          <div className="drawer-empty">
            <p>Your bag is empty.</p>
            <Link to="/products" className="btn btn-solid" onClick={close}>
              Shop the collection
            </Link>
          </div>
        ) : (
          <>
            <div className="drawer-items">
              {items.map((item) => (
                <div className="drawer-item" key={`${item.productId}-${item.size}`}>
                  <Link
                    to={`/products/${item.productId}`}
                    onClick={close}
                    className="drawer-thumb"
                  >
                    <img src={item.imageUrl} alt={item.name} />
                  </Link>
                  <div className="drawer-item-body">
                    <Link
                      to={`/products/${item.productId}`}
                      onClick={close}
                      className="drawer-item-name"
                    >
                      {item.name}
                    </Link>
                    <span className="drawer-item-size">Size {item.size}</span>
                    <div className="drawer-qty">
                      <button
                        type="button"
                        onClick={() => setQty(item.productId, item.size, item.qty - 1)}
                        aria-label="Decrease quantity"
                      >
                        −
                      </button>
                      <span>{item.qty}</span>
                      <button
                        type="button"
                        onClick={() => setQty(item.productId, item.size, item.qty + 1)}
                        aria-label="Increase quantity"
                      >
                        +
                      </button>
                      <button
                        type="button"
                        className="drawer-remove"
                        onClick={() => remove(item.productId, item.size)}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                  <span className="drawer-item-price">
                    {formatPrice(item.price * item.qty)}
                  </span>
                </div>
              ))}
            </div>

            <div className="drawer-foot">
              <div className="drawer-subtotal">
                <span>Subtotal</span>
                <span>{formatPrice(subtotal)}</span>
              </div>
              <button type="button" className="btn btn-solid btn-block" disabled>
                Checkout — coming soon
              </button>
              <p className="drawer-note">
                Taxes and shipping calculated at checkout.
              </p>
            </div>
          </>
        )}
      </aside>
    </div>
  );
}
