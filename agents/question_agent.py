"""
培训问题生成智能体
基于文档内容生成多维度的培训问题
"""
import json
from agents.base_agent import BaseAgent
from document_store import DocumentStore
import config


class QuestionAgent(BaseAgent):
    """问题生成智能体 - 根据产品资料生成培训题"""

    def __init__(self, doc_store: DocumentStore):
        super().__init__(
            name="培训出题专家",
            system_prompt=config.QUESTION_AGENT_PROMPT,
        )
        self.doc_store = doc_store

    def get_description(self) -> str:
        return "根据上传的产品资料自动生成多维度培训问题，供医药代表练习和考核。"

    def generate_questions(
        self,
        num_questions: int = 5,
        difficulty: str = "混合",
        focus_area: str = "综合",
    ) -> str:
        """生成培训问题

        Args:
            num_questions: 生成问题数量
            difficulty: 难度级别（基础/进阶/高级/混合）
            focus_area: 重点领域（产品知识/竞品分析/临床场景/销售技巧/合规/综合）
        """
        num_questions = min(num_questions, config.MAX_QUESTIONS_PER_BATCH)
        context = self.doc_store.get_combined_context(max_chars=6000)

        if not context.strip():
            return "⚠️ 尚未上传任何文档，请先上传产品手册或销售策略文件。"

        prompt = f"""基于以下产品资料，请生成 {num_questions} 道培训问题。

要求：
- 难度级别：{difficulty}
- 重点领域：{focus_area}

产品资料：
{context}

请按以下 JSON 格式输出（用 ```json 包裹）：
```json
[
  {{
    "id": 1,
    "question": "问题内容",
    "difficulty": "基础/进阶/高级",
    "dimension": "能力维度（产品知识/竞品分析/临床场景/销售技巧/合规）",
    "reference_answer": "参考答案要点（详细）",
    "key_points": ["要点1", "要点2", "要点3"]
  }}
]
```

确保问题具有实际培训价值，参考答案准确且有据可查。"""

        return self.chat(prompt, temperature=0.7)

    def generate_scenario_questions(self, scenario: str) -> str:
        """根据指定场景生成情景化问题"""
        context = self.doc_store.get_combined_context(max_chars=6000)

        if not context.strip():
            return "⚠️ 尚未上传任何文档，请先上传产品手册或销售策略文件。"

        prompt = f"""基于以下产品资料，针对「{scenario}」这一场景，
生成 3-5 个情景化培训问题。

产品资料：
{context}

每个问题应模拟真实工作场景，例如：
- 科室主任在门诊间隙的快速提问
- 学术会议后的深入讨论
- 面对竞品挑战时的应对

请为每个问题提供：
1. 场景描述（模拟真实情境）
2. 核心问题
3. 推荐回答策略
4. 应避免的回答方式"""

        return self.chat(prompt, temperature=0.7)

    def parse_questions_json(self, raw_output: str) -> list[dict]:
        """尝试从 LLM 输出中解析问题 JSON"""
        try:
            start = raw_output.index("[")
            end = raw_output.rindex("]") + 1
            return json.loads(raw_output[start:end])
        except (ValueError, json.JSONDecodeError):
            return []
