
import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from agno.media import File as AgnoFile
from agno.run.team import TeamRunOutput
from agno.session.team import TeamSession
from agno.team.team import Team
from redis.asyncio import Redis

from app.config.setting import settings
from app.api.v1.module_system.dept.service import DeptService
from app.common.enums import RedisInitKeyConfig
from app.common.request import PaginationService
from app.core.base_schema import AuthSchema
from app.core.exceptions import CustomException
from app.core.logger import logger
from app.core.redis_crud import RedisCURD

from .crud import ChatSessionCRUD
from .schema import (
    AiModelConfigSchema,
    ChatQuerySchema,
    ChatSessionCreateSchema,
    ChatSessionQueryParam,
    ChatSessionUpdateSchema,
)
from .utils import AgnoFactory


async def _format_session_data(session: TeamSession, auth: AuthSchema | None = None) -> dict[str, Any]:
    """格式化会话数据，添加前端需要的字段"""
    if hasattr(session, "to_dict"):
        session_dict = session.to_dict()
    else:
        session_dict = {
            "session_id": getattr(session, "session_id", ""),
            "agent_id": getattr(session, "agent_id", None),
            "team_id": getattr(session, "team_id", None),
            "workflow_id": getattr(session, "workflow_id", None),
            "user_id": getattr(session, "user_id", None),
            "session_data": getattr(session, "session_data", None),
            "agent_data": getattr(session, "agent_data", None),
            "team_data": getattr(session, "team_data", None),
            "workflow_data": getattr(session, "workflow_data", None),
            "metadata": getattr(session, "metadata", None),
            "runs": getattr(session, "runs", []),
            "summary": getattr(session, "summary", None),
            "created_at": getattr(session, "created_at", None),
            "updated_at": getattr(session, "updated_at", None),
        }

    session_data = session_dict.get("session_data") or {}
    runs = session_dict.get("runs") or []
    messages = _extract_messages(runs)

    # 从 session_data 中获取 session_name 作为标题
    session_name = session_data.get("session_name") if session_data else None

    result = {
        **session_dict,
        "id": session_dict.get("session_id"),
        "title": session_name or session_dict.get("session_id", "")[:8] or "未命名会话",
        "created_time": _unix_to_datetime(session_dict.get("created_at")),
        "updated_time": _unix_to_datetime(session_dict.get("updated_at")),
        "message_count": len(messages),
        "messages": messages,
    }

    # 如果有 auth，查询部门名称
    if auth and session_dict.get("team_id"):
        try:
            team_id = session_dict.get("team_id")
            if isinstance(team_id, str):
                dept_name = await DeptService(auth).detail(id=int(team_id))
                result["team_name"] = dept_name.get("name")
            elif isinstance(team_id, int):
                dept_name = await DeptService(auth).detail(id=team_id)
                result["team_name"] = dept_name.get("name")
            else:
                result["team_name"] = None
        except Exception:
            result["team_name"] = None
    else:
        result["team_name"] = None

    # 如果 summary 是 SessionSummary 对象，提取 summary 字段
    summary = session_dict.get("summary")
    if summary:
        if isinstance(summary, dict):
            result["summary"] = summary.get("summary")
        else:
            result["summary"] = str(summary)

    return result


def _unix_to_datetime(timestamp: int | None) -> str | None:
    """将Unix时间戳转换为日期时间字符串"""
    if timestamp is None:
        return None
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OSError):
        return None


