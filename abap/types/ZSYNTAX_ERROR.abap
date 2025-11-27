*&---------------------------------------------------------------------*
*& Table Type: ZSYNTAX_ERROR
*& Description: Structure for syntax error information
*&---------------------------------------------------------------------*

TYPES: BEGIN OF zsyntax_error,
         line    TYPE i,          " Error line number
         type    TYPE char1,      " Message type: 'E' = Error, 'W' = Warning
         message TYPE string,     " Error description
       END OF zsyntax_error.

TYPES: zsyntax_error_tab TYPE STANDARD TABLE OF zsyntax_error WITH DEFAULT KEY.
