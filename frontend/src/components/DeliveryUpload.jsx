import { useState } from "react";

const API_BASE_URL = "http://localhost:8000";

export default function DeliveryUpload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      setError("Please choose a delivery note to upload.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE_URL}/upload-delivery-note`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = "Upload failed.";
        try {
          const errorBody = await response.json();
          errorMessage = errorBody.detail || errorBody.message || errorMessage;
        } catch {
          // Keep the fallback message when the backend does not return JSON.
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setResult(data);
    } catch (submissionError) {
      setError(submissionError.message || "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const cardState = result?.status === "matched" ? "matched" : result ? "disputed" : "";

  return (
    <section className={`panel ${cardState}`}>
      <div className="panel-header">
        <p className="panel-kicker">Module 5</p>
        <h2>DeliveryUpload</h2>
      </div>
      <form className="upload-form" onSubmit={handleSubmit}>
        <label className="upload-input">
          <span>PDF, DOCX, or image</span>
          <input
            type="file"
            accept=".pdf,.docx,.png,.jpg,.jpeg"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Processing..." : "Upload delivery note"}
        </button>
      </form>
      {error ? <p className="message error">{error}</p> : null}
      {result ? (
        <div className="result-block">
          <p className="status-line">
            Status: <strong>{result.status}</strong>
          </p>
          <p>Delivery ID: {result.delivery_id}</p>
          <p>Issues: {result.issues.length ? result.issues.join(", ") : "None"}</p>
        </div>
      ) : null}
    </section>
  );
}
