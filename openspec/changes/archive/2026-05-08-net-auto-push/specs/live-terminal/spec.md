## ADDED Requirements

### Requirement: WebSocket connection for real-time output

The system SHALL provide a WebSocket endpoint at `/ws/task/{task_id}` that pushes execution events and device output in real time.

#### Scenario: Client connects to task WebSocket
- **WHEN** frontend opens WebSocket to `/ws/task/{task_id}`
- **THEN** the connection is accepted and remains open for the task duration
- **AND** all messages for that task are pushed to the connected client

#### Scenario: Client connects to non-existent task
- **WHEN** frontend opens WebSocket to a task_id that does not exist
- **THEN** the connection is closed with an error code

### Requirement: Event stream in main Xterm.js terminal

The frontend SHALL display WebSocket `device_start`, `device_done`, `device_error`, `task_progress`, and `task_complete` messages in the main Xterm.js terminal as a readable event log.

#### Scenario: Device login succeeds
- **WHEN** `device_start` message is received
- **THEN** the main terminal appends a line like `[10.1.1.22] [OK] connected` with green color

#### Scenario: Device execution complete
- **WHEN** `device_done` message is received
- **THEN** the main terminal appends `[10.1.1.22] [OK] done (show arp), 1.2s` with status and timing

#### Scenario: Device execution fails
- **WHEN** `device_error` message is received
- **THEN** the main terminal appends `[10.1.1.22] [ERR] Auth failed` styled in red

#### Scenario: Task progress update
- **WHEN** `task_progress` message is received
- **THEN** the main terminal appends a progress summary: `Progress: 3/10 done, 2 running, 1 failed`

#### Scenario: Task fully complete
- **WHEN** `task_complete` message is received
- **THEN** the main terminal appends `==== Task complete: 9 success, 1 failed ====`

### Requirement: Device output NOT shown in main terminal

`device_output` messages SHALL NOT be displayed in the main terminal. They SHALL be routed to result storage for the modal detail view.

#### Scenario: device_output message received
- **WHEN** a `device_output` message arrives
- **THEN** the output data is stored in frontend state keyed by `device_ip` and `command`
- **AND** nothing is written to the main terminal

### Requirement: Result summary cards

After execution completes for a device, the frontend SHALL display a result card showing device IP, status (success/failure), and duration.

#### Scenario: Successful device card
- **WHEN** device_done with status="success" is received
- **THEN** a green result card appears with device IP, checkmark, and duration

#### Scenario: Failed device card
- **WHEN** device_error is received
- **THEN** a red result card appears with device IP, cross mark, and error message

### Requirement: Modal popup with Xterm.js pure output

Clicking a result card SHALL open a modal dialog containing an Xterm.js terminal showing the pure command output for that device.

#### Scenario: Open modal for single-command result
- **WHEN** user clicks a result card for a device that ran one command
- **THEN** a modal opens with an Xterm.js terminal displaying the raw command output
- **AND** no event log formatting is mixed in

#### Scenario: Open modal for multi-command result
- **WHEN** user clicks a result card for a device that ran multiple commands
- **THEN** the modal shows Tab buttons for each command (`show arp`, `show version`, ...)
- **AND** clicking a Tab switches the Xterm.js terminal to that command's output

#### Scenario: Close modal
- **WHEN** user clicks the close button or backdrop
- **THEN** the modal is dismissed

### Requirement: Copy and export from modal

The modal SHALL provide buttons to copy the full output or export as a TXT file.

#### Scenario: Copy all output
- **WHEN** user clicks "Copy All" in the modal
- **THEN** all command outputs (concatenated with `========== <command> ==========` separators) are copied to clipboard

#### Scenario: Export as TXT
- **WHEN** user clicks "Export TXT" in the modal
- **THEN** a `.txt` file is downloaded containing all command outputs with separators

### Requirement: Xterm.js rendering of ANSI

The Xterm.js terminals (main and modal) SHALL support ANSI escape sequence rendering for proper display of colored device output and cursor control sequences.

#### Scenario: Output contains ANSI color codes
- **WHEN** device output includes ANSI color escape sequences
- **THEN** Xterm.js renders the text in the appropriate colors
