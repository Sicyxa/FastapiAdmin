from typing import Any
from urllib.parse import urlparse

from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.team import Team

from app.config.setting import settings
from app.core.logger import logger


class AgnoFactory:
    """Agno 工厂类 - 统一管理 Agent、Team 创建逻辑"""

    # 配置常量
    AGENT_DESCRIPTION = "你是一个有用的AI助手，可以帮助用户回答问题和提供帮助。"
    AGENT_INSTRUCTIONS = ["保持回答简洁明了", "如果不确定，请说明"]
    AGENT_EXPECTED_OUTPUT = "中文回答"
    AGENT_TEMPERATURE = 0.7
    NUM_HISTORY_RUNS = 3
    REQUEST_TIMEOUT = 60.0  # LLM 请求总超时（秒），流式响应需放长
    CONNECT_TIMEOUT = 10.0  # TCP 连接超时（秒）

    @staticmethod
    def _mask_api_key(api_key: str | None) -> str:
        if not api_key:
            return ""
        if len(api_key) <= 8:
            return "*" * len(api_key)
        return f"{api_key[:4]}...{api_key[-4:]}"

    @staticmethod
    def _normalize_base_url(base_url: str | None) -> str | None:
        if not base_url:
            return base_url

        value = base_url.strip().rstrip("/")
        parsed = urlparse(value)
        host = (parsed.netloc or "").lower()
        path = parsed.path.rstrip("/")

        default_path_by_host = {
            "api.openai.com": "/v1",
            "api.deepseek.com": "/v1",
            "api.moonshot.cn": "/v1",
            "dashscope.aliyuncs.com": "/compatible-mode/v1",
            "open.bigmodel.cn": "/api/paas/v4",
            "localhost:11434": "/v1",
            "127.0.0.1:11434": "/v1",
        }

        if path:
            return value

        expected_path = default_path_by_host.get(host)
        if not expected_path:
            return value

        return f"{value}{expected_path}"

    def create_agent(
        self,
        user_id: str,
        dept_id: str,
        session_id: str,
        db: Any | None = None,
        model_config: dict[str, Any] | None = None,
    ) -> Team:
        """
        创建带 Agent 的 Team 实例。

        参数:
        - user_id (str): 用户标识。
        - dept_id (str): 部门/团队标识。
        - session_id (str): 会话 ID。
        - db (Any | None): Agno 持久化数据库实例，可选。
        - model_config (dict | None): 运行时模型配置，覆盖系统默认。
            支持字段：base_url, api_key, model_id, temperature。

        返回:
        - Team: 配置好的 Team。
        """
        # 优先使用运行时配置，否则 fallback 到系统 settings
        base_url = settings.OPENAI_BASE_URL
        api_key = settings.OPENAI_API_KEY
        model_id = settings.OPENAI_MODEL
        temperature = self.AGENT_TEMPERATURE

        if model_config:
            base_url = model_config.get("base_url") or base_url
            api_key = model_config.get("api_key") or api_key
            model_id = model_config.get("model_id") or model_id
            if isinstance(model_config.get("temperature"), (int, float)):
                temperature = float(model_config["temperature"])

        base_url = self._normalize_base_url(base_url)

        logger.info(
            "创建 AI Agent: session_id={} user_id={} model_id={} base_url={} api_key={}",
            session_id,
            user_id,
            model_id,
            base_url,
            self._mask_api_key(api_key),
        )

        # 创建 Agent
        fastapiadmin_agent = Agent(
            id=user_id,
            name="fastapiadmin_agent",
            role="You are a helpful AI assistant",
            description=self.AGENT_DESCRIPTION,
            tools=[],
        )

        # 创建 Team
        fastapiadmin_team = Team(
            id=dept_id,
            user_id=user_id,
            session_id=session_id,
            model=OpenAILike(
                id=model_id,
                api_key=api_key,
                base_url=base_url,
                temperature=temperature,
                timeout=self.REQUEST_TIMEOUT,
            ),
            members=[fastapiadmin_agent],
            instructions=self.AGENT_INSTRUCTIONS,
            expected_output=self.AGENT_EXPECTED_OUTPUT,
            add_datetime_to_context=True,
            add_history_to_context=True,
            markdown=True,
            num_history_runs=self.NUM_HISTORY_RUNS,
            input_schema=None,
            output_schema=None,
            parse_response=True,
            read_chat_history=True,
            db=db,
        )

        return fastapiadmin_team
