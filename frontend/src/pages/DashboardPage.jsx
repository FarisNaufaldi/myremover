import React, { useCallback, useEffect, useRef, useState } from "react";
import api from "../api/client.js";
import UploadZone from "../components/background-remover/UploadZone.jsx";
import ImagePreview from "../components/background-remover/ImagePreview.jsx";
import ProcessingState from "../components/background-remover/ProcessingState.jsx";
import BeforeAfterViewer from "../components/background-remover/BeforeAfterViewer.jsx";
import ResultActions from "../components/background-remover/ResultActions.jsx";

const STAGES = [
  "Preparing image…",
  "Analyzing subject…",
  "Removing background…",
  "Refining edges…",
  "Finalizing result…",
];

function formatBytes(n) {
  if (!n && n !== 0) return "";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}

export default function DashboardPage() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [stageIdx, setStageIdx] = useState(0);
  const stageTimer = useRef(null);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      if (stageTimer.current) window.clearInterval(stageTimer.current);
    };
  }, [previewUrl]);

  const clearPreview = useCallback(() => {
    setPreviewUrl((url) => {
      if (url) URL.revokeObjectURL(url);
      return null;
    });
  }, []);

  const resetAll = useCallback(() => {
    clearPreview();
    setFile(null);
    setResult(null);
    setError(null);
    setProcessing(false);
    setStageIdx(0);
    if (stageTimer.current) {
      window.clearInterval(stageTimer.current);
      stageTimer.current = null;
    }
  }, [clearPreview]);

  const onFile = useCallback(
    (f) => {
      if (!f) return;
      setError(null);
      setResult(null);
      clearPreview();
      setFile(f);
      setPreviewUrl(URL.createObjectURL(f));
    },
    [clearPreview],
  );

  const startStages = () => {
    setStageIdx(0);
    if (stageTimer.current) window.clearInterval(stageTimer.current);
    // Advance stage labels for UX while real work happens server-side
    // (no fake percentage — only message progression with a cap)
    stageTimer.current = window.setInterval(() => {
      setStageIdx((i) => Math.min(i + 1, STAGES.length - 2));
    }, 2200);
  };

  const stopStages = (final = true) => {
    if (stageTimer.current) {
      window.clearInterval(stageTimer.current);
      stageTimer.current = null;
    }
    if (final) setStageIdx(STAGES.length - 1);
  };

  const process = async () => {
    if (!file || processing) return;
    setError(null);
    setProcessing(true);
    startStages();
    try {
      const data = await api.removeBackground(file);
      stopStages(true);
      const dataUrl = `data:image/png;base64,${data.image_base64}`;
      setResult({
        ...data,
        dataUrl,
      });
    } catch (err) {
      stopStages(false);
      setError(err.message || "Something went wrong while processing your image. Please try again.");
    } finally {
      setProcessing(false);
    }
  };

  const download = () => {
    if (!result?.dataUrl) return;
    const a = document.createElement("a");
    a.href = result.dataUrl;
    a.download = result.filename || "image-no-bg.png";
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  return (
    <div className="space-y-8">
      <header className="flex flex-col items-start gap-3">
        <span className="pill">Background Remover</span>
        <h1 className="display-heading text-[44px] leading-[1.05] md:text-[56px]">
          Background <span className="emphasis">Remover</span>
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-slate-400 md:text-base">
          Remove image backgrounds with AI.
        </p>
      </header>

      {!result && !processing && (
        <div className="space-y-5">
          {!file ? (
            <UploadZone onFile={onFile} onError={setError} />
          ) : (
            <ImagePreview
              file={file}
              previewUrl={previewUrl}
              sizeLabel={formatBytes(file.size)}
              onRemove={resetAll}
              onProcess={process}
              processing={processing}
            />
          )}
        </div>
      )}

      {processing && (
        <ProcessingState stage={STAGES[stageIdx]} filename={file?.name} />
      )}

      {error && (
        <div
          role="alert"
          className="card border-rose-500/40 text-sm text-rose-300"
        >
          {error}
        </div>
      )}

      {result && previewUrl && (
        <div className="space-y-6">
          <div>
            <span className="pill">Background Removed</span>
            <h2 className="display-heading mt-3 text-3xl md:text-4xl">
              Clean cutout, ready to <span className="emphasis">download</span>
            </h2>
          </div>
          <BeforeAfterViewer
            beforeUrl={previewUrl}
            afterUrl={result.dataUrl}
            width={result.width}
            height={result.height}
          />
          <ResultActions
            onDownload={download}
            onAnother={resetAll}
            meta={`${result.width}×${result.height} · ${formatBytes(result.size_bytes)} · PNG`}
          />
        </div>
      )}
    </div>
  );
}
