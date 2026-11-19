import type { ConceptNode } from "../types";
import { ScoreBar } from "./ScoreBar";

interface Props {
  chain: ConceptNode[];
  rootId: string;
  targetId: string;
}

/** The prerequisite chain from the root cause (left) up to the target concept (right). */
export function ChainView({ chain, rootId, targetId }: Props) {
  return (
    <ol className="chain" aria-label="Knowledge chain from root cause to target">
      {chain.map((node, index) => {
        const role = node.id === rootId ? "root" : node.id === targetId ? "target" : "step";
        const tag = role === "root" ? "Root cause" : role === "target" ? "Target" : "Prerequisite";
        return (
          <li key={node.id} className="chain-item">
            <div className={`chain-node chain-node--${role}`}>
              <span className="chain-tag">{tag}</span>
              <span className="chain-name">{node.name}</span>
              <ScoreBar score={node.score} />
            </div>
            {index < chain.length - 1 && (
              <svg className="chain-arrow" width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M4 12h15M13 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2" />
              </svg>
            )}
          </li>
        );
      })}
    </ol>
  );
}
