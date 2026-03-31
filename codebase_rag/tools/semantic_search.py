from __future__ import annotations

from loguru import logger
from pydantic_ai import Tool

from .. import constants as cs
from .. import exceptions as ex
from .. import logs as ls
from ..cypher_queries import (
    CYPHER_GET_FUNCTION_SOURCE_LOCATION,
    build_nodes_by_ids_query,
)
from ..schemas import SemanticSearchResponse, ToolStatus
from ..types_defs import SemanticSearchResult
from ..utils.dependencies import has_semantic_dependencies
from . import tool_descriptions as td


def semantic_code_search(query: str, top_k: int = 5) -> SemanticSearchResponse:
    if not has_semantic_dependencies():
        logger.warning(ex.SEMANTIC_EXTRA)
        return SemanticSearchResponse(
            status=ToolStatus.UNAVAILABLE,
            error_message="Semantic search unavailable - missing dependencies",
            next_action=cs.TOOL_FALLBACK_SEMANTIC,
            query=query,
            results=[],
        )

    try:
        from ..config import settings
        from ..embedder import embed_code
        from ..services.graph_service import MemgraphIngestor
        from ..vector_store import search_embeddings

        query_embedding = embed_code(query)

        search_results = search_embeddings(query_embedding, top_k=top_k)

        if not search_results:
            logger.info(ls.SEMANTIC_NO_MATCH.format(query=query))
            return SemanticSearchResponse(
                status=ToolStatus.EMPTY,
                error_message=f"No semantic matches found for '{query}'",
                next_action=cs.TOOL_FALLBACK_SEMANTIC,
                query=query,
                results=[],
            )

        node_ids = [node_id for node_id, _ in search_results]

        with MemgraphIngestor(
            host=settings.MEMGRAPH_HOST,
            port=settings.MEMGRAPH_PORT,
            batch_size=cs.SEMANTIC_BATCH_SIZE,
        ) as ingestor:
            cypher_query = build_nodes_by_ids_query(node_ids)
            params = {str(i): node_id for i, node_id in enumerate(node_ids)}
            results = ingestor._execute_query(cypher_query, params)

            results_map = {res["node_id"]: res for res in results}

            formatted_results: list[SemanticSearchResult] = []
            for node_id, score in search_results:
                if node_id in results_map:
                    result = results_map[node_id]
                    result_type = result["type"]
                    type_str = (
                        result_type[0]
                        if isinstance(result_type, list) and result_type
                        else cs.SEMANTIC_TYPE_UNKNOWN
                    )
                    formatted_results.append(
                        SemanticSearchResult(
                            node_id=node_id,
                            qualified_name=str(result["qualified_name"]),
                            name=str(result["name"]),
                            type=type_str,
                            score=round(score, 3),
                        )
                    )

            logger.info(
                ls.SEMANTIC_FOUND.format(count=len(formatted_results), query=query)
            )
            return SemanticSearchResponse(
                status=ToolStatus.SUCCESS,
                query=query,
                results=formatted_results,
            )

    except Exception as e:
        logger.error(ls.SEMANTIC_FAILED.format(query=query, error=e))
        return SemanticSearchResponse(
            status=ToolStatus.ERROR,
            error_message=f"Semantic search failed: {e}",
            next_action=cs.TOOL_FALLBACK_SEMANTIC,
            query=query,
            results=[],
        )


def get_function_source_code(node_id: int) -> str | None:
    try:
        from ..config import settings
        from ..services.graph_service import MemgraphIngestor
        from ..utils.source_extraction import (
            extract_source_lines,
            validate_source_location,
        )

        with MemgraphIngestor(
            host=settings.MEMGRAPH_HOST,
            port=settings.MEMGRAPH_PORT,
            batch_size=cs.SEMANTIC_BATCH_SIZE,
        ) as ingestor:
            results = ingestor._execute_query(
                CYPHER_GET_FUNCTION_SOURCE_LOCATION, {"node_id": node_id}
            )

            if not results:
                logger.warning(ls.SEMANTIC_NODE_NOT_FOUND.format(id=node_id))
                return None

            result = results[0]
            file_path = result.get("path")
            start_line = result.get("start_line")
            end_line = result.get("end_line")

            is_valid, file_path_obj = validate_source_location(
                file_path, start_line, end_line
            )
            if not is_valid or file_path_obj is None:
                logger.warning(ls.SEMANTIC_INVALID_LOCATION.format(id=node_id))
                return None

            return extract_source_lines(file_path_obj, start_line, end_line)

    except Exception as e:
        logger.error(ls.SEMANTIC_SOURCE_FAILED.format(id=node_id, error=e))
        return None


def create_semantic_search_tool() -> Tool:
    async def semantic_search_functions(query: str, top_k: int = 5) -> str:
        logger.info(ls.SEMANTIC_TOOL_SEARCH.format(query=query))

        response = semantic_code_search(query, top_k)

        if response.status == ToolStatus.UNAVAILABLE:
            return cs.MSG_TOOL_UNAVAILABLE.format(
                reason="required dependencies not installed",
                next_action=response.next_action or cs.TOOL_FALLBACK_SEMANTIC,
            )

        if response.status == ToolStatus.ERROR:
            return cs.MSG_TOOL_ERROR.format(
                error=response.error_message or "Unknown error",
                next_action=response.next_action or cs.TOOL_FALLBACK_SEMANTIC,
            )

        if response.status == ToolStatus.EMPTY or not response.results:
            return cs.MSG_TOOL_EMPTY.format(
                reason=f"No matches for '{query}'",
                next_action=response.next_action or cs.TOOL_FALLBACK_SEMANTIC,
            )

        formatted_results = []
        for i, result in enumerate(response.results, 1):
            formatted_results.append(
                f"{i}. {result['qualified_name']} (type: {result['type']}, score: {result['score']})"
            )

        output = cs.MSG_SEMANTIC_RESULT_HEADER.format(
            count=len(response.results), query=query
        )
        output += "\n".join(formatted_results)
        output += cs.MSG_SEMANTIC_RESULT_FOOTER

        return output

    return Tool(semantic_search_functions, name=td.AgenticToolName.SEMANTIC_SEARCH)


def create_get_function_source_tool() -> Tool:
    async def get_function_source_by_id(node_id: int) -> str:
        logger.info(ls.SEMANTIC_TOOL_SOURCE.format(id=node_id))

        source_code = get_function_source_code(node_id)

        if source_code is None:
            return cs.MSG_SEMANTIC_SOURCE_UNAVAILABLE.format(id=node_id)

        return cs.MSG_SEMANTIC_SOURCE_FORMAT.format(id=node_id, code=source_code)

    return Tool(get_function_source_by_id, name=td.AgenticToolName.GET_FUNCTION_SOURCE)
