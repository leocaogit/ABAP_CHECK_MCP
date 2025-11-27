"""
Data models for ABAP syntax checker MCP server.

This module defines the data structures used to represent syntax check results
and errors returned from the ERP system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import json


@dataclass
class SyntaxError:
    """Represents a single syntax error or warning from ABAP syntax check.
    
    Attributes:
        line: Error line number in the source code
        type: Message type ('E' for error, 'W' for warning)
        message: Error description text
    """
    line: int
    type: str
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the syntax error to a dictionary.
        
        Returns:
            Dictionary representation of the syntax error
        """
        return {
            "line": self.line,
            "type": self.type,
            "message": self.message
        }
    
    @classmethod
    def from_rfc_row(cls, row: Dict[str, Any]) -> "SyntaxError":
        """Create a SyntaxError from an RFC response table row.
        
        Args:
            row: Dictionary containing LINE, TYPE, and MESSAGE fields
            
        Returns:
            SyntaxError instance
        """
        return cls(
            line=int(row.get("LINE", 0)),
            type=str(row.get("TYPE", "E")),
            message=str(row.get("MESSAGE", ""))
        )


@dataclass
class CheckResult:
    """Represents the complete result of an ABAP syntax check.
    
    Attributes:
        success: Whether the check execution was successful
        has_errors: Whether syntax errors were found
        errors: List of syntax errors and warnings
        message: Execution message (used when success is False)
    """
    success: bool
    has_errors: bool
    errors: List[SyntaxError] = field(default_factory=list)
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the check result to a dictionary.
        
        Returns:
            Dictionary representation of the check result
        """
        return {
            "success": self.success,
            "has_errors": self.has_errors,
            "errors": [error.to_dict() for error in self.errors],
            "message": self.message
        }
    
    def to_json(self) -> str:
        """Convert the check result to a JSON string.
        
        Returns:
            JSON string representation of the check result
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_rfc_response(cls, response: Dict[str, Any]) -> "CheckResult":
        """Create a CheckResult from an RFC function call response.
        
        Args:
            response: Dictionary containing EV_SUCCESS, EV_MESSAGE, and ET_ERRORS
            
        Returns:
            CheckResult instance
        """
        success = response.get("EV_SUCCESS", "") == "X"
        message = str(response.get("EV_MESSAGE", ""))
        error_table = response.get("ET_ERRORS", [])
        
        # Parse error table rows
        errors = [SyntaxError.from_rfc_row(row) for row in error_table]
        
        # Sort errors by line number
        errors.sort(key=lambda e: e.line)
        
        has_errors = len(errors) > 0
        
        return cls(
            success=success,
            has_errors=has_errors,
            errors=errors,
            message=message
        )
