import { useState } from "react";

const API_BASE_URL = "http://localhost:8000";

export default function Chatbot() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "bot",
      content: "Ask about deliveries, disputes, or invoice context.",
    },
  ]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) {
      return;
    }

    const nextMessages = [...messages, { role: "user", content: trimmed }];
    setMessages(nextMessages);
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: trimmed }),
      });

      if (!response.ok) {
        let errorMessage = "Chat request failed.";
        try {
          const errorBody = await response.json();
          errorMessage = errorBody.detail || errorBody.message || errorMessage;
        } catch {
          // Keep the fallback message when the backend does not return JSON.
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setMessages([...nextMessages, { role: "bot", content: data.response }]);
    } catch (chatError) {
      setMessages([
        ...nextMessages,
        {
          role: "bot",
          content: chatError.message || "Unable to fetch a response right now.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel chatbot-panel">
      <div className="panel-header">
        <p className="panel-kicker">Global Support</p>
        <h2>Chatbot</h2>
      </div>
      <div className="chat-window">
        {messages.map((entry, index) => (
          <div key={`${entry.role}-${index}`} className={`bubble ${entry.role}`}>
            {entry.content}
          </div>
        ))}
        {loading ? <div className="bubble bot loading">Processing...</div> : null}
      </div>
      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="What is my delivery status?"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
        />
        <button type="submit" disabled={loading}>
          Send
        </button>
      </form>
    </section>
  );
}
