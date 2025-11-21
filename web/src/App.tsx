import { useMemo, useState } from "react";

type Phase = "idle" | "queued" | "running" | "packaging" | "success" | "error";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

const statusLabels: Record<Phase, string> = {
  idle: "Ready",
  queued: "Queued",
  running: "Parsing & Validating",
  packaging: "Packaging",
  success: "Done",
  error: "Error",
};

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [pastedText, setPastedText] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [download, setDownload] = useState<{ url: string; name: string } | null>(
    null
  );

  const canSubmit = useMemo(
    () => !!selectedFile || pastedText.trim().length > 0,
    [selectedFile, pastedText]
  );

  const handleSubmit = async () => {
    if (!canSubmit || isSubmitting) return;
    setIsSubmitting(true);
    setDownload(null);
    setError("");
    setPhase("queued");

    const formData = new FormData();
    if (selectedFile) {
      formData.append("file", selectedFile);
    } else if (pastedText.trim()) {
      formData.append("text", pastedText.trim());
    }

    try {
      setPhase("running");
      const response = await fetch(`${API_BASE}/api/quiz`, {
        method: "POST",
        body: formData,
      });

      setPhase("packaging");

      if (!response.ok) {
        let detail = "QuizForge failed to process the request.";
        try {
          const data = await response.json();
          detail = data?.detail ?? detail;
        } catch {
          detail = await response.text();
        }
        throw new Error(detail || "QuizForge failed to process the request.");
      }

      const blob = await response.blob();
      const contentDisposition = response.headers.get("content-disposition") || "";
      const nameMatch = contentDisposition.match(/filename=\"?(.+?)\"?$/i);
      const filename = nameMatch?.[1] ?? "quizforge_export.zip";

      const url = URL.createObjectURL(blob);
      setDownload({ url, name: filename });
      setPhase("success");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Something went wrong. Try again.";
      setError(message);
      setPhase("error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPastedText("");
    setPhase("idle");
    setError("");
    setDownload(null);
  };

  const statusOrder: Phase[] = [
    "queued",
    "running",
    "packaging",
    "success",
    "error",
  ];

  return (
    <>
      <header>
        <h1>QuizForge</h1>
        <p>
          Upload or paste a QuizForge-ready TXT, and we&apos;ll return the same
          outputs as the CLI - packaged as a ZIP you can import into Canvas or print.
        </p>
      </header>

      <main className="layout">
        <div className="columns">
          <section className="card">
            <h2>Send a Quiz</h2>
            <p className="helper">
              Choose a `.txt` file or paste the contents. We run the existing
              orchestrator end-to-end and stream back the Finished_Exports folder
              as a ZIP.
            </p>

            <div className="input-stack">
              <div className="file-picker">
                <label htmlFor="quiz-file">
                  <strong>Upload TXT</strong>
                  <input
                    id="quiz-file"
                    type="file"
                    accept=".txt"
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      setSelectedFile(file ?? null);
                    }}
                  />
                </label>
                {selectedFile && (
                  <div className="small">
                    Selected: <strong>{selectedFile.name}</strong>
                  </div>
                )}
              </div>

              <div>
                <label htmlFor="quiz-text">
                  <strong>Or paste the TXT contents</strong>
                </label>
                <textarea
                  id="quiz-text"
                  className="textarea"
                  placeholder="Paste your QuizForge-ready TXT..."
                  value={pastedText}
                  onChange={(e) => setPastedText(e.target.value)}
                />
              </div>
            </div>

            <div className="actions" style={{ marginTop: "1rem" }}>
              <button
                className="primary"
                disabled={!canSubmit || isSubmitting}
                onClick={handleSubmit}
              >
                {isSubmitting ? "Queuing..." : "Queue Quiz"}
              </button>
              <button className="secondary" onClick={handleReset} disabled={isSubmitting}>
                Reset
              </button>
            </div>

            {error && <div className="alert">{error}</div>}
            {download && (
              <div className="downloads">
                <a
                  className="download-link"
                  href={download.url}
                  download={download.name}
                >
                  Download {download.name}
                </a>
                <div className="small">
                  Contains the same Finished_Exports structure the CLI writes locally.
                </div>
              </div>
            )}
          </section>

          <section className="card">
            <h2>Progress</h2>
            <p className="helper">
              We mirror the local flow: parse -> validate -> package -> archive. Jobs are
              processed synchronously and cleaned up after the ZIP streams.
            </p>
            <div className="status-track">
              {statusOrder.map((key) => {
                const active = phase === key;
                const success = phase === "success" && key === "success";
                const errorState = phase === "error" && key === "error";
                return (
                  <div
                    key={key}
                    className={`pill ${active ? "active" : ""} ${
                      success ? "success" : ""
                    } ${errorState ? "error" : ""}`}
                  >
                    {statusLabels[key as Phase]}
                  </div>
                );
              })}
            </div>
            <p className="small" style={{ marginTop: "0.75rem" }}>
              Nothing is persisted on the server: each request runs in a temp directory,
              produces Finished_Exports, zips, streams, and discards.
            </p>
          </section>
        </div>
      </main>
    </>
  );
}

export default App;
