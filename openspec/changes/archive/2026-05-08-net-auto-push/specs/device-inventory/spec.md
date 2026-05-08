## ADDED Requirements

### Requirement: CSV-based device data loading

The system SHALL load device inventory from CSV files placed in the `/data/` directory at startup. CSV columns are: `ip`, `Type`, `username`, `password`, `Protocol`, `port`, `Area`, `encode`.

#### Scenario: Startup loading
- **WHEN** the backend starts
- **THEN** it reads all CSV files from `/data/` and loads devices into memory
- **AND** password fields are never sent to the frontend

#### Scenario: CSV with missing optional columns
- **WHEN** a CSV is loaded with missing columns (e.g., missing `Area` or `encode`)
- **THEN** the system treats those fields as empty strings and continues loading

### Requirement: Device inventory API

The system SHALL expose `GET /api/inventory` returning all loaded devices.

#### Scenario: Get all devices
- **WHEN** frontend calls `GET /api/inventory`
- **THEN** the response is a JSON array of devices, each with `{ip, type, username, protocol, port, area, encode}` fields
- **AND** the `password` field MUST NOT be included

### Requirement: CSV upload and refresh

The system SHALL accept CSV file uploads via `POST /api/upload` to replace or augment the current device inventory.

#### Scenario: Upload new CSV
- **WHEN** a user uploads a CSV file via POST /api/upload
- **THEN** the CSV is parsed and devices are added/merged into the in-memory inventory
- **AND** the uploaded file is saved to `/data/` directory
- **AND** the updated device list is returned

#### Scenario: Upload invalid CSV
- **WHEN** a user uploads a file that is not valid CSV or missing the `ip` column
- **THEN** the system returns HTTP 422 with an error message

### Requirement: Device filtering on frontend

The frontend SHALL allow filtering the device table by `Area` and `Type` columns, and searching by keyword.

#### Scenario: Filter by Area
- **WHEN** user selects an Area value from the filter dropdown
- **THEN** only devices matching that Area are displayed in the table

#### Scenario: Filter by Type
- **WHEN** user selects a Type value from the filter dropdown
- **THEN** only devices matching that Type are displayed in the table

#### Scenario: Keyword search
- **WHEN** user types a keyword in the search box
- **THEN** devices whose `ip` contains the keyword are displayed

#### Scenario: Combined filters
- **WHEN** user applies both Area filter and keyword search
- **THEN** devices must match ALL active filters

### Requirement: Device selection

The frontend SHALL provide checkboxes for selecting which devices to execute commands on, including a "select all" shortcut.

#### Scenario: Select individual devices
- **WHEN** user checks checkboxes next to specific devices
- **THEN** those devices are added to the selection set

#### Scenario: Select all filtered
- **WHEN** user clicks "select all" while a filter is active
- **THEN** only the currently visible (filtered) devices are selected
