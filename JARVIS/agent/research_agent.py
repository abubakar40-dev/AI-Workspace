# agent/research_agent.py
# Specialized agent for web research and information gathering

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.agent_base import BaseAgent, AgentType, AgentStatus, AgentResult, AgentTask


class ResearchAgent(BaseAgent):
    """Agent specialized in web research, information gathering, and fact-finding"""
    
    def __init__(self, name: str = "ResearchAgent"):
        super().__init__(AgentType.RESEARCH, name)
        self._search_history: List[Dict] = []
    
    def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute research task with specialized planning"""
        # Enhance goal with research-specific instructions
        enhanced_goal = self._enhance_research_goal(task.goal)
        task.goal = enhanced_goal
        
        return super().execute_task(task)
    
    def _enhance_research_goal(self, goal: str) -> str:
        """Enhance goal with research methodology"""
        return f"""
RESEARCH TASK: {goal}

METHODOLOGY:
1. Use web_search tool with focused queries to gather comprehensive information
2. Search for multiple perspectives and recent data
3. Verify facts across multiple sources
4. Organize findings by theme/topic
5. Cite sources with URLs where possible
6. Provide executive summary and detailed findings

OUTPUT FORMAT:
- Executive Summary (2-3 sentences)
- Key Findings (bulleted with sources)
- Detailed Analysis (organized by subtopic)
- Sources Consulted (list of URLs)
- Confidence Assessment (high/medium/low for key claims)
"""
    
    def _execute_plan(self, plan: dict, task: AgentTask) -> str:
        """Execute research plan with enhanced search strategy"""
        steps = plan.get("steps", [])
        if not steps:
            return "No valid research plan created"
        
        completed_steps = []
        step_results = {}
        
        for step in steps:
            if task.cancel_flag.is_set():
                return "Research cancelled"
            
            step_num = step.get("step", "?")
            tool = step.get("tool", "")
            desc = step.get("description", "")
            params = step.get("parameters", {})
            
            # Enhance search parameters for research
            if tool == "web_search":
                params = self._enhance_search_params(params, task.goal)
            
            from agent.executor import _inject_context
            params = _inject_context(params, tool, step_results, goal=task.goal)
            
            self._notify_progress(AgentStatus.RUNNING, f"Researching: {desc[:60]}")
            
            print(f"\n[{self.name}] 🔍 Research Step {step_num}: [{tool}] {desc}")
            
            attempt = 1
            step_ok = False
            
            while attempt <= 3:
                if task.cancel_flag.is_set():
                    return "Research cancelled"
                
                try:
                    from agent.executor import _call_tool
                    result = _call_tool(tool, params, None)
                    
                    # Track search history
                    if tool == "web_search":
                        self._search_history.append({
                            "query": params.get("query", ""),
                            "result_length": len(result),
                            "step": step_num
                        })
                    
                    step_results[step_num] = result
                    completed_steps.append(step)
                    print(f"[{self.name}] ✅ Research Step {step_num} done")
                    step_ok = True
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"[{self.name}] ❌ Research Step {step_num} attempt {attempt} failed: {error_msg}")
                    
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
                        return f"Research aborted: {recovery.get('reason', '')}"
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
                        
                        return f"Research step failed: {error_msg}"
            
            if not step_ok:
                return f"Research step {step_num} failed after retries"
        
        # Create comprehensive research report
        return self._compile_research_report(task.goal, completed_steps, step_results)
    
    def _enhance_search_params(self, params: dict, goal: str) -> dict:
        """Enhance search parameters for better research results"""
        params = dict(params)
        
        # Ensure we use search mode
        if "mode" not in params:
            params["mode"] = "search"
        
        # Add comparison mode for certain queries
        query = params.get("query", "").lower()
        if any(term in query for term in ["compare", "versus", "vs", "difference", "pros and cons"]):
            params["mode"] = "compare"
        
        return params
    
    def _compile_research_report(self, goal: str, completed_steps: list, step_results: dict) -> str:
        """Compile research findings into a structured report"""
        all_content = []
        for step_num, result in step_results.items():
            if result and len(result) > 50:
                step_desc = next((s.get("description", "") for s in completed_steps if s.get("step") == step_num), "")
                all_content.append(f"=== {step_desc} ===\n{result}")
        
        combined = "\n\n".join(all_content)
        
        # Use LLM to structure the research report
        try:
            from google import genai
            from agent.executor import _get_api_key
            client = genai.Client(api_key=_get_api_key(), http_options={"api_version": "v1beta"})
            
            prompt = f"""You are a professional research analyst. Compile the following raw research findings into a comprehensive, well-structured research report.

ORIGINAL GOAL: {goal}

RAW FINDINGS:
{combined[:8000]}

Create a report with these sections:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY FINDINGS (bulleted, with source references)
3. DETAILED ANALYSIS (organized by subtopic)
4. SOURCES CONSULTED (list with URLs)
5. CONFIDENCE ASSESSMENT (high/medium/low for key claims)
6. GAPS & RECOMMENDATIONS (what's missing, what to research next)

Be thorough but concise. Keep factual accuracy paramount."""
            
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            print(f"[{self.name}] ⚠️ Report compilation failed: {e}")
            return f"RESEARCH REPORT FOR: {goal}\n\nRAW FINDINGS:\n{combined}"
    
    def get_search_history(self) -> List[Dict]:
        return self._search_history.copy()



# Factory function
def create_research_agent(name: str = "ResearchAgent") -> ResearchAgent:
    """Create a research agent"""
    return ResearchAgent(name)
