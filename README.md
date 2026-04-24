# PicoROS

**PicoROS** is a lightweight ROS-like framework implemented in MicroPython for resource-constrained embedded systems. It provides a minimal publish–subscribe architecture, enabling modular communication between components and seamless interaction with web-based interfaces.

---

## 🚀 Overview

PicoROS brings core robotics abstractions—such as nodes, topics, and message passing—to microcontroller environments. The system is designed to support rapid prototyping and experimentation in embedded robotics, while maintaining low computational overhead.

The architecture consists of three main components:

- **Embedded Nodes** (MicroPython, TCP communication)
- **Communication Broker** (TCP ↔ WebSocket bridge)
- **Web Client** (browser-based interface)

