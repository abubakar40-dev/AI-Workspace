# agent/code_agent.py
# Specialized agent for software development, coding, debugging

import json
import os
import tempfile
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.agent_base import BaseAgent, AgentType, AgentStatus, AgentResult, AgentTask


class CodeAgent(BaseAgent):
    """Agent specialized in software development: coding, debugging, testing, refactoring"""
    
    def __init__(self, name: str = "CodeAgent"):
        super().__init__(AgentType.CODE, name)
        self._project_context: Dict = {}
        self._code_files: Dict[str, str] = {}  # path -> content
    
    def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute coding task"""
        enhanced_goal = self._enhance_code_goal(task.goal, task.context)
        task.goal = enhanced_goal
        return super().execute_task(task)
    
    def _enhance_code_goal(self, goal: str, context: Dict) -> str:
        """Enhance goal with code development methodology"""
        project_info = ""
        if self._project_context:
            project_info = f"""
PROJECT CONTEXT:
- Root: {self._project_context.get('root', 'unknown')}
- Language: {self._project_context.get('language', 'unknown')}
- Framework: {self._project_context.get('framework', 'unknown')}
- Files: {len(self._code_files)} tracked
"""
        
        research_data = ""
        if context:
            for dep_id, dep_result in context.items():
                if dep_result and isinstance(dep_result, dict) and dep_result.get("data"):
                    research_data += f"\n\n--- REFERENCE: {dep_id} ---\n{dep_result['data'][:3000]}"
        
        return f"""
CODE DEVELOPMENT TASK: {goal}

{project_info}

REFERENCE MATERIALS:
{research_data if research_data else "No external references"}

REQUIREMENTS:
1. Write clean, production-ready code
2. Follow best practices for the language/framework
3. Include error handling and logging
4. Add documentation/comments
5. Write tests where appropriate
6. Use existing project structure and conventions
7. Save files using file_controller or claude_code

OUTPUT: Working code saved to project, summary of changes
"""
    
    def set_project_context(self, root: str, language: str = "", framework: str = ""):
        """Set project context for the agent"""
        self._project_context = {
            "root": root,
            "language": language,
            "framework": framework
        }
        # Scan existing files
        self._scan_project_files(root)
    
    def _scan_project_files(self, root: str):
        """Scan project for existing code files"""
        try:
            root_path = Path(root)
            if not root_path.exists():
                return
            
            extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', '.php', '.rb'}
            for ext in extensions:
                for file_path in root_path.rglob(f"*{ext}"):
                    try:
                        rel_path = file_path.relative_to(root_path)
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if len(content) < 50000:  # Skip huge files
                            self._code_files[str(rel_path)] = content[:5000]
                    except Exception:
                        pass
        except Exception:
            pass
    
    def _execute_plan(self, plan: dict, task: AgentTask) -> str:
        """Execute code development plan"""
        steps = plan.get("steps", [])
        if not steps:
            return "No valid code plan created"
        
        completed_steps = []
        step_results = {}
        
        for step in steps:
            if task.cancel_flag.is_set():
                return "Code development cancelled"
            
            step_num = step.get("step", "?")
            tool = step.get("tool", "")
            desc = step.get("description", "")
            params = step.get("parameters", {})
            
            from agent.executor import _inject_context
            params = _inject_context(params, tool, step_results, goal=task.goal)
            
            self._notify_progress(AgentStatus.RUNNING, f"Coding: {desc[:60]}")
            
            print(f"\n[{self.name}] 💻 Code Step {step_num}: [{tool}] {desc}")
            
            attempt = 1
            step_ok = False
            
            while attempt <= 3:
                if task.cancel_flag.is_set():
                    return "Code development cancelled"
                
                try:
                    from agent.executor import _call_tool
                    result = _call_tool(tool, params, None)
                    step_results[step_num] = result
                    completed_steps.append(step)
                    print(f"[{self.name}] ✅ Code Step {step_num} done")
                    step_ok = True
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"[{self.name}] ❌ Code Step {step_num} attempt {attempt} failed: {error_msg}")
                    
                    from agent.error_handler import analyze_error, generate_fix, ErrorDecision
                    recovery = analyze_error(step, error_msg, attempt=attempt)
                    decision = recovery["decision"]
                    
                    if decision == ErrorDecision.RETRY:
                        attempt += 1
                        import time; time.sleep(2)
                        continue
                    elif decision == ErrorDecision.SKIP:
                        completed_steps.append(step)
                        step_ok = True
                        break
                    elif decision == ErrorDecision.ABORT:
                        return f"Code development aborted: {recovery.get('reason', '')}"
                    else:
                        fix_suggestion = recovery.get("fix_suggestion", "")
                        if fix_suggestion and tool != "generated_code":
                            try:
                                fixed_step = generate_fix(step, error_msg, fix_suggestion)
                                from agent.executor import _call_tool
                                res = _call_tool(fixed_step["tool"], fixed_step["parameters"], None)
                                step_results[step_num] = res
                                completed_steps.append(step)
                                step_ok = True
                                break
                            except Exception:
                                pass
                        
                        return f"Code step failed: {error_msg}"
            
            if not step_ok:
                return f"Code step {step_num} failed after retries"
        
        return self._summarize_code_work(task.goal, completed_steps, step_results)
    
    def _summarize_code_work(self, goal: str, completed_steps: list, step_results: dict) -> str:
        """Summarize code development work"""
        files_created = []
        for result in step_results.values():
            if isinstance(result, str):
                import re
                paths = re.findall(r'([/\w.-]+\.(?:py|js|ts|java|cpp|cs|go|rs|php|rb|html|css|json|yaml|yml))', result)
                files_created.extend(paths)
        
        summary = f"Code development completed: {len(completed_steps)} steps for {goal[:60]}"
        if files_created:
            summary += f"\nFiles created/modified: {', '.join(set(files_created)[:10])}"
        
        return summary
    
    def write_code_file(self, path: str, content: str) -> str:
        """Write a code file to the project"""
        try:
            full_path = Path(self._project_context.get('root', '.')) / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            self._code_files[path] = content[:5000]
            return f"File written: {path}"
        except Exception as e:
            return f"Failed to write {path}: {e}"
    
    def read_code_file(self, path: str) -> str:
        """Read a code file from the project"""
        try:
            full_path = Path(self._project_context.get('root', '.')) / path
            content = full_path.read_text(encoding='utf-8')
            self._code_files[path] = content[:5000]
            return content
        except Exception as e:
            return f"Failed to read {path}: {e}"
    
    def run_tests(self, test_command: str = "pytest") -> str:
        """Run tests in the project"""
        try:
            import subprocess
            root = self._project_context.get('root', '.')
            result = subprocess.run(
                test_command.split(),
                cwd=root,
                capture_output=True,
                text=True,
                timeout=120
            )
            return f"Exit code: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except Exception as e:
            return f"Test run failed: {e}"


# Factory function
def create_code_agent(name: str = "CodeAgent") -> CodeAgent:
    """Create a code agent"""
    return CodeAgent(name)
