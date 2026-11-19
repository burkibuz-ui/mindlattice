import { RUN_TIMEOUT_MS, type RunOutcome } from "../runner/usePythonRunner";

interface Props {
  outcome: RunOutcome;
  expected: string;
}

const normalize = (text: string) => text.split("\n").map((line) => line.trimEnd()).join("\n").trim();

/** Tasks like "evens([1, 2, 3, 4]) -> [2, 4]" describe behaviour, they are not printed output. */
const isPrintedOutput = (expected: string) => expected.trim() !== "" && !expected.includes("->");

export function RunOutput({ outcome, expected }: Props) {
  if (outcome.timedOut) {
    return (
      <div className="run-output run-output--bad" role="status">
        <strong>Stopped after {RUN_TIMEOUT_MS / 1000} seconds.</strong> The code probably never finishes,
        for example a while loop whose condition never becomes false.
      </div>
    );
  }

  const matches = isPrintedOutput(expected) && !outcome.error && normalize(outcome.stdout) === normalize(expected);
  const mismatch = isPrintedOutput(expected) && !outcome.error && !matches;

  return (
    <div className="run-output" role="status">
      <div className="run-output-header">
        <span>Output</span>
        {matches && <span className="run-badge run-badge--good">Matches expected output</span>}
        {mismatch && <span className="run-badge run-badge--bad">Expected {expected.replace(/\n/g, ", ")}</span>}
      </div>
      <pre className="run-stdout">{outcome.stdout || <span className="run-empty">(no output)</span>}</pre>
      {outcome.truncated && <p className="muted small">Output was cut off: too many lines.</p>}
      {outcome.error && <pre className="run-error">{outcome.error}</pre>}
    </div>
  );
}
