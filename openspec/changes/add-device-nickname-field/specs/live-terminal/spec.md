## MODIFIED Requirements

### Requirement: Event stream in main Xterm.js terminal

The frontend SHALL display WebSocket `device_start`, `device_done`, `device_error`, `task_progress`, and `task_complete` messages in the main Xterm.js terminal as a readable event log. When a device has a non-empty nickname, the nickname SHALL be shown instead of the IP address. When nickname is empty, IP SHALL be used as fallback.

#### Scenario: Device login succeeds
- **WHEN** `device_start` message is received
- **THEN** the main terminal appends a line like `[Core-SW-01] [OK] connected` with green color, using nickname when available
- **AND** if nickname is empty, the IP is shown: `[10.1.1.22] [OK] connected`

#### Scenario: Device execution complete
- **WHEN** `device_done` message is received
- **THEN** the main terminal appends `[Core-SW-01] [OK] done (show arp), 1.2s` with nickname when available

#### Scenario: Device execution fails
- **WHEN** `device_error` message is received
- **THEN** the main terminal appends `[Core-SW-01] [ERR] Auth failed` with nickname when available, styled in red

#### Scenario: Task progress update
- **WHEN** `task_progress` message is received
- **THEN** the main terminal appends a progress summary: `Progress: 3/10 done, 2 running, 1 failed`

#### Scenario: Task fully complete
- **WHEN** `task_complete` message is received
- **THEN** the main terminal appends `==== Task complete: 9 success, 1 failed ====`

### Requirement: Result summary cards

After execution completes for a device, the frontend SHALL display a result card showing device nickname (or IP as fallback), status (success/failure), and duration. The nickname SHALL be the primary label with IP shown as a secondary subtitle when nickname is non-empty.

#### Scenario: Successful device card with nickname
- **WHEN** device_done with status="success" is received for a device that has a nickname
- **THEN** a green result card appears with the nickname as the primary label, the IP as a smaller subtitle, a checkmark, and duration

#### Scenario: Successful device card without nickname
- **WHEN** device_done with status="success" is received for a device with an empty nickname
- **THEN** a green result card appears with the IP as the primary label (no subtitle), a checkmark, and duration

#### Scenario: Failed device card
- **WHEN** device_error is received
- **THEN** a red result card appears with nickname (or IP fallback), cross mark, and error message

### Requirement: Modal popup with Xterm.js pure output

Clicking a result card SHALL open a modal dialog containing an Xterm.js terminal showing the pure command output for that device. The modal title SHALL display the device nickname (or IP as fallback) and the IP as a subtitle when nickname is non-empty.

#### Scenario: Open modal for single-command result
- **WHEN** user clicks a result card for a device that ran one command
- **THEN** a modal opens with an Xterm.js terminal displaying the raw command output
- **AND** the modal title shows the device nickname (primary) and IP (subtitle)
- **AND** no event log formatting is mixed in

#### Scenario: Open modal for multi-command result
- **WHEN** user clicks a result card for a device that ran multiple commands
- **THEN** the modal shows Tab buttons for each command (`show arp`, `show version`, ...)
- **AND** clicking a Tab switches the Xterm.js terminal to that command's output

#### Scenario: Close modal
- **WHEN** user clicks the close button or backdrop
- **THEN** the modal is dismissed
