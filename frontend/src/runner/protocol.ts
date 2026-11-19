// Messages exchanged between the page and the Python worker.

export interface RunRequest {
  id: number;
  code: string;
}

export type WorkerMessage =
  | { type: "ready" }
  | { type: "load-error"; message: string }
  | { type: "result"; id: number; stdout: string; error: string | null; truncated: boolean };
