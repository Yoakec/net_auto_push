## MODIFIED Requirements

### Requirement: CSV-based device data loading

The system SHALL load device inventory from CSV files placed in the `/data/` directory at startup. CSV columns are: `nickname`, `ip`, `Type`, `username`, `password`, `Protocol`, `port`, `Area`, `encode`.

#### Scenario: Startup loading
- **WHEN** the backend starts
- **THEN** it reads all CSV files from `/data/` and loads devices into memory
- **AND** password fields are never sent to the frontend

#### Scenario: CSV with missing optional columns
- **WHEN** a CSV is loaded with missing columns (e.g., missing `Area`, `encode`, or `nickname`)
- **THEN** the system treats those fields as empty strings and continues loading

#### Scenario: Nickname loaded from CSV
- **WHEN** a CSV row contains a non-empty `nickname` value
- **THEN** the device is loaded with that nickname stored

### Requirement: Device inventory API

The system SHALL expose `GET /api/inventory` returning all loaded devices.

#### Scenario: Get all devices
- **WHEN** frontend calls `GET /api/inventory`
- **THEN** the response is a JSON array of devices, each with `{nickname, ip, type, username, protocol, port, area, encode}` fields
- **AND** the `password` field MUST NOT be included
- **AND** the `nickname` field MAY be an empty string

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
- **THEN** devices whose `ip` OR `nickname` contains the keyword are displayed

#### Scenario: Combined filters
- **WHEN** user applies both Area filter and keyword search
- **THEN** devices must match ALL active filters
