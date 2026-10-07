import {
  BrowserRouter,
  Route,
  Routes,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { useAuth } from "./auth/context";
import { ChatResultsProvider } from "./chat/ChatResultsProvider";
import { CartProvider } from "./cart/CartProvider";
import CartDrawer from "./cart/CartDrawer";
import NavBar from "./components/NavBar";
import ChatWidget from "./components/ChatWidget";
import Home from "./pages/Home";
import Products from "./pages/Products";
import ProductDetail from "./pages/ProductDetail";
import About from "./pages/About";
import Login from "./pages/Login";
import CreateAccount from "./pages/CreateAccount";
import "./App.css";

// Remount the detail page per product so its state starts clean.
function KeyedProductDetail() {
  const { productId = "" } = useParams();
  return <ProductDetail key={productId} />;
}

// Remount the chat widget when the signed-in shopper changes, so one customer's
// loaded history never carries over to another (or to a guest).
function KeyedChatWidget() {
  const { user } = useAuth();
  return <ChatWidget key={user?.id ?? "guest"} />;
}

// Remount Products when the ?q= search param changes (e.g. a "Shop by" tile),
// so the search box re-seeds from the URL without a sync effect.
function KeyedProducts() {
  const [searchParams] = useSearchParams();
  return <Products key={searchParams.get("q") ?? ""} />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
      <CartProvider>
      <ChatResultsProvider>
      <NavBar />
      <main className="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<KeyedProducts />} />
          <Route path="/products/:productId" element={<KeyedProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
        </Routes>
      </main>
      <footer className="footer">
        <p>Campus Customs · New Haven, Connecticut</p>
      </footer>
      <KeyedChatWidget />
      <CartDrawer />
      </ChatResultsProvider>
      </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