def _extract_messages(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """从 runs 中提取消息"""
    messages: list[dict[str, Any]] = []
    if not runs:
        return messages

    for run in runs:
        messages.extend(_extract_messages_from_run(run))

    return messages


def _extract_messages_from_run(run: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(run, dict):
        return []

    messages: list[dict[str, Any]] = []

    run_messages = run.get("messages", [])
    if isinstance(run_messages, list):
        for msg in run_messages:
            parsed_message = _normalize_run_message(msg)
            if parsed_message:
                messages.append(parsed_message)

    member_responses = run.get("member_responses", [])
    if isinstance(member_responses, list):
        for member_run in member_responses:
            messages.extend(_extract_messages_from_run(member_run))

    # 某些 Team 运行记录不会把最终对话落在顶层 messages，兜底从 input/content 恢复
    if messages:
        return messages

    input_payload = run.get("input")
    if isinstance(input_payload, dict):
        input_content = _normalize_message_content(input_payload.get("input_content"))
        if input_content:
            messages.append(
                {
                    "id": f'{run.get("run_id", "run")}:input',
                    "role": "user",
                    "content": input_content,
                    "created_at": run.get("created_at"),
                }
            )

    output_content = _normalize_message_content(run.get("content"))
    if output_content:
        messages.append(
            {
                "id": f'{run.get("run_id", "run")}:output',
                "role": "assistant",
                "content": output_content,
                "created_at": run.get("created_at"),
            }
        )

    return messages


def _normalize_run_message(msg: Any) -> dict[str, Any] | None:
    if not isinstance(msg, dict):
        return None

    role = msg.get("role")
    if role == "model":
        role = "assistant"

    if role not in ("user", "assistant"):
        return None

    content = _normalize_message_content(msg.get("content"))
    if not content:
        return None

    return {
        "id": msg.get("id"),
        "role": role,
        "content": content,
        "created_at": msg.get("created_at"),
    }


def _normalize_message_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, (dict, list)):
        try:
            return json.dumps(content, ensure_ascii=False)
        except TypeError:
            return str(content)
    return str(content)


class ChatService:
    """聊天会话管理模块服务层"""

    def __init__(self, auth: AuthSchema) -> None:
        self.auth = auth

    def _resolve_chat_files(self, files: list[dict[str, Any]] | None) -> tuple[list[AgnoFile], str]:
        if not files:
            return [], ""

        agno_files: list[AgnoFile] = []
        file_context_blocks: list[str] = []
        upload_root = settings.UPLOAD_FILE_PATH.resolve()

        for index, file_info in enumerate(files, start=1):
            if not isinstance(file_info, dict):
                continue

            file_path = file_info.get("file_path")
            if not file_path:
                continue

            path_obj = Path(file_path).expanduser()
            try:
                resolved_path = path_obj.resolve(strict=True)
            except FileNotFoundError:
                logger.warning("聊天附件不存在，跳过: {}", file_path)
                continue
            except Exception:
                logger.warning("聊天附件路径解析失败，跳过: {}", file_path)
                continue

            if not str(resolved_path).startswith(str(upload_root)):
                logger.warning("聊天附件路径非法，跳过: {}", resolved_path)
                continue

            mime_type = (file_info.get("type") or "").strip() or None
            filename = file_info.get("name") or resolved_path.name
            suffix = resolved_path.suffix.lower()

            agno_files.append(
                AgnoFile(
                    filepath=str(resolved_path),
                    mime_type=mime_type,
                    filename=filename,
                    name=filename,
                    size=file_info.get("size"),
                    format=suffix.lstrip(".") or None,
                )
            )

            extracted_text = self._extract_text_from_file(resolved_path, suffix)
            if extracted_text:
                file_context_blocks.append(
                    f"[附件{index}: {filename}]\n{extracted_text[:12000]}"
                )

        if not file_context_blocks:
            return agno_files, ""

        file_context = "\n\n".join(file_context_blocks)
        return agno_files, (
            "以下是用户本次上传的附件内容，请优先结合附件回答；如果附件内容不完整，要明确说明：\n\n"
            f"{file_context}"
        )

    @staticmethod
    def _extract_text_from_file(filepath: Path, suffix: str) -> str:
        try:
            if suffix in {".txt", ".md", ".markdown", ".csv", ".json"}:
                return filepath.read_text(encoding="utf-8", errors="ignore").strip()

            if suffix == ".docx":
                return ChatService._extract_text_from_docx(filepath)
        except Exception as exc:
            logger.warning("附件文本提取失败: path={} error={}", filepath, exc)

        return ""

    @staticmethod
    def _extract_text_from_docx(filepath: Path) -> str:
        with ZipFile(filepath) as archive:
            xml_bytes = archive.read("word/document.xml")
        root = ET.fromstring(xml_bytes)
        namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs: list[str] = []
        for paragraph in root.findall(".//w:p", namespaces):
            texts = [node.text for node in paragraph.findall(".//w:t", namespaces) if node.text]
            if texts:
                paragraphs.append("".join(texts))
        return "\n".join(paragraphs).strip()

    async def chat_query(
        self,
        query: ChatQuerySchema,
        stop_event: asyncio.Event | None = None,
        model_config: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """流式 AI 对话"""
        try:
            crud = ChatSessionCRUD(self.auth)

            session_id = query.session_id
            if not session_id:
                import uuid

                session_id = str(uuid.uuid4())
                session: TeamSession | None = await crud.create_crud(data=ChatSessionCreateSchema(title="新对话"))
                if not session:
                    raise CustomException(msg="创建会话失败")
                session_id = session.session_id

            agno_factory = AgnoFactory()
            dept_id = str(self.auth.user.dept_id) if self.auth and self.auth.user and hasattr(self.auth.user, "dept_id") and self.auth.user.dept_id else "default"
            agent = agno_factory.create_agent(
                user_id=self.auth.user.username if self.auth and self.auth.user else "user",
                dept_id=dept_id,
                session_id=session_id,
                db=crud.db,
                model_config=model_config,
            )

            agno_files, file_context = self._resolve_chat_files(query.files)
            message = (query.message or "").strip()
            if file_context:
                message = f"{file_context}\n\n用户问题：{message or '请阅读并总结附件内容'}"

            if not message:
                yield "请输入消息内容"
                return

            logger.info("开始流式生成: session_id={} message={!r}", session_id, message[:80])
            chunk_count = 0
            try:
                if agno_files:
                    logger.info(
                        "当前模型使用文本注入附件内容，跳过原始文件直传: session_id={} file_count={}",
                        session_id,
                        len(agno_files),
                    )
                stream = agent.arun(input=message, stream=True)
                logger.info("agent.arun 返回对象类型: {}", type(stream).__name__)
                if hasattr(stream, "__aiter__"):
                    async for chunk in stream:
                        if stop_event is not None and stop_event.is_set():
                            logger.info("用户主动停止生成: session_id={}", session_id)
                            return
                        if chunk and getattr(chunk, "content", None):
                            chunk_count += 1
                            yield chunk.content
                        else:
                            logger.debug("空 chunk 跳过: {}", type(chunk).__name__ if chunk else None)
                else:
                    # 兼容非流式直接返回结果的场景
                    logger.warning("agent.arun 未返回异步迭代器，尝试按单次结果处理")
                    if stream and getattr(stream, "content", None):
                        chunk_count += 1
                        yield stream.content
            except asyncio.CancelledError:
                logger.info("生成任务被取消: session_id={}", session_id)
                return

            logger.info("流式生成结束: session_id={} chunk_count={}", session_id, chunk_count)

        except Exception as e:
            logger.error(f"聊天查询失败: {e}", exc_info=True)
            yield f"抱歉，处理您的请求时出现错误：{str(e)}"

    async def chat_non_stream(
        self,
        message: str,
        session_id: str | None,
        model_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """非流式 AI 对话"""
        try:
            crud = ChatSessionCRUD(self.auth)

            if not session_id:
                import uuid

                session_id = str(uuid.uuid4())
                session: TeamSession | None = await crud.create_crud(data=ChatSessionCreateSchema(title="新对话"))
                if not session:
                    raise CustomException(msg="创建会话失败")
                session_id = session.session_id

            agno_factory = AgnoFactory()
            dept_id = str(self.auth.user.dept_id) if self.auth and self.auth.user and hasattr(self.auth.user, "dept_id") and self.auth.user.dept_id else "default"
            agent: Team = agno_factory.create_agent(
                user_id=self.auth.user.username if self.auth and self.auth.user else "user",
                dept_id=dept_id,
                session_id=session_id,
                db=crud.db,
                model_config=model_config,
            )

            response: TeamRunOutput = await agent.arun(input=message)

            response_text = ""
            action = None

            if response and response.content:
                response_text = response.content
                try:
                    if response_text.strip().startswith("{") and response_text.strip().endswith("}"):
                        action = json.loads(response_text)
                    elif "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        if json_end > json_start:
                            json_str = response_text[json_start:json_end].strip()
                            action = json.loads(json_str)
                except (json.JSONDecodeError, Exception):
                    pass

                if not action:
                    action = self._parse_action_from_response(response_text)

            return {
                "response": response_text,
                "session_id": session_id,
                "function_calls": None,
                "action": action,
            }

        except Exception as e:
            logger.error(f"聊天查询失败: {e}")
            return {
                "response": f"抱歉，处理您的请求时出现错误：{str(e)}",
                "session_id": session_id,
                "function_calls": None,
                "action": None,
            }

    @staticmethod
    def _parse_action_from_response(response_text: str) -> dict[str, Any] | None:
        """从响应文本中解析操作建议"""

        route_config = {
            "用户管理": {"path": "/system/user", "name": "用户管理"},
            "角色管理": {"path": "/system/role", "name": "角色管理"},
            "菜单管理": {"path": "/system/menu", "name": "菜单管理"},
            "部门管理": {"path": "/system/dept", "name": "部门管理"},
            "字典管理": {"path": "/system/dict", "name": "字典管理"},
            "系统日志": {"path": "/system/log", "name": "系统日志"},
        }

        navigation_keywords = ["跳转", "打开", "进入", "前往", "去", "浏览", "查看"]
        has_navigation = any(keyword in response_text for keyword in navigation_keywords)

        if not has_navigation:
            return None

        for page_name, route_info in route_config.items():
            if page_name in response_text:
                return {
                    "type": "navigate",
                    "path": route_info["path"],
                    "name": route_info["name"],
                }

        keyword_mapping = {
            "用户": {"path": "/system/user", "name": "用户管理"},
            "角色": {"path": "/system/role", "name": "角色管理"},
            "菜单": {"path": "/system/menu", "name": "菜单管理"},
            "部门": {"path": "/system/dept", "name": "部门管理"},
            "字典": {"path": "/system/dict", "name": "字典管理"},
            "日志": {"path": "/system/log", "name": "系统日志"},
        }

        for keyword, route_info in keyword_mapping.items():
            if keyword in response_text:
                return {
                    "type": "navigate",
                    "path": route_info["path"],
                    "name": route_info["name"],
                }

        return None

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        crud = ChatSessionCRUD(self.auth)
        session: TeamSession | None = await crud.get_by_id_crud(session_id=session_id)
        if session:
            return await _format_session_data(session, self.auth)
        return None

    async def create(self, data: ChatSessionCreateSchema) -> dict[str, Any] | None:
        crud = ChatSessionCRUD(self.auth)
        session = await crud.create_crud(data=data)
        if session:
            return await _format_session_data(session, self.auth)
        return None

    async def page(
        self,
        page_no: int,
        page_size: int,
        search: ChatSessionQueryParam,
        order_by: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        crud = ChatSessionCRUD(self.auth)
        sessions = await crud.list_crud()
        items = [await _format_session_data(s, self.auth) for s in sessions]
        return await PaginationService.paginate(
            data_list=items,
            page_no=page_no,
            page_size=page_size,
        )

    async def update(self, session_id: str, data: ChatSessionUpdateSchema) -> bool:
        crud = ChatSessionCRUD(self.auth)
        return await crud.update_crud(session_id=session_id, data=data)

    async def delete(self, session_ids: list[str]) -> None:
        await ChatSessionCRUD(self.auth).delete_crud(session_ids=session_ids)


# ================================================= #
# ******************* AI 模型配置 ****************** #
# ================================================= #


def _normalize_tenant_id(tenant_id: int | None) -> int:
    return tenant_id or 1


def _shared_ai_model_items_key(tenant_id: int) -> str:
    return f"{RedisInitKeyConfig.AI_MODEL_CONFIG.key}:shared:items:{tenant_id}"


def _shared_ai_model_active_key(tenant_id: int) -> str:
    return f"{RedisInitKeyConfig.AI_MODEL_CONFIG.key}:shared:active:{tenant_id}"


def _user_ai_model_active_key(tenant_id: int, user_id: int) -> str:
    return f"{RedisInitKeyConfig.AI_MODEL_CONFIG.key}:user:active:{tenant_id}:{user_id}"


def _legacy_ai_model_items_key(user_id: int) -> str:
    return f"{RedisInitKeyConfig.AI_MODEL_CONFIG.key}:items:{user_id}"


def _legacy_ai_model_active_key(user_id: int) -> str:
    return f"{RedisInitKeyConfig.AI_MODEL_CONFIG.key}:active:{user_id}"


def _can_manage_shared_ai_models(user: Any) -> bool:
    if not user:
        return False
    if getattr(user, "is_superuser", False):
        return True
    if getattr(user, "id", None) == 1:
        return True

    username = (getattr(user, "username", "") or "").strip().upper()
    display_name = (getattr(user, "name", "") or "").strip()
    nickname = (getattr(user, "nickname", "") or "").strip()

    if username in {"ADMIN", "SUPER_ADMIN", "SUPERADMIN", "ROOT"}:
        return True
    if "管理员" in display_name or "管理员" in nickname:
        return True

    for role in getattr(user, "roles", []) or []:
        if getattr(role, "status", 1) != 0:
            continue

        code = (getattr(role, "code", "") or "").strip().upper()
        name = (getattr(role, "name", "") or "").strip()
        if code in {"ADMIN", "SUPER_ADMIN"} or code.endswith("_ADMIN") or "管理员" in name:
            return True

    return False


async def list_shared_model_configs(redis: Redis, tenant_id: int) -> list[dict[str, Any]]:
    """列出租户共享的模型配置项。"""
    raw = await RedisCURD(redis).get(_shared_ai_model_items_key(_normalize_tenant_id(tenant_id)))
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, TypeError):
        logger.warning("AI 共享模型配置列表 JSON 解析失败: tenant_id={}", tenant_id)
        return []


async def get_shared_active_model_id(redis: Redis, tenant_id: int) -> str | None:
    tenant_id = _normalize_tenant_id(tenant_id)
    active_id = await RedisCURD(redis).get(_shared_ai_model_active_key(tenant_id))
    if not active_id:
        items = await list_shared_model_configs(redis, tenant_id)
        first_id = next((item.get("id") for item in items if item.get("id")), None)
        return first_id if isinstance(first_id, str) else None

    items = await list_shared_model_configs(redis, tenant_id)
    if any(item.get("id") == active_id for item in items):
        return active_id
    return next((item.get("id") for item in items if item.get("id")), None)


async def _get_user_active_override_id(redis: Redis, tenant_id: int, user_id: int) -> str | None:
    override_id = await RedisCURD(redis).get(_user_ai_model_active_key(_normalize_tenant_id(tenant_id), user_id))
    if not override_id:
        return None

    items = await list_shared_model_configs(redis, tenant_id)
    return override_id if any(item.get("id") == override_id for item in items) else None


async def get_effective_active_model_id(redis: Redis, tenant_id: int, user_id: int) -> str | None:
    override_id = await _get_user_active_override_id(redis, tenant_id, user_id)
    if override_id:
        return override_id
    return await get_shared_active_model_id(redis, tenant_id)


async def get_user_model_config(redis: Redis, tenant_id: int, user_id: int) -> dict[str, Any] | None:
    """读取当前用户实际生效的 AI 模型配置（用户选择优先，否则回落共享默认）。"""
    active_id = await get_effective_active_model_id(redis, tenant_id, user_id)
    if not active_id:
        return None

    items = await list_shared_model_configs(redis, tenant_id)
    for item in items:
        if item.get("id") == active_id:
            return item
    return None


async def migrate_legacy_user_model_configs(redis: Redis, tenant_id: int, user_id: int) -> bool:
    """将旧版“按用户存储”的模型配置迁移为当前租户共享配置。"""
    tenant_id = _normalize_tenant_id(tenant_id)
    if await list_shared_model_configs(redis, tenant_id):
        return False

    raw = await RedisCURD(redis).get(_legacy_ai_model_items_key(user_id))
    if not raw:
        return False

    try:
        items = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning("旧版 AI 模型配置迁移失败，JSON 解析异常: user_id={}", user_id)
        return False

    if not isinstance(items, list) or not items:
        return False

    await RedisCURD(redis).set(
        _shared_ai_model_items_key(tenant_id),
        json.dumps(items, ensure_ascii=False),
    )

    legacy_active_id = await RedisCURD(redis).get(_legacy_ai_model_active_key(user_id))
    if legacy_active_id and any(item.get("id") == legacy_active_id for item in items):
        await RedisCURD(redis).set(_shared_ai_model_active_key(tenant_id), legacy_active_id)
    else:
        first_id = next((item.get("id") for item in items if item.get("id")), None)
        if first_id:
            await RedisCURD(redis).set(_shared_ai_model_active_key(tenant_id), first_id)

    logger.info("已迁移旧版 AI 模型配置到共享空间: tenant_id={} user_id={}", tenant_id, user_id)
    return True


async def create_shared_model_config(
    redis: Redis,
    tenant_id: int,
    config: AiModelConfigSchema,
) -> dict[str, Any]:
    """新增一个共享模型配置项。"""
    import uuid
    from datetime import datetime

    tenant_id = _normalize_tenant_id(tenant_id)
    items = await list_shared_model_configs(redis, tenant_id)
    item = {
        **config.model_dump(),
        "id": uuid.uuid4().hex,
        "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    items.append(item)
    await RedisCURD(redis).set(
        _shared_ai_model_items_key(tenant_id),
        json.dumps(items, ensure_ascii=False),
    )

    # 若尚未设置共享默认模型，则自动激活新增项
    if not await get_shared_active_model_id(redis, tenant_id):
        await RedisCURD(redis).set(_shared_ai_model_active_key(tenant_id), item["id"])

    logger.info("已新增共享 AI 模型配置: tenant_id={} name={} id={}", tenant_id, config.name, item["id"])
    return item


async def update_shared_model_config(
    redis: Redis,
    tenant_id: int,
    config_id: str,
    config: AiModelConfigSchema,
) -> dict[str, Any] | None:
    """更新指定 ID 的共享模型配置项；不存在返回 None。"""
    tenant_id = _normalize_tenant_id(tenant_id)
    items = await list_shared_model_configs(redis, tenant_id)
    target = next((it for it in items if it.get("id") == config_id), None)
    if not target:
        return None
    target.update(config.model_dump())
    await RedisCURD(redis).set(
        _shared_ai_model_items_key(tenant_id),
        json.dumps(items, ensure_ascii=False),
    )
    logger.info("已更新共享 AI 模型配置: tenant_id={} id={}", tenant_id, config_id)
    return target


async def delete_shared_model_config(redis: Redis, tenant_id: int, config_id: str) -> bool:
    """删除指定 ID 的共享模型配置项；若该 ID 是共享默认则回退到剩余第一项。"""
    tenant_id = _normalize_tenant_id(tenant_id)
    items = await list_shared_model_configs(redis, tenant_id)
    new_items = [it for it in items if it.get("id") != config_id]
    if len(new_items) == len(items):
        return False
    await RedisCURD(redis).set(
        _shared_ai_model_items_key(tenant_id),
        json.dumps(new_items, ensure_ascii=False),
    )
    shared_active_id = await RedisCURD(redis).get(_shared_ai_model_active_key(tenant_id))
    if shared_active_id == config_id:
        next_active_id = next((item.get("id") for item in new_items if item.get("id")), None)
        if next_active_id:
            await RedisCURD(redis).set(_shared_ai_model_active_key(tenant_id), next_active_id)
        else:
            await RedisCURD(redis).delete(_shared_ai_model_active_key(tenant_id))
    logger.info("已删除共享 AI 模型配置: tenant_id={} id={}", tenant_id, config_id)
    return True


async def set_shared_active_model_config(redis: Redis, tenant_id: int, config_id: str) -> bool:
    """设置共享默认模型；id 为空字符串或 "__default__" 表示使用环境默认模型。"""
    tenant_id = _normalize_tenant_id(tenant_id)
    if config_id in ("", "__default__"):
        await RedisCURD(redis).delete(_shared_ai_model_active_key(tenant_id))
        logger.info("已切换到环境默认模型: tenant_id={}", tenant_id)
        return True

    items = await list_shared_model_configs(redis, tenant_id)
    if not any(it.get("id") == config_id for it in items):
        return False
    await RedisCURD(redis).set(_shared_ai_model_active_key(tenant_id), config_id)
    logger.info("已切换共享 AI 模型: tenant_id={} id={}", tenant_id, config_id)
    return True


async def set_user_active_model_config(redis: Redis, tenant_id: int, user_id: int, config_id: str) -> bool:
    """设置用户当前生效模型；空值表示回退到共享默认模型。"""
    tenant_id = _normalize_tenant_id(tenant_id)
    if config_id in ("", "__default__"):
        await RedisCURD(redis).delete(_user_ai_model_active_key(tenant_id, user_id))
        logger.info("已回退到共享默认模型: tenant_id={} user_id={}", tenant_id, user_id)
        return True

    items = await list_shared_model_configs(redis, tenant_id)
    if not any(it.get("id") == config_id for it in items):
        return False

    await RedisCURD(redis).set(_user_ai_model_active_key(tenant_id, user_id), config_id)
    logger.info("已设置用户生效 AI 模型: tenant_id={} user_id={} id={}", tenant_id, user_id, config_id)
    return True


class AiModelConfigService:
    """AI 模型配置业务服务（共享配置 + 用户切换）"""

    def __init__(self, auth: AuthSchema, redis: Redis) -> None:
        self.auth = auth
        self.redis = redis

    @property
    def _user_id(self) -> int:
        if not self.auth or not self.auth.user:
            raise CustomException(msg="未登录", code=10401, status_code=401)
        return self.auth.user.id

    @property
    def _tenant_id(self) -> int:
        if self.auth.tenant_id:
            return self.auth.tenant_id
        if self.auth.user and getattr(self.auth.user, "tenant_id", None):
            return self.auth.user.tenant_id
        return 1

    @property
    def _can_manage(self) -> bool:
        return _can_manage_shared_ai_models(self.auth.user)

    def _ensure_manage_permission(self) -> None:
        if not self._can_manage:
            raise CustomException(msg="仅管理员可维护模型配置", code=10403, status_code=403)

    async def list(self) -> dict[str, Any]:
        """获取共享配置列表 + 当前用户生效模型 ID。"""
        if self._can_manage:
            await migrate_legacy_user_model_configs(self.redis, self._tenant_id, self._user_id)

        items = await list_shared_model_configs(self.redis, self._tenant_id)
        active_id = (
            await get_shared_active_model_id(self.redis, self._tenant_id)
            if self._can_manage
            else await get_effective_active_model_id(self.redis, self._tenant_id, self._user_id)
        )

        response_items = items
        if not self._can_manage:
            response_items = [{**item, "api_key": "********"} for item in items]

        return {
            "items": response_items,
            "active_id": active_id,
            "can_manage": self._can_manage,
        }

    async def get_active(self) -> dict[str, Any] | None:
        return await get_user_model_config(self.redis, self._tenant_id, self._user_id)

    async def create(self, config: AiModelConfigSchema) -> dict[str, Any]:
        self._ensure_manage_permission()
        return await create_shared_model_config(self.redis, self._tenant_id, config)

    async def update(self, config_id: str, config: AiModelConfigSchema) -> dict[str, Any] | None:
        self._ensure_manage_permission()
        result = await update_shared_model_config(self.redis, self._tenant_id, config_id, config)
        if result is None:
            raise CustomException(msg="模型配置不存在", code=10404, status_code=404)
        return result

    async def delete(self, config_id: str) -> None:
        self._ensure_manage_permission()
        ok = await delete_shared_model_config(self.redis, self._tenant_id, config_id)
        if not ok:
            raise CustomException(msg="模型配置不存在", code=10404, status_code=404)

    async def set_active(self, config_id: str) -> None:
        ok = (
            await set_shared_active_model_config(self.redis, self._tenant_id, config_id)
            if self._can_manage
            else await set_user_active_model_config(self.redis, self._tenant_id, self._user_id, config_id)
        )
        if not ok:
            raise CustomException(msg="模型配置不存在", code=10404, status_code=404)
