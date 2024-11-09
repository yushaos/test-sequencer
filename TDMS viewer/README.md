# TDMS Viewer

A PyQt6-based viewer for TDMS (Technical Data Management Streaming) files with real-time plotting and data inspection capabilities.

## Features

- Interactive plot visualization
- Data table view
- Dual cursors with measurements
- Signal snapping
- Drag and drop file loading
- Multi-signal selection
- Configurable time axis mapping
- Zoom and pan controls
- Manual axis range control

## Installation

1. Clone the repository
2. Install dependencies: 

bash
pip install PyQt6 nptdms pyqtgraph numpy

## Usage

Run the viewer:


### Basic Controls

- **File Loading**: 
  - Drag and drop TDMS files onto the application
  - Use the browse button (📁)
  - Enter file path manually

- **Plot Controls**:
  - Zoom In/Out buttons
  - Reset view button
  - Manual axis range input
  - Pan mode (default)

- **Cursor Controls**:
  - Toggle cursors with "Cursor" button
  - Center cursors with "⌖ Center Cursors"
  - Snap cursors to signals using dropdown
  - Drag cursors for measurements

## Configuration

### Time Axis Mapping (tdms_viewer_config.json)

The viewer uses a configuration file to map Y-axis signals to their corresponding X-axis (time) signals. Create a `tdms_viewer_config.json` file in the same directory as `tdms_viewer.py`:


#### Configuration Format:
- Each entry in `signal_pairs` maps a Y-signal to its X-signal
- `"y"`: Name of the value signal
- `"x"`: Name of the corresponding time signal

#### Example:
If your TDMS file has signals:
- `Voltage` with time data in `Voltage_Time`
- `Current` with time data in `Current_Time`

Your config would look like:
json
{
"signal_pairs": [
{
"y": "Voltage",
"x": "Voltage_Time"
},
{
"y": "Current",
"x": "Current_Time"
}
]
}

Note: If no mapping is found for a signal, the viewer will automatically look for a time channel with the naming pattern `{signal_name}_Time`.

## Tips

1. Use Ctrl+Click for multiple signal selection
2. Use Shift+Click for range selection
3. Switch between Graph and Table views using tabs
4. Drag cursors for precise measurements
5. Use the snap feature to align cursors with data points

## Requirements

- Python 3.6+
- PyQt6
- nptdms
- pyqtgraph
- numpy
