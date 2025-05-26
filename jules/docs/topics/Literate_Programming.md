# Literate Programming (LP) and Interoperable Literate Programming (ILP)

**Summary:**
Literate Programming (LP) principles and the proposed Interoperable Literate Programming (ILP) standard aim to enhance LLM-based code generation, particularly in large-scale projects. ILP emphasizes a structured approach to combining code and descriptive content in a narrative style within "documents," as opposed to simple files with comments.

**Key Concepts of ILP:**
*   **Structured Documents:** ILP promotes organizing code and narrative in a way that is understandable and maintainable for both humans and LLMs.
*   **API Logic as a DAG:** The use of **Scheme** is highlighted for its simplicity and suitability in structuring API logic as a Directed Acyclic Graph (DAG) within ILP documents. Scheme's foundation in lambda calculus aligns well with this DAG representation.
*   **"Zero-step" and "Successor-step" Methodology:** This clear structure is intended to guide LLMs effectively during code generation and understanding.
*   **Machine-Readable Metadata:** Annotations like `define-with-docs` are used to embed metadata (e.g., pattern, complexity, examples) directly within the documentation, providing guidance for LLMs.
*   **Tooling:**
    *   **Mogan:** A UTF-8 compatible LP editor that facilitates editing and exporting all project files from a single ILP document.
    *   **Goldfish Scheme:** A Scheme interpreter introduced to support ILP development.

**Benefits and Evaluation:**
Experiments conducted on the **RepoBench** benchmark have shown measurable improvements in both structural consistency and implementation quality when ILP principles guide LLM-based code generation. The core idea is that by making the code's narrative, structure, and intent clearer, LLMs can produce better, more maintainable code.
