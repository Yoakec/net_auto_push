## ADDED Requirements

### Requirement: Command execution API

The system SHALL expose `POST /api/execute` that accepts selected device IPs, commands, and a concurrency limit, and returns a task_id for tracking.

#### Scenario: Execute commands on multiple devices
- **WHEN** frontend sends `POST /api/execute` with `{device_ips: [...], commands: [...], max_concurrent: 5}`
- **THEN** the system creates a task with a unique `task_id`
- **AND** returns `{task_id: "uuid"}` immediately (non-blocking)
- **AND** begins executing commands on selected devices with the specified concurrency limit

#### Scenario: Missing required fields
- **WHEN** frontend sends a request without `device_ips` or `commands`
- **THEN** the system returns HTTP 422 with validation error details

### Requirement: SSH connection with netmiko

For each device, the system SHALL establish an SSH connection using netmiko with the device's stored credentials and protocol/port.

#### Scenario: Successful connection
- **WHEN** netmiko connects to a device with valid credentials
- **THEN** the system sends `device_start` message via WebSocket
- **AND** the system enters the SSH session and proceeds to command execution

#### Scenario: Authentication failure
- **WHEN** netmiko fails to authenticate
- **THEN** the system sends `device_error` message with "Auth failed" error
- **AND** the device is marked as failed

#### Scenario: Connection timeout
- **WHEN** netmiko fails to establish TCP connection within 15 seconds
- **THEN** the system sends `device_error` message with "Connection timeout" error
- **AND** the device is marked as failed

### Requirement: Pagination suppression

After establishing an SSH session, the system SHALL attempt to disable CLI pagination by sending `screen-length 0 disable` before executing user commands.

#### Scenario: Successful pagination disable
- **WHEN** `screen-length 0 disable` is sent and acknowledged by the device
- **THEN** subsequent command output is not interrupted by pagination prompts

#### Scenario: Pagination disable command unrecognized
- **WHEN** the device does not support `screen-length 0 disable`
- **THEN** the system silently ignores the error and continues with command execution
- **AND** relies on netmiko's default output collection behavior

### Requirement: Multi-command sequential execution per device

For each device, the system SHALL execute commands in the order they appear in the input, one at a time.

#### Scenario: Two commands executed in order
- **WHEN** commands are `["show arp", "show version"]`
- **THEN** `show arp` is executed first, its full output collected
- **THEN** `show version` is executed second, its full output collected
- **AND** each command's output is streamed via WebSocket with the `command` field identifying it

#### Scenario: Command output containing ANSI escape sequences
- **WHEN** device output contains ANSI escape codes
- **THEN** the system strips or passes through the escape sequences for Xterm.js to render

### Requirement: Fail-fast on command error

If a command returns an error (output containing `Error:` or `Unrecognized command`, or raises an exception), the system SHALL immediately stop executing remaining commands for that device.

#### Scenario: First command fails
- **WHEN** the first command `show arrp` (typo) returns `Unrecognized command`
- **THEN** the system sends `device_error` with the error output
- **AND** does NOT execute the remaining commands for that device

#### Scenario: Middle command fails
- **WHEN** the second of three commands fails
- **THEN** the third command is NOT executed for that device
- **AND** the device result includes output from commands 1 and the error from command 2

### Requirement: Concurrency control

The system SHALL limit the number of concurrently executing device sessions using `asyncio.Semaphore`, with the limit set by the `max_concurrent` parameter.

#### Scenario: Concurrency limit of 3 with 10 devices
- **WHEN** 10 devices are selected with max_concurrent=3
- **THEN** at most 3 devices have active SSH sessions at any time
- **AND** as each device completes, the next waiting device starts

#### Scenario: Single device execution
- **WHEN** only 1 device is selected
- **THEN** it executes immediately regardless of concurrency setting

### Requirement: Task-level progress reporting

The system SHALL broadcast task-level progress via WebSocket as devices start, complete, or fail.

#### Scenario: Progress update after device completes
- **WHEN** a device finishes execution
- **THEN** a `task_progress` message is sent with updated `{total, completed, running, failed}` counts

#### Scenario: All devices finished
- **WHEN** all selected devices have completed or failed
- **THEN** a `task_complete` message is sent with final `{total, success, failed}` counts
