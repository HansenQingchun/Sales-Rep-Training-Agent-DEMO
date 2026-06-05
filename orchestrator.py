"""
多智能体编排器
协调各智能体完成医药代表培训的完整流程
"""
from document_store import DocumentStore
from agents.document_agent import DocumentAgent
from agents.question_agent import QuestionAgent
from agents.roleplay_agent import RolePlayAgent
from agents.evaluation_agent import EvaluationAgent


class Orchestrator:
    """多智能体编排器 - 管理所有智能体的生命周期和协作"""

    def __init__(self):
        self.doc_store = DocumentStore()
        self.document_agent = DocumentAgent(self.doc_store)
        self.question_agent = QuestionAgent(self.doc_store)
        self.roleplay_agent = RolePlayAgent(self.doc_store)
        self.evaluation_agent = EvaluationAgent(self.doc_store)

    # ==========================================================
    # 文档管理
    # ==========================================================

    def upload_document(self, file_path: str, file_name: str) -> str:
        """上传并分析文档"""
        return self.document_agent.analyze_document(file_path, file_name)

    def ask_about_documents(self, question: str) -> str:
        """基于文档问答"""
        return self.document_agent.answer_about_documents(question)

    def get_uploaded_documents(self) -> list[dict]:
        """获取已上传文档列表"""
        return self.doc_store.get_all_documents()

    # ==========================================================
    # 培训问题生成
    # ==========================================================

    def generate_questions(
        self,
        num_questions: int = 5,
        difficulty: str = "混合",
        focus_area: str = "综合",
    ) -> str:
        """生成培训问题"""
        self.question_agent.reset()
        return self.question_agent.generate_questions(
            num_questions, difficulty, focus_area
        )

    def generate_scenario_questions(self, scenario: str) -> str:
        """生成场景化题目"""
        self.question_agent.reset()
        return self.question_agent.generate_scenario_questions(scenario)

    # ==========================================================
    # 角色扮演
    # ==========================================================

    def start_roleplay(
        self, preset_name: str, custom_config: dict | None = None
    ) -> str:
        """开始角色扮演会话"""
        return self.roleplay_agent.start_session(preset_name, custom_config)

    def roleplay_respond(self, message: str) -> str:
        """角色扮演中代表发言"""
        return self.roleplay_agent.respond(message)

    def end_roleplay(self) -> str:
        """结束角色扮演"""
        return self.roleplay_agent.end_session()

    @property
    def roleplay_active(self) -> bool:
        return self.roleplay_agent.session_active

    # ==========================================================
    # 评估打分
    # ==========================================================

    def evaluate_qa(
        self, question: str, answer: str, reference_answer: str = ""
    ) -> str:
        """评估单个问答"""
        return self.evaluation_agent.evaluate_single_qa(
            question, answer, reference_answer
        )

    def evaluate_roleplay(self) -> str:
        """评估角色扮演会话"""
        conversation = self.roleplay_agent.get_conversation_for_evaluation()
        return self.evaluation_agent.evaluate_roleplay_session(conversation)

    def quick_score(self, question: str, answer: str) -> dict:
        """快速评分"""
        return self.evaluation_agent.quick_score(question, answer)

    # ==========================================================
    # 系统管理
    # ==========================================================

    def clear_all(self):
        """清空所有数据和对话"""
        self.doc_store.clear()
        self.document_agent.reset()
        self.question_agent.reset()
        self.roleplay_agent.reset()
        self.roleplay_agent.session_active = False
        self.evaluation_agent.reset()
