# Inference-coordination-solution-for-ResNet

A research-oriented implementation exploring **dynamic inference strategies** for Residual Networks (ResNet). Instead of executing every residual block for every input, this project investigates how an auxiliary decision module can coordinate the inference process by selectively activating network blocks according to the input complexity.

> **Note**
>
> This project is **inspired by the research direction introduced in BlockDrop (CVPR 2018)** and other dynamic neural network approaches. It is **not** an official implementation or reproduction of BlockDrop. The architecture, implementation details, training pipeline, and experimental settings have been redesigned for learning and experimentation purposes.

---

## Motivation

Conventional ResNet models execute every residual block regardless of the difficulty of the input sample. However, many images can be classified correctly without requiring the full network depth.

This project explores an adaptive inference mechanism that aims to:

* Reduce unnecessary computation during inference.
* Preserve classification accuracy whenever possible.
* Learn input-dependent execution paths.
* Study the trade-off between computational cost and predictive performance.

The overall objective is to make inference more efficient while maintaining the flexibility of standard ResNet architectures.

---

## Project Overview

The framework consists of two primary components:

### 1. Backbone Network

A standard ResNet model is used as the feature extraction backbone.

### 2. Inference Coordination Module

An auxiliary controller predicts which residual blocks should be executed for each input sample.

Unlike static pruning methods, the execution path is determined dynamically during inference, allowing different images to activate different subsets of the network.

---

## Features

* Dynamic residual block execution
* Adaptive inference for ResNet architectures
* Configurable execution policy
* Training and evaluation pipelines
* Modular PyTorch implementation
* Easy experimentation with different coordination strategies

---

## Repository Structure

```
.
├── models/          # ResNet and coordination modules
├── datasets/        # Dataset loading
├── train.py         # Training script
├── test.py          # Evaluation
├── utils/           # Utilities
├── configs/         # Hyperparameters
└── README.md
```

---

## Installation

```bash
git clone <repository-url>
cd Inference-Coordination-for-ResNet

pip install -r requirements.txt
```

---

## Training

Example:

```bash
python train.py
```

Model configurations and hyperparameters can be adjusted inside the configuration files.

---

## Evaluation

```bash
python test.py
```

Typical evaluation metrics include:

* Top-1 Accuracy
* FLOPs
* Inference latency
* Average executed residual blocks

---

## Research Goals

This project focuses on understanding how dynamic execution policies affect:

* Computational efficiency
* Model accuracy
* Generalization ability
* Inference speed
* Resource utilization

Rather than proposing a production-ready system, the implementation serves as a research platform for experimenting with adaptive computation in convolutional neural networks.

---

## Future Improvements

* Support for ResNet-50/101/152
* Reinforcement learning-based policy optimization
* Multi-objective loss balancing accuracy and efficiency
* Mixed precision inference
* ONNX / TensorRT deployment
* Visualization of execution paths
* Benchmarking on larger datasets
