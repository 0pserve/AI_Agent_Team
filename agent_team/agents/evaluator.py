"""
Evaluator Agent - Evaluates code quality and performs debugging analysis
"""
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re

from .base import BaseAgent, AgentResponse
from .coder import GeneratedCode, CodeFile


class QualityLevel(Enum):
    """Code quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAILED = "failed"


class IssueSeverity(Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeIssue:
    """Code issue structure"""
    severity: IssueSeverity
    category: str  # syntax, style, security, performance, bug
    message: str
    location: str  # file:line or file:function
    suggestion: Optional[str] = None


@dataclass
class QualityMetrics:
    """Code quality metrics"""
    test_coverage: float = 0.0
    complexity: int = 0
    duplicate_rate: float = 0.0
    documentation_rate: float = 0.0
    security_issues: int = 0
    bugs_found: int = 0
    
    def is_acceptable(
        self,
        min_coverage: float = 0.70,
        max_complexity: int = 10,
        max_duplicate: float = 0.05,
        min_docs: float = 0.30
    ) -> bool:
        """Check if metrics meet acceptable thresholds"""
        return (
            self.test_coverage >= min_coverage and
            self.complexity <= max_complexity and
            self.duplicate_rate <= max_duplicate and
            self.documentation_rate >= min_docs and
            self.security_issues == 0 and
            self.bugs_found == 0
        )


@dataclass
class EvaluationResult:
    """Evaluation result structure"""
    passed: bool
    quality_level: QualityLevel
    metrics: QualityMetrics
    issues: List[CodeIssue] = field(default_factory=list)
    summary: str = ""
    suggestions: List[str] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=datetime.now)


class EvaluatorAgent(BaseAgent):
    """
    Evaluator Agent - Evaluates code quality and performs debugging analysis
    
    Responsibilities:
    - Evaluate code quality (readability, maintainability, performance)
    - Perform static analysis (syntax errors, type checking, code smells)
    - Run tests and analyze failures
    - Detect bugs and suggest fixes
    - Analyze security vulnerabilities
    """
    
    SYSTEM_PROMPT = """You are an Expert Code Reviewer AI assistant.
Your role is to thoroughly evaluate code quality and identify issues.

When evaluating code, you should:
1. Check for syntax errors and type issues
2. Evaluate code readability and maintainability
3. Identify potential bugs and logical errors
4. Check for security vulnerabilities
5. Assess performance concerns
6. Verify test coverage and quality

