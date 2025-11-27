# ABAP Function Module for Syntax Checking

This directory contains the ABAP artifacts that need to be deployed to the SAP ERP system.

## Components

### 1. Function Group: ZSYNTAX_CHECK

The function group that contains the syntax checking function module.

**File**: `function_group/ZSYNTAX_CHECK.fugr.xml`

### 2. Function Module: Z_CHECK_ABAP_SYNTAX

The main function module that performs ABAP syntax checking.

**File**: `function_module/Z_CHECK_ABAP_SYNTAX.abap`

#### Interface

**Import Parameters:**
- `IV_CODE` (STRING) - The ABAP REPORT program source code to check

**Export Parameters:**
- `EV_SUCCESS` (CHAR1) - 'X' if check executed successfully, '' otherwise
- `EV_MESSAGE` (STRING) - Status message or error description

**Table Parameters:**
- `ET_ERRORS` (ZSYNTAX_ERROR) - Table of syntax errors found

#### Implementation Details

The function module:
1. Validates that input code is not empty
2. Generates a unique temporary program name using timestamp
3. Creates a temporary program using `INSERT REPORT`
4. Performs syntax check using `SYNTAX-CHECK FOR`
5. Collects additional error details using `SCAN ABAP-SOURCE`
6. Sorts errors by line number
7. Deletes the temporary program
8. Returns structured error information

Exception handling ensures the temporary program is always deleted, even if errors occur.

### 3. Type Definition: ZSYNTAX_ERROR

Structure definition for syntax error information.

**File**: `types/ZSYNTAX_ERROR.abap`

**Fields:**
- `LINE` (I) - Error line number
- `TYPE` (CHAR1) - Message type ('E' = Error, 'W' = Warning)
- `MESSAGE` (STRING) - Error description

## Deployment Instructions

### Option 1: Manual Creation in SAP GUI

1. **Create the Type Definition:**
   - Transaction: SE11
   - Create structure `ZSYNTAX_ERROR` with fields:
     - LINE (Type: I)
     - TYPE (Type: CHAR1)
     - MESSAGE (Type: STRING)

2. **Create the Function Group:**
   - Transaction: SE80
   - Create function group `ZSYNTAX_CHECK`

3. **Create the Function Module:**
   - Transaction: SE37
   - Create function module `Z_CHECK_ABAP_SYNTAX`
   - Define interface parameters as specified above
   - Copy implementation code from `function_module/Z_CHECK_ABAP_SYNTAX.abap`
   - Activate the function module

### Option 2: Using abapGit

If your SAP system has abapGit installed:

1. Create a new abapGit repository
2. Link it to this directory
3. Pull the objects
4. Activate all objects

### Option 3: Transport

1. Create the objects in a development system
2. Add to a transport request
3. Release and import to target systems

## Testing the Function Module

You can test the function module directly in SE37:

**Test Case 1: Valid ABAP Code**
```abap
REPORT ztest.
WRITE: 'Hello World'.
```
Expected: EV_SUCCESS = 'X', ET_ERRORS is empty

**Test Case 2: Invalid ABAP Code**
```abap
REPORT ztest.
WRITE: lv_undefined_variable.
```
Expected: EV_SUCCESS = 'X', ET_ERRORS contains error about undefined variable

**Test Case 3: Empty Code**
```abap
(empty string)
```
Expected: EV_SUCCESS = '', EV_MESSAGE = 'Input code is empty'

## Authorization Requirements

The function module requires the following authorizations:
- S_PROGRAM: Authority to create and delete programs
- S_DEVELOP: Development authorization

Ensure the RFC user has these authorizations in the target system.

## Notes

- The function module creates temporary programs with names starting with `ZTEMP_`
- Temporary programs are automatically deleted after syntax checking
- The implementation uses exception handling to ensure cleanup even on errors
- Error messages are sorted by line number for easier consumption
- The function module uses both `SYNTAX-CHECK FOR` and `SCAN ABAP-SOURCE` to capture comprehensive error information
