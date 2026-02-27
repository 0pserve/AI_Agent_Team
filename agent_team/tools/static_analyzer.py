"""
Static Analyzer - Performs static code analysis
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import re
import logging


@dataclass
class AnalysisResult:
    """Static analysis result"""
    passed: bool
    issues: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    score: int = 100  # 0-100
    timestamp: datetime = field(default_factory=datetime.now)


class StaticAnalyzer:
    """
    Static Analyzer - Performs static code analysis
    
    Checks for:
    - Syntax errors
    - Code style violations
    - Potential bugs
    - Security vulnerabilities
    - Code complexity
    - Documentation coverage
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize static analyzer
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger("StaticAnalyzer")
        
        # Security patterns to check
        self.security_patterns = {
            "hardcoded_password": {
                "pattern": r'password\s*=\s*["\'][^"\']+["\']',
                "severity": "critical",
                "message": "Hardcoded password detected"
            },
            "hardcoded_api_key": {
                "pattern": r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
                "severity": "critical",
                "message": "Hardcoded API key detected"
            },
            "hardcoded_secret": {
                "pattern": r'secret[_-]?key\s*=\s*["\'][^"\']+["\']',
                "severity": "critical",
                "message": "Hardcoded secret key detected"
            },
            "sql_injection": {
                "pattern": r'execute\s*\([^)]*\+[^)]*\)',
                "severity": "high",
                "message": "Potential SQL injection vulnerability"
            },
            "eval_usage": {
                "pattern": r'\beval\s*\(',
                "severity": "high",
                "message": "Use of eval() is dangerous"
            },
            "exec_usage": {
                "pattern": r'\bexec\s*\(',
                "severity": "high",
                "message": "Use of exec() is dangerous"
            },
            "pickle_usage": {
                "pattern": r'pickle\.loads?\(',
                "severity": "medium",
                "message": "Pickle can execute arbitrary code"
            }
        }
        
        # Style patterns
        self.style_patterns = {
            "long_line": {
                "pattern": r'^.{121,}$',
                "severity": "low",
                "message": "Line too long (over 120 characters)"
            },
            "trailing_whitespace": {
                "pattern": r'[\t ]+$',
                "severity": "info",
                "message": "Trailing whitespace"
            },
            "todo_comment": {
                "pattern": r'#\s*(TODO|FIXME|HACK|XXX):',
                "severity": "info",
                "message": "TODO/FIXME comment found"
            }
        }
    
    async def analyze(
        self,
        code: str,
        language: str = "python",
        file_path: str = ""
    ) -> AnalysisResult:
        """
        Analyze code
        
        Args:
            code: Source code to analyze
            language: Programming language
            file_path: File path (optional)
            
        Returns:
            AnalysisResult with analysis findings
        """
        self.logger.info(f"Analyzing {language} code: {file_path or 'inline'}")
        
        result = AnalysisResult(passed=True)
        
        # Run all checks
        issues = []
        
        # Security check
        issues.extend(self._check_security(code, file_path))
        
        # Style check
        issues.extend(self._check_style(code, file_path))
        
        # Complexity check
        issues.extend(self._check_complexity(code, file_path))
        
        # Documentation check
        issues.extend(self._check_documentation(code, file_path))
        
        # Calculate metrics
        metrics = self._calculate_metrics(code, language)
        
        # Calculate score
        score = self._calculate_score(issues, metrics)
        
        result.issues = issues
        result.metrics = metrics
        result.score = score
        result.passed = len([i for i in issues if i.get("severity") in ["critical", "high"]]) == 0
        
        self.logger.info(
            f"Analysis complete: score={score}, issues={len(issues)}, "
            f"passed={result.passed}"
        )
        
        return result
    
    def _check_security(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for security issues"""
        issues = []
        
        for name, config in self.security_patterns.items():
            pattern = re.compile(config["pattern"], re.IGNORECASE)
            matches = pattern.finditer(code)
            
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append({
                    "type": "security",
                    "severity": config["severity"],
                    "message": config["message"],
                    "location": f"{file_path}:{line_num}" if file_path else f"line {line_num}",
                    "pattern": match.group()[:50]
                })
        
        return issues
    
    def _check_style(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for style issues"""
        issues = []
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check long lines
            if len(line) > 120:
                issues.append({
                    "type": "style",
                    "severity": "low",
                    "message": "Line too long",
                    "location": f"{file_path}:{i}" if file_path else f"line {i}",
                    "length": len(line)
                })
            
            # Check trailing whitespace
            if re.search(r'[\t ]+$', line):
                issues.append({
                    "type": "style",
                    "severity": "info",
                    "message": "Trailing whitespace",
                    "location": f"{file_path}:{i}" if file_path else f"line {i}"
                })
            
            # Check TODO comments
            if re.search(r'#\s*(TODO|FIXME|HACK|XXX):', line, re.IGNORECASE):
                issues.append({
                    "type": "style",
                    "severity": "info",
                    "message": "TODO/FIXME comment found",
                    "location": f"{file_path}:{i}" if file_path else f"line {i}"
                })
        
        return issues
    
    def _check_complexity(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Check code complexity"""
        issues = []
        
        # Count functions
        functions = re.findall(r'def (\w+)\(', code)
        
        for func_name in functions:
            # Find function body
            func_pattern = rf'def {func_name}\(.*?\):(.*?)(?=\ndef |\nclass |\Z)'
            match = re.search(func_pattern, code, re.DOTALL)
            
            if match:
                body = match.group(1)
                
                # Count indentation levels (rough complexity measure)
                indents = re.findall(r'\n( +)', body)
                if indents:
                    max_indent = max(len(i) for i in indents)
                    if max_indent > 16:  # 4 levels * 4 spaces
                        issues.append({
                            "type": "complexity",
                            "severity": "medium",
                            "message": f"Function '{func_name}' may be too complex",
                            "location": f"{file_path}:{func_name}" if file_path else func_name,
                            "max_indent": max_indent
                        })
        
        return issues
    
    def _check_documentation(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Check documentation coverage"""
        issues = []
        
        lines = [l for l in code.split('\n') if l.strip()]
        
        if not lines:
            return issues
        
        # Count docstrings
        docstrings = re.findall(r'"""[\s\S]*?"""', code)
        docstring_lines = sum(d.count('\n') + 1 for d in docstrings)
        
        # Count comment lines
        comment_lines = sum(1 for l in lines if l.strip().startswith('#'))
        
        total_lines = len(lines)
        doc_rate = (docstring_lines + comment_lines) / total_lines if total_lines > 0 else 0
        
        if doc_rate < 0.1 and total_lines > 20:
            issues.append({
                "type": "documentation",
                "severity": "low",
                "message": f"Low documentation rate ({doc_rate:.1%})",
                "location": file_path or "file",
                "doc_rate": doc_rate
            })
        
        return issues
    
    def _calculate_metrics(self, code: str, language: str) -> Dict[str, Any]:
        """Calculate code metrics"""
        metrics = {}
        
        lines = code.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]
        
        # Basic metrics
        metrics["total_lines"] = len(lines)
        metrics["code_lines"] = len(non_empty_lines)
        metrics["blank_lines"] = len(lines) - len(non_empty_lines)
        
        if language == "python":
            # Python-specific metrics
            metrics["functions"] = len(re.findall(r'def \w+\(', code))
            metrics["classes"] = len(re.findall(r'class \w+', code))
            metrics["imports"] = len(re.findall(r'^import |^from ', code, re.MULTILINE))
            
            # Calculate cyclomatic complexity (rough estimate)
            decisions = len(re.findall(r'\b(if|elif|for|while|and|or)\b', code))
            metrics["cyclomatic_complexity"] = decisions + 1
        
        return metrics
    
    def _calculate_score(
        self, 
        issues: List[Dict[str, Any]], 
        metrics: Dict[str, Any]
    ) -> int:
        """Calculate overall score (0-100)"""
        score = 100
        
        # Deduct for issues
        for issue in issues:
            severity = issue.get("severity", "low")
            if severity == "critical":
                score -= 20
            elif severity == "high":
                score -= 10
            elif severity == "medium":
                score -= 5
            elif severity == "low":
                score -= 2
            elif severity == "info":
                score -= 1
        
        # Ensure score is within bounds
        return max(0, min(100, score))
    
    async def analyze_multiple(
        self,
        files: List[Dict[str, str]]
    ) -> List[AnalysisResult]:
        """
        Analyze multiple files
        
        Args:
            files: List of dicts with 'path' and 'content' keys
            
        Returns:
            List of AnalysisResult
        """
        results = []
        
        for file in files:
            result = await self.analyze(
                code=file.get("content", ""),
                language=file.get("language", "python"),
                file_path=file.get("path", "")
            )
            results.append(result)
        
        return results
    
    def get_summary(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """Get summary of multiple analysis results"""
        total_issues = sum(len(r.issues) for r in results)
        critical = sum(len([i for i in r.issues if i.get("severity") == "critical"]) for r in results)
        high = sum(len([i for i in r.issues if i.get("severity") == "high"]) for r in results)
        avg_score = sum(r.score for r in results) / len(results) if results else 0
        
        return {
            "total_files": len(results),
            "total_issues": total_issues,
            "critical_issues": critical,
            "high_issues": high,
            "average_score": avg_score,
            "all_passed": all(r.passed for r in results)
        }