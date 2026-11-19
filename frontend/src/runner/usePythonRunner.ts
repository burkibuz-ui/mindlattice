import { useCallback, useEffect, useRef, useState } from "react";
import type { WorkerMessage } from "./protocol";

export const RUN_TIMEOUT_MS = 5_000;

export type RunnerStatus = "loading" | "ready" | "running" | "failed";

export interface RunOutcome {
  stdout: string;
  error: string | null;
  timedOut: boolean;
  truncated: boolean;
}

function createWorker() {
  return new Worker(new URL("./python.worker.ts", import.meta.url), { type: "module" });
}

/**
 * Owns the Python worker. `run(code)` resolves with the program's output.
 * If the code runs longer than RUN_TIMEOUT_MS the worker is killed and a new one
 * is started; that is the only reliable way to stop an infinite loop.
 */
export function usePythonRunner() {
  const workerRef = useRef<Worker | null>(null);
  const pendingRef = useRef<{ id: number; resolve: (o: RunOutcome) => void; timer: number } | null>(null);
  const nextIdRef = useRef(1);
  const [status, setStatus] = useState<RunnerStatus>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);

  const start = useCallback(() => {
    const worker = createWorker();
    worker.onmessage = (event: MessageEvent<WorkerMessage>) => {
      const message = event.data;
      if (message.type === "ready") {
        setStatus("ready");
      } else if (message.type === "load-error") {
        setStatus("failed");
        setLoadError(message.message);
      } else {
        const pending = pendingRef.current;
        if (!pending || pending.id !== message.id) return;
        window.clearTimeout(pending.timer);
        pendingRef.current = null;
        setStatus("ready");
        pending.resolve({ stdout: message.stdout, error: message.error, timedOut: false,
          truncated: message.truncated });
      }
    };
    workerRef.current = worker;
    setStatus("loading");
  }, []);

  useEffect(() => {
    start();
    return () => workerRef.current?.terminate();
  }, [start]);

  const run = useCallback((code: string) => new Promise<RunOutcome>((resolve) => {
    const worker = workerRef.current;
    if (!worker || pendingRef.current) return;
    const id = nextIdRef.current++;
    const timer = window.setTimeout(() => {
      pendingRef.current = null;
      worker.terminate();
      start(); // fresh interpreter for the next run
      resolve({ stdout: "", error: null, timedOut: true, truncated: false });
    }, RUN_TIMEOUT_MS);
    pendingRef.current = { id, resolve, timer };
    setStatus("running");
    worker.postMessage({ id, code });
  }), [start]);

  return { status, loadError, run };
}
