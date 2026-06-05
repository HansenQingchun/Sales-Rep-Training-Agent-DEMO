"""
评估打分智能体
对医药代表的问答和角色扮演表现进行专业评估
"""
import json
from agents.base_agent import BaseAgent
from document_store import DocumentStore
import config


class EvaluationAgent(BaseAgent):
    """评估智能体 - 对问答和角色扮演进行评分和反馈"""

    def __init__(self, doc_store: DocumentStore):
        super().__init__(
            name="培训评估专家",
            system_prompt=config.EVALUATION_AGENT_PROMPT.format(
                max_score=config.SCORING_SCALE
            ),
        )
        self.doc_store = doc_store

    def get_description(self) -> str:
        return "对医药代表的培训问答和角色扮演表现进行多维度打分，并提供改进建议和推荐话术。"

    def evaluate_single_qa(
        self, question: str, answer: str, reference_answer: str = ""
    ) -> str:
        """评估单个问答对"""
        context = self.doc_store.get_combined_context(max_chars=4000)

        prompt = f"""请对以下医药代表的回答进行专业评估。

**培训问题：**
{question}

**代表回答：**
{answer}
"""
        if reference_answer:
            prompt += f"""
**参考答案：**
{reference_answer}
"""
        if context:
            prompt += f"""
**产品资料参考：**
{context}
"""

        prompt += f"""
请从以下维度进行评分（每项满分 {config.SCORING_SCALE} 分），并给出详细反馈：

1. **产品知识准确性**
2. **临床证据引用**
3. **沟通技巧**
4. **合规性**
5. **价值传递**

请按以下格式输出：

### 📊 评分详情

| 维度 | 得分 | 评价 |
|------|------|------|
| 产品知识准确性 | X/{config.SCORING_SCALE} | 简要评价 |
| 临床证据引用 | X/{config.SCORING_SCALE} | 简要评价 |
| 沟通技巧 | X/{config.SCORING_SCALE} | 简要评价 |
| 合规性 | X/{config.SCORING_SCALE} | 简要评价 |
| 价值传递 | X/{config.SCORING_SCALE} | 简要评价 |

**总分：XX/{config.SCORING_SCALE * 5}  总体评级：XX**

### ✅ 亮点
（回答中做得好的地方）

### ⚠️ 不足
（需要改进的地方）

### 💡 改进建议
（具体的推荐话术和表达方式）
"""
        self.reset()
        return self.chat(prompt, temperature=0.3)

    def evaluate_roleplay_session(self, conversation: list[dict]) -> str:
        """评估整个角色扮演会话"""
        context = self.doc_store.get_combined_context(max_chars=4000)

        # 格式化对话记录
        dialogue_text = ""
        for msg in conversation:
            role_label = "🧑‍⚕️ 科室主任" if msg["role"] == "assistant" else "👔 医药代表"
            dialogue_text += f"{role_label}：{msg['content']}\n\n"

        if not dialogue_text.strip():
            return "⚠️ 没有可评估的对话记录。"

        prompt = f"""请对以下医药代表拜访科室主任的角色扮演对话进行全面评估。

---
**对话记录：**

{dialogue_text}
---
"""
        if context:
            prompt += f"""
**产品资料参考：**
{context}
---
"""

        prompt += f"""
请进行全面评估，包括：

### 📊 总体评分（每项满分 {config.SCORING_SCALE} 分）

| 维度 | 得分 | 详细评价 |
|------|------|----------|
| 产品知识准确性 | X/{config.SCORING_SCALE} | |
| 临床证据引用 | X/{config.SCORING_SCALE} | |
| 沟通技巧 | X/{config.SCORING_SCALE} | |
| 异议处理能力 | X/{config.SCORING_SCALE} | |
| 合规性 | X/{config.SCORING_SCALE} | |
| 价值传递 | X/{config.SCORING_SCALE} | |

**总分：XX/{config.SCORING_SCALE * 6}  总体评级：XX**

### 🔍 逐轮点评
（对每一轮代表的发言进行简要点评）

### ✅ 亮点表现
（代表做得好的 2-3 个方面）

### ⚠️ 关键改进点
（最需要改进的 2-3 个方面）

### 💡 推荐话术
（针对回答不佳的环节，给出具体的推荐表达方式）

### 📋 培训建议
（基于整体表现，给出后续学习重点建议）
"""
        self.reset()
        return self.chat(prompt, temperature=0.3)

    def quick_score(self, question: str, answer: str) -> dict:
        """快速评分，返回结构化分数（用于批量评估）"""
        context = self.doc_store.get_combined_context(max_chars=3000)
        prompt = f"""对以下问答进行快速评分，仅返回 JSON。

问题：{question}
回答：{answer}

产品资料参考：
{context}

请严格按以下 JSON 格式返回（用 ```json 包裹）：
```json
{{
  "accuracy": {{"score": 0, "max": {config.SCORING_SCALE}}},
  "evidence": {{"score": 0, "max": {config.SCORING_SCALE}}},
  "communication": {{"score": 0, "max": {config.SCORING_SCALE}}},
  "compliance": {{"score": 0, "max": {config.SCORING_SCALE}}},
  "value_delivery": {{"score": 0, "max": {config.SCORING_SCALE}}},
  "total_score": 0,
  "total_max": {config.SCORING_SCALE * 5},
  "grade": "优秀/良好/合格/需改进",
  "brief_feedback": "一句话总结"
}}
```"""
        self.reset()
        raw = self.chat(prompt, temperature=0.2)
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            return json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            return {"error": "评分解析失败", "raw": raw}
