import { useMemo, useState, useEffect } from "react";
import logo from "../images/quizforge_logo.png";

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
  const templateUrl = "/LLM_Modules/QuizForge_Base.md";
  const exampleUrl = "/llm_modules/example_quiz_all_types.txt";
  const steps = [
    <>Give your AI-Teaching Assistant (AI-TA) the <a href={templateUrl}>QuizForge Base module</a>.</>,
    <>Talk to your AI-TA about what quiz you need. The more information, the better!</>,
    <>Copy your AI-TA&apos;s final output and paste it here.</>,
    <>Download the ZIP QuizForge provides and unZIP it (inside is your QuizName_QTI.zip).</>,
    <>Create/open a Canvas New Quiz, then load the inner QTI-ZIP (three dots to "Import Content").</>,
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
          ["Warnings detected: Copy/paste into your AI to fix", ...warnings.map((w, i) => `${i + 1}. ${w}`)].join("\n")
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
          setBuildInfo(parts.join(" - "));
        }
      })
      .catch(() => {});
  }, []);

  return (
    <>
      {reviewPrompt && (
        <div className="modal-backdrop">
          <div className="modal">
            <h3>
              {reviewType === "fail"
                ? "Processing failed"
                : "Warnings detected: Copy/paste into your AI to fix"}
            </h3>
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
          <div className="logo-row">
            <img src={logo} alt="QuizForge logo" className="logo" />
            <div className="taglines">
            <p className="headline">
              Load the <a href={templateUrl}>QuizForge Base module</a> to turn any AI into your
              Teaching Assistant (AI-TA).
            </p>
            <p className="headline">
              Get Canvas New Quizzes, printable doc versions, answer rationales for students, and
              answer keys.
            </p>
            <p className="headline">
              <a href="/ai-ta-tools.html">
                More AI-TA tools (AI-generated presentations, Gimkits, and Blookets!)
              </a>
            </p>
          </div>
        </div>
      </header>

      <main className="layout">
        <div className="columns two-col">
          <section className="card emphasis">
            <div className="input-header">
              <div>
                <h2>Paste here (or upload)</h2>
              </div>
            </div>

            <div className="input-stack">
              <div className="textarea-wrap">
                <textarea
                  id="quiz-text"
                  className="textarea"
                  aria-label="Paste quiz text"
                  placeholder="Paste the text you copied from your AI..."
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
              <div className="small">
                Need a pattern? Download the <a href={exampleUrl}>all-question-types example quiz</a>.
              </div>
              <div className="small">
                Need the format? Download the <a href={templateUrl}>QuizForge Base module</a>.
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
                <strong>Warnings detected: Copy/paste into your AI to fix</strong>
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
                  You get an outer ZIP with printables and an inner QuizName_QTI.zip. Import the
                  inner QTI file into Canvas.
                </div>
              </div>
            )}
          </section>
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
        </div>
        <div className="columns two-col">
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
          <section className="card howto-card">
            <h2>Question types at a glance</h2>
            <ul className="howto-list" style={{ listStyle: "none", paddingLeft: 0 }}>
              <li><strong>MC</strong> - Multiple choice, 1 correct.</li>
              <li><strong>MA</strong> - Multiple answers, select all that apply.</li>
              <li><strong>TF</strong> - True/False.</li>
              <li><strong>MATCHING</strong> - Pair terms with definitions.</li>
              <li><strong>FITB</strong> - Fill in the blanks with accepted answers.</li>
              <li><strong>ESSAY</strong> - Free-response, manual scoring.</li>
              <li><strong>FILEUPLOAD</strong> - Upload artifact (PDF/doc/image).</li>
              <li><strong>ORDERING</strong> - Arrange items in the correct sequence.</li>
              <li><strong>CATEGORIZATION</strong> - Sort items into categories.</li>
              <li><strong>NUMERICAL</strong> - Numeric response with tolerance/precision/range.</li>
              <li><strong>STIMULUS / STIMULUS_END</strong> - Passages that group related questions.</li>
            </ul>
          </section>
        </div>
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
