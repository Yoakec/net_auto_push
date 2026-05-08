## ADDED Requirements

### Requirement: Task completion triggers archiving

When all devices in a task finish execution, the system SHALL automatically generate an archive in `/archives/<timestamp>_Task/`.

#### Scenario: Single-device task archive
- **WHEN** a task with 1 device completes
- **THEN** a directory is created: `/archives/2026-05-07_143000_Task/`
- **AND** it contains `10.1.1.22_Huawei.md` and `task_summary.json`

#### Scenario: Multi-device task archive
- **WHEN** a task with 3 devices completes (2 success, 1 failed)
- **THEN** the archive directory contains 3 device `.md` files and `task_summary.json`
- **AND** the failed device's `.md` file includes the error section

### Requirement: Device Markdown file format

Each device `.md` file SHALL be named `<ip>_<type>.md` and contain the device's command outputs organized by command name.

#### Scenario: Single-command device markdown
- **WHEN** a device executed only `show arp`
- **THEN** its `.md` file contains:
  - H1: `# <ip> (<type>)`
  - H2: `## show arp`
  - Code block with raw output
  - Execution metadata (start time, end time, duration)

#### Scenario: Multi-command device markdown
- **WHEN** a device executed `show arp` and `show version`
- **THEN** its `.md` file contains two H2 sections, one per command
- **AND** outputs appear in the order commands were executed

#### Scenario: Failed device markdown
- **WHEN** a device failed during execution
- **THEN** its `.md` file includes:
  - Any successfully executed command outputs (before the failure)
  - An H2 section `## Error` with the error message
  - Execution metadata with status "failed"

### Requirement: task_summary.json format

`task_summary.json` SHALL contain task-level metadata.

#### Scenario: Task summary file
- **WHEN** a task completes
- **THEN** `task_summary.json` contains:
  - `task_id`: the task UUID
  - `started_at`, `finished_at`: ISO8601 timestamps
  - `commands`: array of commands executed
  - `devices`: array of `{ip, type, area, status, duration_ms}` per device
  - `summary`: `{total, success, failed}`

### Requirement: Archive directory naming

Archive directories SHALL be named with a timestamp prefix for natural chronological sorting.

#### Scenario: Directory naming convention
- **WHEN** a task is created at 2026-05-07 14:30:00
- **THEN** the archive directory is named `2026-05-07_143000_Task`
- **AND** multiple tasks at the same second append a counter suffix: `2026-05-07_143000_Task_2`

### Requirement: Archive browsing API

The system SHALL expose `GET /api/archives` listing all past task archives.

#### Scenario: List archives
- **WHEN** frontend calls `GET /api/archives`
- **THEN** the response is a JSON array of archive summaries, each with `{task_id, started_at, finished_at, total, success, failed, device_count}`
