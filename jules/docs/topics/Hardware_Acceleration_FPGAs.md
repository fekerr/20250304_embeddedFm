# Hardware Acceleration using FPGAs: Split Learning

**Overview:**
This section discusses the implementation of **Split Learning on Field-Programmable Gate Arrays (FPGAs)**, referencing a Master's thesis from MIT. Split Learning is a technique where a neural network model is partitioned between a client device (in this case, an FPGA) and a server.

**Key Aspects:**

*   **Model Partitioning:** The core idea involves dividing a neural network, distributing parts of it to run on the FPGA (client) and other parts on a server. This is often done for reasons like resource constraints on the client, privacy, or efficiency.
*   **FPGA Implementation:** The focus was on implementing the client-side portion of the neural network on an FPGA, likely for edge devices or scenarios requiring low latency and power.
*   **High-Level Synthesis (HLS):** Tools like **hls4ml** and **Vivado** were used in this work. This indicates the application of HLS to translate higher-level descriptions of machine learning models (e.g., potentially from frameworks like Keras, given the mention of `keras-js` in related source contexts) into hardware implementations suitable for FPGAs.

**Context and Related Projects:**
*   **DARPA ReImagine Project:** The work was noted within the context of this DARPA project.
*   **Griffin FPIA at MIT Lincoln Laboratory:** Also associated with this research environment.
*   **hls4ml:** A key tool for converting machine learning models into HLS projects for FPGA deployment.
*   **Vivado:** Xilinx's (now AMD's) design suite for FPGAs, used for synthesis, implementation, and programming of the hardware.
