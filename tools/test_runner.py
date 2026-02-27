"""
Test Runner - Executes tests and reports results
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import subprocess
import logging
import json


@dataclass
class TestResult:
    """Test result structure"""
    passed: bool
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    output: str = ""
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class TestRunner:
    """
    Test Runner - Executes tests and reports results
    
    Supports:
    - pytest
    - unittest
    - Other test frameworks
    """
    
    def __init__(
        self,
        framework: str = "pytest",
        timeout: int = 300,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize test runner
        
        Args:
            framework: Test framework to use
            timeout: Test execution timeout in seconds
            logger: Logger instance
        """
        self.framework = framework
        self.timeout = timeout
        self.logger = logger or logging.getLogger("TestRunner")
    
    async def run_tests(
        self,
        test_path: str = "tests",
        verbose: bool = True,
        coverage: bool = False
    ) -> TestResult:
        """
        Run tests
        
        Args:
            test_path: Path to tests
            verbose: Verbose output
            coverage: Enable coverage report
            
        Returns:
            TestResult with test execution results
        """
        self.logger.info(f"Running tests with {self.framework}: {test_path}")
        
        result = TestResult(passed=False)
        
        try:
            # Build command
            cmd = self._build_command(test_path, verbose, coverage)
            
            # Execute tests
            start_time = datetime.now()
            process = await self._execute_command(cmd)
            end_time = datetime.now()
            
            result.duration = (end_time - start_time).total_seconds()
            result.output = process.get("stdout", "") + process.get("stderr", "")
            
            # Parse results
            result = self._parse_output(result, process)
            
            self.logger.info(
                f"Tests completed: {result.passed_tests}/{result.total_tests} passed "
                f"in {result.duration:.2f}s"
            )
            
        except Exception as e:
            self.logger.error(f"Test execution failed: {str(e)}")
            result.errors.append({
                "type": "execution_error",
                "message": str(e)
            })
        
        return result
    
    def _build_command(
        self, 
        test_path: str, 
        verbose: bool, 
        coverage: bool
    ) -> List[str]:
        """Build test command based on framework"""
        if self.framework == "pytest":
            cmd = ["pytest", test_path, "-v" if verbose else "-q"]
            if coverage:
                cmd.extend(["--cov", ".", "--cov-report", "json"])
        elif self.framework == "unittest":
            cmd = ["python", "-m", "unittest", "discover", test_path, "-v" if verbose else ""]
        else:
            cmd = [self.framework, test_path]
        
        return cmd
    
    async def _execute_command(self, cmd: List[str]) -> Dict[str, str]:
        """Execute command and return output"""
        try:
            # Run in subprocess
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.timeout
                )
                
                return {
                    "returncode": proc.returncode,
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else ""
                }
                
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise TimeoutError(f"Test execution timed out after {self.timeout}s")
                
        except FileNotFoundError:
            raise RuntimeError(f"Test framework '{self.framework}' not found")
    
    def _parse_output(self, result: TestResult, process: Dict[str, str]) -> TestResult:
        """Parse test output"""
        output = process.get("stdout", "") + process.get("stderr", "")
        returncode = process.get("returncode", 1)
        
        result.output = output
        
        # Parse pytest output
        if self.framework == "pytest":
            # Look for summary line
            # Example: "5 passed in 1.23s" or "3 passed, 1 failed"
            import re
            
            # Match patterns like "5 passed" or "3 passed, 1 failed"
            match = re.search(r'(\d+)\s+passed', output)
            if match:
                result.passed_tests = int(match.group(1))
                result.total_tests = result.passed_tests
            
            match = re.search(r'(\d+)\s+failed', output)
            if match:
                result.failed_tests = int(match.group(1))
                result.total_tests += result.failed_tests
            
            match = re.search(r'(\d+)\s+skipped', output)
            if match:
                result.skipped_tests = int(match.group(1))
            
            # Check for errors
            if "ERROR" in output:
                error_lines = [line for line in output.split('\n') if 'ERROR' in line]
                for line in error_lines[:5]:  # Limit to 5 errors
                    result.errors.append({
                        "type": "error",
                        "message": line.strip()
                    })
            
            # Check for failures
            if "FAILED" in output:
                failure_lines = [line for line in output.split('\n') if 'FAILED' in line]
                for line in failure_lines[:5]:  # Limit to 5 failures
                    result.errors.append({
                        "type": "failure",
                        "message": line.strip()
                    })
        
        # Determine overall pass/fail
        result.passed = (
            returncode == 0 and 
            result.failed_tests == 0 and 
            len(result.errors) == 0
        )
        
        return result
    
    async def run_specific_test(self, test_name: str) -> TestResult:
        """Run a specific test"""
        self.logger.info(f"Running specific test: {test_name}")
        
        if self.framework == "pytest":
            cmd = ["pytest", test_name, "-v"]
        else:
            cmd = [self.framework, test_name]
        
        process = await self._execute_command(cmd)
        return self._parse_output(TestResult(passed=False), process)
    
    def get_test_files(self, test_path: str = "tests") -> List[str]:
        """Get list of test files"""
        import os
        import glob
        
        if self.framework == "pytest":
            pattern = f"{test_path}/test_*.py"
        else:
            pattern = f"{test_path}/*_test.py"
        
        return glob.glob(pattern)


# Import asyncio for subprocess
import asyncio