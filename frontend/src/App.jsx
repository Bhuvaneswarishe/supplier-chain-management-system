import Chatbot from "./components/Chatbot";
import DeliveryUpload from "./components/DeliveryUpload";

export default function App() {
  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">Supply Chain Management</p>
        <h1>Delivery mismatch handling and support chat in one shared console.</h1>
        <p className="hero-copy">
          Upload a delivery note for validation, then use the support bot to ask
          about delivery history, disputes, and invoice-backed context.
        </p>
      </section>
      <section className="content-grid">
        <DeliveryUpload />
        <Chatbot />
      </section>
    </main>
  );
}
