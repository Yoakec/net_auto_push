## ADDED Requirements

### Requirement: Snippet library CSV loading

The system SHALL load command snippets from `/data/commands.csv` at startup. The CSV format is flexible; at minimum it has a `command` column and an optional `category` column.

#### Scenario: Load snippet CSV with categories
- **WHEN** commands.csv has columns `command` and `category`
- **THEN** snippets are grouped by category in the frontend dropdown
- **AND** snippets without a category are placed under "Uncategorized"

#### Scenario: Load snippet CSV with only command column
- **WHEN** commands.csv has only a `command` column
- **THEN** all snippets are listed flat without category grouping

#### Scenario: No commands.csv present
- **WHEN** `/data/commands.csv` does not exist
- **THEN** the snippet library is empty
- **AND** the command input box remains fully functional for manual entry

### Requirement: Snippet library API

The system SHALL expose `GET /api/snippets` returning all loaded command snippets.

#### Scenario: Get all snippets
- **WHEN** frontend calls `GET /api/snippets`
- **THEN** the response is a JSON array of snippets, each with `{command, category}` fields

### Requirement: Snippet library dropdown in frontend

The frontend SHALL display command snippets in a dropdown near the command input box, grouped by category when applicable.

#### Scenario: Select a snippet
- **WHEN** user clicks a snippet from the dropdown (e.g., `show arp`)
- **THEN** the snippet text is inserted into the command input box
- **AND** user can edit or append to the text before executing

#### Scenario: Select a snippet when input is not empty
- **WHEN** user selects a snippet while the command input box already has text
- **THEN** the existing text is replaced with the selected snippet

### Requirement: Multi-line command input

The command input box SHALL support multiple lines, where each non-empty line is treated as a separate command to execute sequentially on each device.

#### Scenario: Enter multiple commands
- **WHEN** user types `show arp` on line 1 and `show version` on line 2
- **THEN** two commands are submitted when clicking Execute
- **AND** they are executed in order on each selected device

#### Scenario: Blank lines in input
- **WHEN** the command input contains blank lines between commands
- **THEN** blank lines are ignored during parsing

### Requirement: Snippet upload and refresh

The system SHALL accept snippet CSV upload via `POST /api/upload/snippets`.

#### Scenario: Upload new snippet CSV
- **WHEN** user uploads a snippet CSV file
- **THEN** the file is saved to `/data/commands.csv`
- **AND** the snippet library is updated
- **AND** the updated snippet list is returned
