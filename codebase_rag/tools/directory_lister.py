from __future__ import annotations

import os
from pathlib import Path

from loguru import logger
from pydantic_ai import Tool

from .. import exceptions as ex
from .. import logs as ls
from .. import tool_errors as te
from ..schemas import DirectoryListResult, ToolStatus
from . import tool_descriptions as td


class DirectoryLister:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()

    def list_directory_contents(self, directory_path: str) -> DirectoryListResult:
        target_path = self._get_safe_path(directory_path)
        logger.info(ls.DIR_LISTING.format(path=target_path))

        try:
            if not target_path.is_dir():
                return DirectoryListResult(
                    status=ToolStatus.ERROR,
                    error_message=te.DIRECTORY_INVALID.format(path=directory_path),
                    next_action="Use file_read if this is a file path",
                    path=directory_path,
                    contents=[],
                )

            if contents := os.listdir(target_path):
                return DirectoryListResult(
                    status=ToolStatus.SUCCESS,
                    path=directory_path,
                    contents=contents,
                )
            return DirectoryListResult(
                status=ToolStatus.EMPTY,
                error_message=te.DIRECTORY_EMPTY.format(path=directory_path),
                next_action="Try listing a different directory",
                path=directory_path,
                contents=[],
            )

        except Exception as e:
            logger.error(ls.DIR_LIST_ERROR.format(path=directory_path, error=e))
            return DirectoryListResult(
                status=ToolStatus.ERROR,
                error_message=te.DIRECTORY_LIST_FAILED.format(path=directory_path),
                next_action="Check permissions or try a different path",
                path=directory_path,
                contents=[],
            )

    def _get_safe_path(self, file_path: str) -> Path:
        if Path(file_path).is_absolute():
            safe_path = Path(file_path).resolve()
        else:
            safe_path = (self.project_root / file_path).resolve()

        try:
            safe_path.relative_to(self.project_root.resolve())
        except ValueError as e:
            raise PermissionError(ex.ACCESS_DENIED) from e

        if not str(safe_path).startswith(str(self.project_root.resolve())):
            raise PermissionError(ex.ACCESS_DENIED)

        return safe_path


def create_directory_lister_tool(directory_lister: DirectoryLister) -> Tool:
    async def list_directory(path: str) -> str:
        result = directory_lister.list_directory_contents(path)
        if result.status == ToolStatus.SUCCESS:
            return "\n".join(result.contents)
        return f"Error: {result.error_message}\nSuggested: {result.next_action}"

    return Tool(
        function=list_directory,
        name=td.AgenticToolName.LIST_DIRECTORY,
        description=td.DIRECTORY_LISTER,
    )
