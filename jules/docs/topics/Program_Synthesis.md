# Program Synthesis

**Summary:**
Program synthesis focuses on approaches for automatically generating programs from specifications or examples. One notable technique is **Program Synthesis via Relational Decomposition**.

**Relational Decomposition Approach:**
This method decomposes complex synthesis tasks into simpler relational subtasks. Instead of treating input-output examples as monolithic structures (like entire lists or images), they are represented as sets of facts. The goal is then to learn rules that govern the relationships between these input facts and output facts.

**Evaluation and Benchmarks:**
This decomposed representation has been shown to outperform standard (undecomposed) representations when evaluated on various domains, including:
*   **Abstraction and Reasoning Corpus (ARC)**
*   **Strings**
*   **List functions**

These datasets serve as benchmarks for assessing the effectiveness of different program synthesis techniques. The relational decomposition approach aims to make the learning problem more tractable by breaking it into smaller, more manageable pieces.
