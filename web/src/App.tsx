import { useMemo, useState, useEffect } from "react";

type Phase = "idle" | "queued" | "running" | "packaging" | "success" | "error";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

const statusLabels: Record<Phase, string> = {
  idle: "Ready when you are",
  queued: "Working",
  running: "Building",
  packaging: "Finishing up",
  success: "Done",
  error: "Error",
};

function App() {
  const templateUrl = "/qf_base_module.txt";
  const steps = [
    <>
      Download the <a href={templateUrl}>QuizForge Base module</a> and drop it in your AI chat.
    </>,
    <>
      Copy your AI assistant&apos;s response and paste it in. Or, if you downloaded the quiz in TXT
      format, attach it with the “Choose File” button.
    </>,
    <>
      Click “Go”. You will either get a .ZIP with all your goodies or an error message to copy/paste
      back to your AI to fix the problem.
    </>,
    <>Un-ZIP the download to see your Canvas import and print-ready docs.</>,
  ];
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [pastedText, setPastedText] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [download, setDownload] = useState<{ url: string; name: string } | null>(
    null
  );
  const [pendingDownload, setPendingDownload] = useState<{ url: string; name: string } | null>(
    null
  );
  const [warnings, setWarnings] = useState<string[]>([]);
  const [reviewPrompt, setReviewPrompt] = useState<string | null>(null);
  const [reviewType, setReviewType] = useState<"fail" | "warning" | null>(null);
  const [buildInfo, setBuildInfo] = useState<string>("");

  const canSubmit = useMemo(
    () => !!selectedFile || pastedText.trim().length > 0,
    [selectedFile, pastedText]
  );

  const handleSubmit = async () => {
    if (!canSubmit || isSubmitting) return;
    setIsSubmitting(true);
    setDownload(null);
    setError("");
    setWarnings([]);
    setReviewPrompt(null);
    setReviewType(null);
    setPendingDownload(null);
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

      // Capture warnings from headers (if any)
      const warningHeader = response.headers.get("x-quizforge-warnings");
      if (warningHeader) {
        try {
          const parsed = JSON.parse(decodeURIComponent(warningHeader));
          if (Array.isArray(parsed)) {
            setWarnings(parsed as string[]);
          }
        } catch {
          // ignore parse errors
        }
      }

      const blob = await response.blob();
      const contentDisposition = response.headers.get("content-disposition") || "";
      const nameMatch = contentDisposition.match(/filename=\"?(.+?)\"?$/i);
      const filename = nameMatch?.[1] ?? "quizforge_export.zip";

      const url = URL.createObjectURL(blob);
      // If warnings exist, require user confirmation before exposing download
      if (warnings.length) {
        setPendingDownload({ url, name: filename });
        setReviewType("warning");
        setReviewPrompt(
          ["Warnings detected:", ...warnings.map((w, i) => `${i + 1}. ${w}`)].join("\n")
        );
        setPhase("success");
      } else {
        setDownload({ url, name: filename });
        setPhase("success");
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Something went wrong. Try again.";
      setError(message);
      // Treat error detail as a fail prompt when present
      if (message) {
        setReviewType("fail");
        setReviewPrompt(message);
      }
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
    setWarnings([]);
    setDownload(null);
    setPendingDownload(null);
    setReviewPrompt(null);
    setReviewType(null);
  };

  const progressValue = (() => {
    switch (phase) {
      case "idle":
        return 0;
      case "queued":
        return 25;
      case "running":
        return 55;
      case "packaging":
        return 85;
      case "success":
        return 100;
      case "error":
        return 100;
      default:
        return 0;
    }
  })();

  // Fetch build info for display
  useEffect(() => {
    fetch(`${API_BASE || ""}/api/health`)
      .then((res) => res.json())
      .then((data) => {
        if (data?.build) {
          const b = data.build;
          const parts = [];
          if (b.ref) parts.push(b.ref);
          if (b.sha) parts.push(b.sha.substring(0, 7));
          if (b.time) parts.push(b.time);
          setBuildInfo(parts.join(" · "));
        }
      })
      .catch(() => {});
  }, []);

  return (
    <>
      {reviewPrompt && (
        <div className="modal-backdrop">
          <div className="modal">
            <h3>{reviewType === "fail" ? "Processing failed" : "Warnings detected"}</h3>
            <pre className="modal-body">{reviewPrompt}</pre>
            <div className="modal-actions">
              {reviewType === "warning" && pendingDownload && (
                <>
                  <button
                    className="primary"
                    onClick={() => {
                      setDownload(pendingDownload);
                      setPendingDownload(null);
                      setReviewPrompt(null);
                      setReviewType(null);
                    }}
                  >
                    Proceed to download
                  </button>
                  <button
                    className="secondary"
                    onClick={() => {
                      setPendingDownload(null);
                      setReviewPrompt(null);
                      setReviewType(null);
                    }}
                  >
                    Cancel
                  </button>
                </>
              )}
              {reviewType === "fail" && (
                <button
                  className="primary"
                  onClick={() => {
                    setReviewPrompt(null);
                    setReviewType(null);
                  }}
                >
                  Close
                </button>
              )}
            </div>
          </div>
        </div>
      )}
      <header>
        <h1>QuizForge - Using AI to create Canvas New Quizzes and more!</h1>
        <p className="eyebrow">
          Load the <a href={templateUrl}>QuizForge Base module</a> to turn any AI into your Teaching
          Assistant.
        </p>
      </header>

      <main className="layout">
        <div className="columns two-col">
          <section className="card steps-card">
            <h2>How QuizForge works</h2>
            <ol className="steps">
              {steps.map((text, idx) => (
                <li key={text}>
                  <span className="step-number">{idx + 1}</span>
                  <span className="step-text">{text}</span>
                </li>
              ))}
            </ol>
            <div className="feature-block">
              <h3>Teachers can:</h3>
              <ul className="feature-list">
                <li>Create fresh quizzes from scratch.</li>
                <li>Convert existing quizzes from documents or even photos.</li>
                <li>Give the AI unit plans or standards to improve pedagogy.</li>
              </ul>
            </div>
            <div className="feature-block">
              <h3>Built-in pedagogy:</h3>
              <ul className="feature-list">
                <li>Depth of Knowledge alignment.</li>
                <li>Tiers of Intervention (1-3) on request.</li>
                <li>Bloom&apos;s Taxonomy targeting.</li>
                <li>Clear rationales for every scored item.</li>
              </ul>
            </div>
          </section>

          <section className="card emphasis">
            <div className="input-header">
              <div>
                <h2>Paste here (or upload)</h2>
                <p className="helper">
                  Paste is easiest. Upload works too. Click Go and we&apos;ll build your
                  Canvas-ready ZIP and docs.
                </p>
              </div>
              <a className="tiny-link" href={templateUrl} download>
                Need the format? Download QF_Base
              </a>
            </div>

            <div className="input-stack">
              <div className="textarea-wrap">
                <label htmlFor="quiz-text">
                  <strong>Paste your quiz text</strong>
                </label>
                <textarea
                  id="quiz-text"
                  className="textarea"
                  placeholder="Paste the text you copied from your AI (between the QUIZFORGE tags)..."
                  value={pastedText}
                  onChange={(e) => setPastedText(e.target.value)}
                />
              </div>

              <div className="file-picker">
                <label htmlFor="quiz-file">
                  <strong>Or upload a TXT file</strong>
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
            </div>

            <div className="actions" style={{ marginTop: "1rem" }}>
              <button
                className="primary"
                disabled={!canSubmit || isSubmitting}
                onClick={handleSubmit}
              >
                {isSubmitting ? "Working..." : "Go"}
              </button>
              <button className="secondary" onClick={handleReset} disabled={isSubmitting}>
                Reset
              </button>
            </div>

            <div className="progress-wrap">
              <div className="progress-label">
                {phase === "idle" ? "Waiting for your quiz" : statusLabels[phase]}
              </div>
              <div className="progress-bar">
                <div
                  className={`progress-fill ${phase === "error" ? "error" : ""} ${
                    phase === "success" ? "success" : ""
                  }`}
                  style={{ width: `${progressValue}%` }}
                />
              </div>
            </div>

            {error && <div className="alert">{error}</div>}
            {warnings.length > 0 && (
              <div className="alert warning">
                <strong>Warnings detected:</strong>
                <ul>
                  {warnings.map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
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
                  Contains Canvas New Quiz import and printable docs.
                </div>
              </div>
            )}
          </section>
        </div>
        <section className="card howto-card">
          <h2>How to import to Canvas</h2>
          <ol className="howto-list">
            <li>
              <strong>Step 1 - Unzip the file from QuizForge.</strong> Right-click the download and
              choose <em>Extract All</em>. Inside the new folder you&apos;ll see: a DOCX to print,
              an answer key for scoring, a rationales file for students, and a QTI-ZIP for Canvas.
            </li>
            <li>
              <strong>Step 2 - Create a new Canvas &quot;New Quiz&quot;.</strong>
            </li>
            <li>
              <strong>Step 3 - Click &quot;Build&quot;.</strong>
            </li>
            <li>
              <strong>Step 4 - Click the 3 vertical dots and choose &quot;Import content&quot;.</strong>
            </li>
            <li>
              <strong>Step 5 - Navigate to the folder you just unzipped.</strong>
            </li>
            <li>
              <strong>Step 6 - Select the QTI-ZIP with your quiz&apos;s name.</strong>
            </li>
            <li>
              <strong>Step 7 - Import, save, publish.</strong>
            </li>
          </ol>
        </section>
        <footer className="footer">
          <a href="https://www.github.com/longhornadam/quizforge" target="_blank" rel="noreferrer">
            View QuizForge on GitHub
          </a>
          {buildInfo && (
            <span className="small" style={{ float: "right" }}>
              Build: {buildInfo}
            </span>
          )}
        </footer>
      </main>
    </>
  );
}

export default App;
