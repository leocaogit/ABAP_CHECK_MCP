FUNCTION Z_CHECK_ABAP_SYNTAX.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(IV_CODE) TYPE  STRING
*"  EXPORTING
*"     VALUE(EV_SUCCESS) TYPE  CHAR1
*"     VALUE(EV_MESSAGE) TYPE  STRING
*"  TABLES
*"      ET_ERRORS STRUCTURE  ZSYNTAX_ERROR
*"----------------------------------------------------------------------

  " Local data declarations
  DATA: lv_program_name TYPE program VALUE 'ZTEMP_SYNTAX_CHECK',
        lv_timestamp    TYPE string,
        lv_line         TYPE i,
        lv_word         TYPE string,
        lv_message      TYPE string,
        lt_code         TYPE TABLE OF string,
        ls_error        TYPE zsyntax_error.

  " Initialize output parameters
  CLEAR: ev_success, ev_message, et_errors[].

  " Validate input
  IF iv_code IS INITIAL.
    ev_success = ''.
    ev_message = 'Input code is empty'.
    RETURN.
  ENDIF.

  " Generate unique program name with timestamp
  GET TIME STAMP FIELD DATA(lv_ts).
  lv_timestamp = lv_ts.
  CONCATENATE 'ZTEMP_' lv_timestamp INTO lv_program_name.

  " Add REPORT statement if not present
  DATA: lv_code_with_report TYPE string.
  IF iv_code NS 'REPORT' AND iv_code NS 'PROGRAM'.
    CONCATENATE 'REPORT ' lv_program_name '.' cl_abap_char_utilities=>newline iv_code
      INTO lv_code_with_report.
  ELSE.
    lv_code_with_report = iv_code.
  ENDIF.

  " Split code into lines for INSERT REPORT
  SPLIT lv_code_with_report AT cl_abap_char_utilities=>newline INTO TABLE lt_code.

  " Create temporary program
  TRY.
      INSERT REPORT lv_program_name FROM lt_code.
      
      " Perform syntax check
      SYNTAX-CHECK FOR lt_code MESSAGE lv_message LINE lv_line WORD lv_word.
      
      " Check if syntax check found errors
      IF sy-subrc <> 0.
        " Syntax errors found
        ls_error-line = lv_line.
        ls_error-type = 'E'.
        ls_error-message = lv_message.
        APPEND ls_error TO et_errors.
      ENDIF.
      
      " Sort errors by line number
      SORT et_errors BY line ASCENDING.
      
      " Delete temporary program
      DELETE REPORT lv_program_name.
      
      " Set success flag
      ev_success = 'X'.
      ev_message = 'Syntax check completed successfully'.
      
    CATCH cx_root INTO DATA(lx_error).
      " Handle any exceptions
      ev_success = ''.
      ev_message = lx_error->get_text( ).
      
      " Ensure temporary program is deleted even on error
      TRY.
          DELETE REPORT lv_program_name.
        CATCH cx_root.
          " Ignore errors during cleanup
      ENDTRY.
  ENDTRY.

ENDFUNCTION.
