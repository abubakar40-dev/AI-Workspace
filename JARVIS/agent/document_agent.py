# agent/document_agent.py
# Specialized agent for document creation: PDF, DOCX, PPTX, XLSX, reports

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.agent_base import BaseAgent, AgentType, AgentStatus, AgentResult, AgentTask


class DocumentAgent(BaseAgent):
    """Agent specialized in creating documents: PDF, DOCX, PPTX, XLSX, reports"""
    
    def __init__(self, name: str = "DocumentAgent"):
        super().__init__(AgentType.DOCUMENT, name)
        self._document_templates = {
            "report": "professional report with title page, TOC, sections, appendix",
            "presentation": "slide deck with title, agenda, content slides, conclusion",
            "spreadsheet": "structured data with headers, formulas, formatting",
            "letter": "formal letter with header, body, closing",
            "memo": "internal memorandum format",
            "proposal": "business proposal with executive summary, details, pricing",
            "whitepaper": "technical whitepaper with abstract, methodology, results",
            "article": "blog article or technical article",
        }
    
    def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute document creation task"""
        enhanced_goal = self._enhance_document_goal(task.goal, task.context)
        task.goal = enhanced_goal
        return super().execute_task(task)
    
    def _enhance_document_goal(self, goal: str, context: Dict) -> str:
        """Enhance goal with document creation methodology"""
        # Extract research data from context
        research_data = ""
        if context:
            for dep_id, dep_result in context.items():
                if dep_result and isinstance(dep_result, dict) and dep_result.get("data"):
                    research_data += f"\n\n--- SOURCE: {dep_id} ---\n{dep_result['data'][:5000]}"
        
        doc_type = self._detect_document_type(goal)
        template = self._document_templates.get(doc_type, "professional document")
        
        return f"""
DOCUMENT CREATION TASK: {goal}

DOCUMENT TYPE: {doc_type}
TEMPLATE STYLE: {template}

SOURCE RESEARCH DATA:
{research_data if research_data else "No prior research data - create from knowledge"}

REQUIREMENTS:
1. Create a professional, well-structured {doc_type}
2. Use research data as primary source (cite inline)
3. Include: Title, Executive Summary, Table of Contents, Body, Conclusion, References
4. Format appropriately for {doc_type}
5. Save using file_controller with proper path and format
6. Ensure content is accurate, well-organized, and professional

OUTPUT: File saved to disk, path returned
"""
    
    def _detect_document_type(self, goal: str) -> str:
        goal_lower = goal.lower()
        if any(t in goal_lower for t in ["ppt", "powerpoint", "presentation", "slides", "slide deck"]):
            return "presentation"
        elif any(t in goal_lower for t in ["pdf", "report", "whitepaper", "document"]):
            return "report"
        elif any(t in goal_lower for t in ["excel", "spreadsheet", "xlsx", "csv", "data table"]):
            return "spreadsheet"
        elif any(t in goal_lower for t in ["letter", "memo", "memorandum"]):
            return "letter"
        elif "proposal" in goal_lower:
            return "proposal"
        elif "article" in goal_lower or "blog" in goal_lower:
            return "article"
        return "report"
    
    def _execute_plan(self, plan: dict, task: AgentTask) -> str:
        """Execute document creation plan"""
        steps = plan.get("steps", [])
        if not steps:
            return "No valid document plan created"
        
        completed_steps = []
        step_results = {}
        doc_type = self._detect_document_type(task.goal)
        
        for step in steps:
            if task.cancel_flag.is_set():
                return "Document creation cancelled"
            
            step_num = step.get("step", "?")
            tool = step.get("tool", "")
            desc = step.get("description", "")
            params = step.get("parameters", {})
            
            from agent.executor import _inject_context
            params = _inject_context(params, tool, step_results, goal=task.goal)
            
            self._notify_progress(AgentStatus.RUNNING, f"Creating {doc_type}: {desc[:60]}")
            
            print(f"\n[{self.name}] 📄 Doc Step {step_num}: [{tool}] {desc}")
            
            attempt = 1
            step_ok = False
            
            while attempt <= 3:
                if task.cancel_flag.is_set():
                    return "Document creation cancelled"
                
                try:
                    from agent.executor import _call_tool
                    result = _call_tool(tool, params, None)
                    step_results[step_num] = result
                    completed_steps.append(step)
                    print(f"[{self.name}] ✅ Doc Step {step_num} done")
                    step_ok = True
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"[{self.name}] ❌ Doc Step {step_num} attempt {attempt} failed: {error_msg}")
                    
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
                        return f"Document creation aborted: {recovery.get('reason', '')}"
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
                        
                        return f"Document step failed: {error_msg}"
            
            if not step_ok:
                return f"Document step {step_num} failed after retries"
        
        # Extract file path from results
        file_path = self._extract_file_path(step_results)
        if file_path:
            return f"Document created successfully: {file_path}\n\n{self._summarize(task.goal, completed_steps)}"
        return self._summarize(task.goal, completed_steps)
    
    def _extract_file_path(self, step_results: dict) -> Optional[str]:
        """Extract file path from step results"""
        for result in step_results.values():
            if isinstance(result, str):
                # Look for file paths in result
                import re
                paths = re.findall(r'(/[^\s]+\.(?:pdf|docx|pptx|xlsx|txt|md))', result)
                if paths:
                    return paths[-1]  # Return last found path
                # Also check for "saved to" patterns
                saved = re.findall(r'saved to[:\s]+([^\s\n]+)', result, re.IGNORECASE)
                if saved:
                    return saved[-1]
        return None
    
    def _summarize(self, goal: str, completed_steps: list) -> str:
        """Summarize document creation"""
        doc_type = self._detect_document_type(goal)
        return f"Created {doc_type} with {len(completed_steps)} steps for: {goal[:60]}"



# Factory function
def create_document_agent(name: str = "DocumentAgent") -> DocumentAgent:
    """Create a document agent"""
    return DocumentAgent(name)
