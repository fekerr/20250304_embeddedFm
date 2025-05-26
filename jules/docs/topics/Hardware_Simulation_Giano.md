# Hardware Simulation: Giano System Simulator

**Overview:**
**Giano**, developed by Microsoft, is a **Real-Time, full-system, hardware-software co-simulator**. It is designed to meet specific requirements for research in embedded systems and reconfigurable computing.

**Key Capabilities and Design Goals:**

*   **Hardware Core Simulation:** Capable of simulating hardware cores intended for Field-Programmable Gate Arrays (FPGAs).
*   **Large Code Base Execution:** Can execute substantial software code bases.
*   **Complete System Simulation:** Simulates entire systems, including various Input/Output (I/O) devices.
*   **Real-Time Communication:** Able to communicate in real-time with the external world, distinguishing it from many other simulators.
*   **Debugging and Tracing:** Supports debugging efforts and tracing, including analysis at the basic block level, which is useful for profiling performance bottlenecks.
*   **Hardware Simulator Interface:** Can interface with hardware simulators like **ModelSim** using the Program Language Interface (PLI).
*   **Supported Architectures:** Includes support for MIPS, ARM, PowerPC, and BlackFin architectures.

**Architectural Features:**
*   **Bus System:** Incorporates a bus system for managing communication between different simulated devices.
*   **Efficiency:** Features like efficient handling of idle conditions and load profile matching are part of its design.

**Source Code Availability:**
The availability of Giano's source code is considered essential for enabling future user modifications and adaptations.
