/// <reference lib="webworker" />
// Runs student code with Pyodide (CPython compiled to WebAssembly) inside a Web Worker.
// The worker keeps the page responsive, and the page can terminate it if the code never
// finishes (e.g. an infinite while loop). Nothing is ever sent to the server.

import type { PyodideAPI } from "pyodide";
import type { RunRequest, WorkerMessage } from "./protocol";

const MAX_OUTPUT_CHARS = 10_000;
const PYODIDE_URL = `${self.location.origin}${import.meta.env.BASE_URL}pyodide/`;

const scope = self as unknown as DedicatedWorkerGlobalScope;
const send = (message: WorkerMessage) => scope.postMessage(message);

let output: string[] = [];
let outputLength = 0;
let truncated = false;

function collect(line: string) {
  if (outputLength >= MAX_OUTPUT_CHARS) {
    truncated = true;
    return;
  }
  output.push(line);
  outputLength += line.length + 1;
}

/** Keep only the part of the traceback that points at the student's code. */
function cleanTraceback(message: string): string {
  const lines = message.trimEnd().split("\n");
  const start = lines.findIndex((line) => line.includes('File "<exec>"'));
  const relevant = start === -1 ? lines.slice(-1) : lines.slice(start);
  return relevant.map((line) => line.replace('File "<exec>", ', "")).join("\n");
}

async function boot(): Promise<PyodideAPI> {
  const { loadPyodide } = await import(/* @vite-ignore */ `${PYODIDE_URL}pyodide.mjs`);
  const pyodide: PyodideAPI = await loadPyodide({ indexURL: PYODIDE_URL });
  pyodide.setStdout({ batched: collect });
  pyodide.setStderr({ batched: collect });
  pyodide.setStdin({
    stdin: () => {
      throw new Error("input() is not supported here. Put the values directly in your code.");
    },
  });
  return pyodide;
}

const ready = boot();
ready.then(
  () => send({ type: "ready" }),
  (error: Error) => send({ type: "load-error", message: error.message }),
);

scope.onmessage = async (event: MessageEvent<RunRequest>) => {
  const { id, code } = event.data;
  const pyodide = await ready;
  output = [];
  outputLength = 0;
  truncated = false;

  // A fresh namespace for every run, so variables from the previous run don't leak in.
  const globals = pyodide.globals.get("dict")();
  let error: string | null = null;
  try {
    await pyodide.runPythonAsync(code, { globals });
  } catch (e) {
    error = cleanTraceback((e as Error).message);
  } finally {
    globals.destroy();
  }
  send({ type: "result", id, stdout: output.join("\n"), error, truncated });
};
