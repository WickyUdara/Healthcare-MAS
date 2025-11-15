import React, { useEffect, useRef } from "react";
import mermaid from "mermaid";
import "./SequenceDiagram.css";

export default function SequenceDiagram({ mermaidText, title }) {
  const diagramRef = useRef(null);

  useEffect(() => {
    if (mermaidText && diagramRef.current) {
      try {
        mermaid.contentLoaded();
        const diagram = mermaid.render("mermaid-diagram", mermaidText);
        diagram
          .then((result) => {
            if (diagramRef.current) {
              diagramRef.current.innerHTML = result.svg;
            }
          })
          .catch((err) => {
            console.error("Mermaid rendering error:", err);
            if (diagramRef.current) {
              diagramRef.current.innerHTML = `<pre>${mermaidText}</pre>`;
            }
          });
      } catch (err) {
        console.error("Mermaid error:", err);
        if (diagramRef.current) {
          diagramRef.current.innerHTML = `<pre>${mermaidText}</pre>`;
        }
      }
    }
  }, [mermaidText]);

  return (
    <div className="sequence-diagram-container">
      {title && <h3 className="diagram-title">{title}</h3>}
      <div className="diagram-content" ref={diagramRef}></div>
    </div>
  );
}
