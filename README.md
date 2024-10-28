# Test Sequencer

A PyQt5-based GUI application for running automated test sequences with configurable steps and real-time status monitoring.

## Overview

The Test Sequencer is a flexible framework for executing and managing test sequences. It provides:

- A graphical interface for loading and running test sequences
- Real-time progress monitoring and status updates
- Error handling and reporting
- Support for modular test steps
- Sequence history tracking
- Result file management

## Key Features

- **Modular Step Execution**: Each test step is loaded dynamically from separate Python modules
- **Section-Based Organization**: Steps are organized into Setup, Test, and Cleanup sections
- **Real-Time Progress**: Visual feedback on sequence execution progress
- **Error Handling**: Comprehensive error catching and reporting
- **Previous Sequences**: Track and reload previously run sequences
- **Result Files**: Manage and access test result files
- **Configurable**: JSON-based sequence configuration

## Architecture

- **Main GUI** (`main.py`): PyQt5-based user interface
- **Scheduler** (`scheduler.py`): Core sequence execution engine
- **NI Timer** (`ni_timer.py`): Timing utilities
- **Previous Sequences** (`previous_sequences.py`): Sequence history management
- **Result Files Handler** (`result_files_handler.py`): Test result file management
- **Status Components**: Error box, status box, and status bar for progress monitoring

## Sequence Configuration

Sequences are defined in JSON files with the following structure:
