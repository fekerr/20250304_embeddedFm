# Smart Contract Generation: ConMover

**Overview:**
**ConMover** is a framework designed for generating **Move smart contracts**, with a primary focus on the **Sui blockchain**. Move is noted as a low-resource domain for code generation, making this task challenging.

**Agentic Approach:**
ConMover employs an agentic design, which involves several specialized components working together:

*   **Concept Generation Stage:**
    *   A **Planner Agent** utilizes Retrieval Augmented Generation (RAG) by drawing information from Sui Move documentation and Docs2KG (Documentation to Knowledge Graph).
*   **Code Generation Stage:**
    *   A stock Large Language Model (LLM) like **Gemini 1.5** is used for the initial code generation.
*   **Code Correction Stage:**
    *   A **Debugging Agent** uses a feedback loop. It analyzes execution traces from failed code attempts to generate refined prompts or guidance for the LLM to correct the code.

**Key Features and Effectiveness:**

*   **Feedback Loop:** The iterative process of generating code, testing, analyzing failures (using execution traces), and refining the generation prompts is central to ConMover's approach.
*   **Low-Resource Domain:** The framework was found to be effective even with a limited dataset of Move smart contract categories, demonstrating its utility in specialized or emerging programming languages.