Provide detailed feedback with:
- Issue severity (critical, high, medium, low, info)
- Issue category (syntax, style, security, performance, bug)
- Specific location (file:line)
- Suggestion for fixing the issue"""

    def __init__(
        self,
        llm_config: Optional[Dict[str, Any]] = None,
        logger: Optional[Any] = None,
        evaluation_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__("EvaluatorAgent", llm_config, logger)
        self.evaluation_config = evaluation_config or {}
        self.last_evaluation: Optional[EvaluationResult] = None
        
        # Evaluation thresholds
        self.min_test_coverage = self.evaluation_config.get('min_test_coverage', 0.70)
        self.max_complexity = self.evaluation_config.get('max_complexity', 10)
        self.max_duplicate_rate = self.evaluation_config.get('max_duplicate_rate', 0.05)
        self.min_documentation_rate = self.evaluation_config.get('min_documentation_rate', 0.30)
        self.max_iterations = self.evaluation_config.get('max_iterations', 3)
    
    async def execute(
        self, 
        input_data: Any, 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Execute the evaluator agent to evaluate code
        
        Args:
            input_data: GeneratedCode or dict with code files
            context: Additional context (optional)
            
        Returns:
            AgentResponse with EvaluationResult
        """
        self.logger.info(f"[EvaluatorAgent] Starting code evaluation")
        
        try:
            # Parse input
            if isinstance(input_data, GeneratedCode):
                generated_code = input_data
            elif isinstance(input_data, dict):
                # Try to reconstruct from dict
                generated_code = self._dict_to_generated_code(input_data)
            else:
                raise ValueError("Input must be GeneratedCode or dict")
            
            # Evaluate code
            result = await self._evaluate_code(generated_code, context)
            
            self.last_evaluation = result
            
            # Add to history
            self.add_message(
                'assistant', 
                f"Evaluation completed: {'PASSED' if result.passed else 'FAILED'} - {result.quality_level.value}"
            )
            
            self.logger.info(
                f"[EvaluatorAgent] Evaluation completed: {result.quality_level.value} "
                f"(Issues: {len(result.issues)})"
            )
            
            return AgentResponse(
                success=True,
                content=result,
                metadata={
                    "passed": result.passed,
                    "quality_level": result.quality_level.value,
                    "issues_count": len(result.issues),
                    "critical_issues": len([i for i in result.issues if i.severity == IssueSeverity.CRITICAL])
                }
            )
            
        except Exception as e:
            self.logger.error(f"[EvaluatorAgent] Error: {str(e)}")
            return AgentResponse(
                success=False,
                content=None,
                error=str(e)
            )
    
    def _dict_to_generated_code(self, data: Dict[str, Any]) -> GeneratedCode:
        """Convert dict to GeneratedCode"""
        files = []
        for file_data in data.get('files', []):
            if isinstance(file_data, dict):
                files.append(CodeFile(
                    path=file_data.get('path', ''),
                    content=file_data.get('content', ''),
                    language=file_data.get('language', 'python'),
                    file_type=file_data.get('file_type', 'source')
                ))
        
        return GeneratedCode(
            project_name=data.get('project_name', 'project'),
            files=files,
            metadata=data.get('metadata', {})
        )
    
    async def _evaluate_code(
        self, 
        generated_code: GeneratedCode,
        context: Optional[Dict[str, Any]]
    ) -> EvaluationResult:
        """Evaluate the generated code"""
        issues: List[CodeIssue] = []
        metrics = QualityMetrics()
        
        # Evaluate each file
        for code_file in generated_code.files:
            file_issues = self._evaluate_file(code_file)
            issues.extend(file_issues)
        
        # Calculate metrics
        metrics = self._calculate_metrics(generated_code, issues)
        
        # Determine if evaluation passed
        passed = metrics.is_acceptable(
            min_coverage=self.min_test_coverage,
            max_complexity=self.max_complexity,
            max_duplicate=self.max_duplicate_rate,
            min_docs=self.min_documentation_rate
        )
        
        # Determine quality level
        quality_level = self._determine_quality_level(metrics, issues)
        
        # Generate summary and suggestions
        summary = self._generate_summary(passed, metrics, issues)
        suggestions = self._generate_suggestions(issues)
        
        return EvaluationResult(
            passed=passed,
            quality_level=quality_level,
            metrics=metrics,
            issues=issues,
            summary=summary,
            suggestions=suggestions
        )
    
    def _evaluate_file(self, code_file: CodeFile) -> List[CodeIssue]:
        """Evaluate a single code file"""
        issues: List[CodeIssue] = []
        
        # Skip non-code files
        if code_file.file_type not in ['source', 'test']:
            return issues
        
        content = code_file.content
        
        # Syntax checks (basic)
        issues.extend(self._check_syntax(code_file))
        
        # Style checks
        issues.extend(self._check_style(code_file))
        
        # Security checks
        issues.extend(self._check_security(code_file))
        
        # Documentation checks
        issues.extend(self._check_documentation(code_file))
        
        return issues
    
    def _check_syntax(self, code_file: CodeFile) -> List[CodeIssue]:
        """Check for syntax errors"""
        issues: List[CodeIssue] = []
        
        if code_file.language != 'python':
            return issues
        
        content = code_file.content
        
        # Check for common syntax issues
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for undefined variables (basic)
            if 'undefined' in line.lower() and 'variable' in line.lower():
                issues.append(CodeIssue(
                    severity=IssueSeverity.HIGH,
                    category='syntax',
                    message=f"Potential undefined variable reference",
                    location=f"{code_file.path}:{i}",
                    suggestion="Define the variable before using it"
                ))
        
        return issues
    
    def _check_style(self, code_file: CodeFile) -> List[CodeIssue]:
        """Check code style"""
        issues: List[CodeIssue] = []
        
        content = code_file.content
        lines = content.split('\n')
        
        # Check line length
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(CodeIssue(
                    severity=IssueSeverity.LOW,
                    category='style',
                    message=f"Line too long ({len(line)} characters)",
                    location=f"{code_file.path}:{i}",
                    suggestion="Consider breaking the line into multiple lines"
                ))
        
        # Check for TODO comments
        if 'TODO' in content or 'FIXME' in content:
            issues.append(CodeIssue(
                severity=IssueSeverity.INFO,
                category='style',
                message="TODO/FIXME comments found",
                location=f"{code_file.path}",
                suggestion="Address TODO items before finalizing"
            ))
        
        # Check function complexity (basic)
        if code_file.language == 'python':
            functions = re.findall(r'def (\w+)\(', content)
            for func in functions:
                # Count indentation levels in function
                func_match = re.search(rf'def {func}\(.*?\):(.*?)(?=\ndef |\nclass |\Z)', content, re.DOTALL)
                if func_match:
                    func_body = func_match.group(1)
                    indent_levels = len(set(re.findall(r'\n( +)', func_body)))
                    if indent_levels > 3:
                        issues.append(CodeIssue(
                            severity=IssueSeverity.MEDIUM,
                            category='style',
                            message=f"Function '{func}' may be too complex",
                            location=f"{code_file.path}:{func}",
                            suggestion="Consider breaking into smaller functions"
                        ))
        
        return issues
    
    def _check_security(self, code_file: CodeFile) -> List[CodeIssue]:
        """Check for security vulnerabilities"""
        issues: List[CodeIssue] = []
        
        content = code_file.content
        
        # Check for hardcoded secrets
        if re.search(r'password\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
            issues.append(CodeIssue(
                severity=IssueSeverity.CRITICAL,
                category='security',
                message="Hardcoded password found",
                location=code_file.path,
                suggestion="Use environment variables for sensitive data"
            ))
        
        if re.search(r'api[_-]?key\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
            issues.append(CodeIssue(
                severity=IssueSeverity.CRITICAL,
                category='security',
                message="Hardcoded API key found",
                location=code_file.path,
                suggestion="Use environment variables for API keys"
            ))
        
        # Check for SQL injection vulnerabilities
        if 'execute(' in content and '+' in content:
            issues.append(CodeIssue(
                severity=IssueSeverity.HIGH,
                category='security',
                message="Potential SQL injection vulnerability",
                location=code_file.path,
                suggestion="Use parameterized queries"
            ))
        
        # Check for eval usage
        if 'eval(' in content:
            issues.append(CodeIssue(
                severity=IssueSeverity.HIGH,
                category='security',
                message="Use of eval() is dangerous",
                location=code_file.path,
                suggestion="Avoid using eval(), use safer alternatives"
            ))
        
        return issues
    
    def _check_documentation(self, code_file: CodeFile) -> List[CodeIssue]:
        """Check documentation"""
        issues: List[CodeIssue] = []
        
        content = code_file.content
        lines = content.split('\n')
        
        # Count comment lines
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        total_lines = len([l for l in lines if l.strip()])
        
        if total_lines > 0:
            doc_rate = comment_lines / total_lines
            
            if doc_rate < 0.1 and code_file.file_type == 'source':
                issues.append(CodeIssue(
                    severity=IssueSeverity.MEDIUM,
                    category='documentation',
                    message=f"Low documentation rate ({doc_rate:.1%})",
                    location=code_file.path,
                    suggestion="Add more comments and docstrings"
                ))
        
        return issues
    
    def _calculate_metrics(
        self, 
        generated_code: GeneratedCode, 
        issues: List[CodeIssue]
    ) -> QualityMetrics:
        """Calculate quality metrics"""
        metrics = QualityMetrics()
        
        # Count issues by category
        metrics.security_issues = len([i for i in issues if i.category == 'security'])
        metrics.bugs_found = len([i for i in issues if i.category == 'bug'])
        
        # Calculate test coverage (estimated based on test files)
        total_files = len([f for f in generated_code.files if f.file_type == 'source'])
        test_files = len([f for f in generated_code.files if f.file_type == 'test'])
        
        if total_files > 0:
            metrics.test_coverage = min(test_files / total_files, 1.0)
        
        # Calculate documentation rate
        all_content = '\n'.join(f.content for f in generated_code.files if f.file_type == 'source')
        lines = [l for l in all_content.split('\n') if l.strip()]
        comment_lines = sum(1 for l in lines if l.strip().startswith('#') or l.strip().startswith('"""'))
        
        if lines:
            metrics.documentation_rate = comment_lines / len(lines)
        
        # Estimate complexity
        metrics.complexity = min(len(issues) * 2, 10)
        
        return metrics
    
    def _determine_quality_level(
        self, 
        metrics: QualityMetrics, 
        issues: List[CodeIssue]
    ) -> QualityLevel:
        """Determine overall quality level"""
        critical_issues = len([i for i in issues if i.severity == IssueSeverity.CRITICAL])
        high_issues = len([i for i in issues if i.severity == IssueSeverity.HIGH])
        
        if critical_issues > 0 or not metrics.is_acceptable():
            return QualityLevel.POOR
        elif high_issues > 2:
            return QualityLevel.ACCEPTABLE
        elif metrics.test_coverage >= 0.8 and metrics.security_issues == 0:
            return QualityLevel.EXCELLENT
        elif metrics.test_coverage >= 0.5:
            return QualityLevel.GOOD
        else:
            return QualityLevel.ACCEPTABLE
    
    def _generate_summary(
        self, 
        passed: bool, 
        metrics: QualityMetrics, 
        issues: List[CodeIssue]
    ) -> str:
        """Generate evaluation summary"""
        if passed:
            return (
                f"✅ Code evaluation PASSED. "
                f"Found {len(issues)} issues. "
                f"Test coverage: {metrics.test_coverage:.0%}. "
                f"Security issues: {metrics.security_issues}"
            )
        else:
            return (
                f"❌ Code evaluation FAILED. "
                f"Found {len(issues)} issues. "
                f"Test coverage: {metrics.test_coverage:.0%}. "
                f"Security issues: {metrics.security_issues}. "
                f"Critical issues must be fixed."
            )
    
    def _generate_suggestions(self, issues: List[CodeIssue]) -> List[str]:
        """Generate suggestions based on issues"""
        suggestions = []
        
        # Group by severity
        critical = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        high = [i for i in issues if i.severity == IssueSeverity.HIGH]
        medium = [i for i in issues if i.severity == IssueSeverity.MEDIUM]
        
        if critical:
            suggestions.append(f"Fix {len(critical)} critical security issues immediately")
        
        if high:
            suggestions.append(f"Address {len(high)} high priority issues")
        
        if medium:
            suggestions.append(f"Consider fixing {len(medium)} medium priority issues")
        
        if not suggestions:
            suggestions.append("Code quality is good. Consider adding more tests for better coverage.")
        
        return suggestions
    
    def get_last_evaluation(self) -> Optional[EvaluationResult]:
        """Get the last evaluation result"""
        return self.last_evaluation
    
    async def analyze_test_failure(
        self, 
        test_output: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Analyze test failures and suggest fixes
        
        Args:
            test_output: Test output/traceback
            context: Additional context
            
        Returns:
            AgentResponse with analysis and suggestions
        """
        self.logger.info(f"[EvaluatorAgent] Analyzing test failure")
        
        analysis = {
            "test_output": test_output,
            "likely_cause": "Unknown",
            "suggestions": []
        }
        
        # Basic pattern matching for common errors
        if "AssertionError" in test_output:
            analysis["likely_cause"] = "Test assertion failed - expected vs actual value mismatch"
            analysis["suggestions"].append("Check the expected values in the test")
        
        if "ImportError" in test_output or "ModuleNotFoundError" in test_output:
            analysis["likely_cause"] = "Missing module or import error"
            analysis["suggestions"].append("Check if all required modules are installed")
        
        if "SyntaxError" in test_output:
            analysis["likely_cause"] = "Syntax error in the code"
            analysis["suggestions"].append("Fix the syntax error indicated in the traceback")
        
        if "AttributeError" in test_output:
            analysis["likely_cause"] = "Accessing non-existent attribute"
            analysis["suggestions"].append("Check the object has the attribute you're trying to access")
        
        return AgentResponse(
            success=True,
            content=analysis,
            metadata={"analysis_type": "test_failure"}
        )
