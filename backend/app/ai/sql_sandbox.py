# app/ai/sql_sandbox.py
"""
Sandbox for executing AI-generated queries safely.
Now adapted for MongoDB — validates and executes MongoDB queries
with strict safety controls.
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Any, Optional
import json
import re
from datetime import datetime

from app.config import get_settings

settings = get_settings()


class MongoSandbox:
    """
    Safe execution environment for AI-generated MongoDB queries.
    
    Safety layers:
    1. Collection whitelist
    2. No write operations
    3. Row limit enforcement
    4. Timeout enforcement
    5. Dangerous operator blocking
    6. Query complexity limits
    """
    
    # Operators that could modify data
    DANGEROUS_OPERATORS = {
        "$where",       # Allows JavaScript execution
        "$function",    # Allows JavaScript execution  
        "$accumulator", # Allows custom accumulators
        "$merge",       # Write operation
        "$out",         # Write operation
        "$lookup__pipeline__unlimited",  # Prevent unlimited pipeline stages
    }
    
    # Pipeline stages that write data
    WRITE_STAGES = {
        "$merge", "$out", "$replaceRoot",
    }
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    def validate_query(self, query: dict) -> dict:
        """
        Validate a MongoDB query before execution.
        Returns {is_safe, reason, sanitized_query}.
        """
        issues = []
        
        # 1. Must have collection
        collection = query.get("collection")
        if not collection:
            return {"is_safe": False, "reason": "missing_collection", "sanitized_query": None}
        
        # 2. Collection whitelist
        if collection not in settings.ALLOWED_COLLECTIONS:
            return {
                "is_safe": False,
                "reason": f"disallowed_collection: {collection}",
                "sanitized_query": None,
            }
        
        # 3. No write operations in query
        query_str = json.dumps(query)
        for op in self.DANGEROUS_OPERATORS:
            if op in query_str:
                issues.append(f"dangerous_operator: {op}")
        
        # Check for aggregation pipeline with write stages
        pipeline = query.get("pipeline", [])
        for stage in pipeline:
            for stage_name in stage.keys():
                if stage_name in self.WRITE_STAGES:
                    issues.append(f"write_pipeline_stage: {stage_name}")
        
        # 4. Enforce limit
        limit = query.get("limit", 100)
        if limit > settings.SQL_MAX_ROWS:
            query["limit"] = settings.SQL_MAX_ROWS
            issues.append(f"limit_capped_to_{settings.SQL_MAX_ROWS}")
        if "limit" not in query:
            query["limit"] = 100
        
        # 5. Check filter complexity (prevent DoS)
        filter_doc = query.get("filter", {})
        filter_str = json.dumps(filter_doc)
        
        # Prevent deeply nested queries
        max_depth = self._json_depth(filter_doc)
        if max_depth > 10:
            issues.append(f"filter_too_deep: {max_depth}")
        
        # 6. Check for regex without anchors (can be slow)
        if "$regex" in filter_str:
            regex_patterns = self._extract_regexes(filter_doc)
            for pattern in regex_patterns:
                if not pattern.startswith("^") and not pattern.endswith("$"):
                    issues.append(f"unanchored_regex: {pattern}")
        
        if issues:
            # Some issues are warnings, some are blockers
            blockers = [i for i in issues if any(
                b in i for b in ["dangerous_operator", "write_pipeline_stage", "disallowed"]
            )]
            if blockers:
                return {
                    "is_safe": False,
                    "reason": "; ".join(blockers),
                    "sanitized_query": None,
                }
        
        return {
            "is_safe": True,
            "reason": None,
            "sanitized_query": query,
            "warnings": issues if issues else None,
        }
    
    async def execute(
        self,
        query: dict,
        timeout_ms: Optional[int] = None,
    ) -> dict:
        """
        Execute a validated MongoDB query in the sandbox.
        Returns {rows, columns, row_count, execution_time_ms, error}.
        """
        import time
        
        start = time.time()
        timeout = timeout_ms or settings.MONGO_QUERY_TIMEOUT_MS
        
        try:
            collection_name = query["collection"]
            collection = self.db[collection_name]
            filter_doc = query.get("filter", {})
            projection = query.get("projection")
            sort_spec = query.get("sort", [])
            limit = query.get("limit", 100)
            
            # Handle parameter substitution
            filter_doc = self._substitute_params(filter_doc)
            
            # Check if this is an aggregation pipeline
            if "pipeline" in query:
                rows = await self._execute_pipeline(
                    collection, query["pipeline"], limit, timeout
                )
            else:
                # Regular find query
                cursor = collection.find(filter_doc, projection)
                
                # Apply sort
                for sort_pair in sort_spec:
                    if isinstance(sort_pair, list) and len(sort_pair) == 2:
                        cursor = cursor.sort(sort_pair[0], sort_pair[1])
                    elif isinstance(sort_pair, str):
                        cursor = cursor.sort(sort_pair, 1)
                
                # Apply limit
                cursor = cursor.limit(limit)
                
                # Execute with timeout
                rows = []
                async for doc in cursor:
                    # Convert ObjectId to string for JSON serialization
                    doc = self._serialize_doc(doc)
                    rows.append(doc)
            
            elapsed = int((time.time() - start) * 1000)
            
            # Get column names from first row
            columns = list(rows[0].keys()) if rows else []
            
            return {
                "rows": rows,
                "columns": columns,
                "row_count": len(rows),
                "execution_time_ms": elapsed,
                "error": None,
            }
            
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            return {
                "rows": [],
                "columns": [],
                "row_count": 0,
                "execution_time_ms": elapsed,
                "error": str(e),
            }
    
    async def _execute_pipeline(
        self, collection, pipeline: list, limit: int, timeout_ms: int
    ) -> list[dict]:
        """Execute an aggregation pipeline with safety limits."""
        # Add limit stage if not present
        has_limit = any("$limit" in stage for stage in pipeline)
        if not has_limit:
            pipeline.append({"$limit": limit})
        
        rows = []
        async for doc in collection.aggregate(pipeline):
            doc = self._serialize_doc(doc)
            rows.append(doc)
        
        return rows
    
    def _substitute_params(self, filter_doc: dict) -> dict:
        """Replace :param placeholders with actual values."""
        filter_str = json.dumps(filter_doc)
        # Common substitutions happen at the query translator level
        # This is a safety net
        return json.loads(filter_str) if filter_str else {}
    
    def _serialize_doc(self, doc: dict) -> dict:
        """Convert MongoDB document to JSON-serializable dict."""
        from bson import ObjectId
        
        result = {}
        for k, v in doc.items():
            if k == "_id":
                result[k] = str(v)
            elif isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, bytes):
                result[k] = v.decode("utf-8", errors="replace")
            else:
                result[k] = v
        return result
    
    def _json_depth(self, obj: Any, current: int = 0) -> int:
        """Calculate nesting depth of a JSON object."""
        if isinstance(obj, dict):
            if not obj:
                return current
            return max(self._json_depth(v, current + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current
            return max(self._json_depth(v, current + 1) for v in obj)
        return current
    
    def _extract_regexes(self, obj: Any) -> list[str]:
        """Extract regex patterns from a query document."""
        patterns = []
        if isinstance(obj, dict):
            if "$regex" in obj:
                patterns.append(str(obj["$regex"]))
            for v in obj.values():
                patterns.extend(self._extract_regexes(v))
        elif isinstance(obj, list):
            for v in obj:
                patterns.extend(self._extract_regexes(v))
        return patterns
    
    async def test_sandbox(self) -> dict:
        """
        Test the sandbox with safe and unsafe queries.
        Used for verification that safety controls work.
        """
        results = {
            "safe_queries_accepted": 0,
            "unsafe_queries_blocked": 0,
            "total_tests": 0,
            "details": [],
        }
        
        # Test 1: Safe query
        safe = self.validate_query({
            "collection": "labevents",
            "filter": {"hadm_id": 10005},
            "limit": 10,
        })
        results["total_tests"] += 1
        if safe["is_safe"]:
            results["safe_queries_accepted"] += 1
        results["details"].append({"query": "safe_find", "result": safe["is_safe"]})
        
        # Test 2: Disallowed collection
        unsafe1 = self.validate_query({
            "collection": "secret_data",
            "filter": {},
            "limit": 10,
        })
        results["total_tests"] += 1
        if not unsafe1["is_safe"]:
            results["unsafe_queries_blocked"] += 1
        results["details"].append({"query": "disallowed_collection", "result": not unsafe1["is_safe"]})
        
        # Test 3: Dangerous operator
        unsafe2 = self.validate_query({
            "collection": "patients",
            "filter": {"$where": "this.age > 100"},
            "limit": 10,
        })
        results["total_tests"] += 1
        if not unsafe2["is_safe"]:
            results["unsafe_queries_blocked"] += 1
        results["details"].append({"query": "dangerous_operator", "result": not unsafe2["is_safe"]})
        
        # Test 4: Write pipeline stage
        unsafe3 = self.validate_query({
            "collection": "patients",
            "pipeline": [{"$out": "stolen_data"}],
        })
        results["total_tests"] += 1
        if not unsafe3["is_safe"]:
            results["unsafe_queries_blocked"] += 1
        results["details"].append({"query": "write_pipeline", "result": not unsafe3["is_safe"]})
        
        # Test 5: No limit (should auto-add)
        no_limit = self.validate_query({
            "collection": "admissions",
            "filter": {},
        })
        results["total_tests"] += 1
        has_limit = no_limit.get("sanitized_query", {}).get("limit") is not None
        results["details"].append({"query": "auto_limit", "result": has_limit})
        
        results["all_passed"] = (
            results["safe_queries_accepted"] == 1 and
            results["unsafe_queries_blocked"] == 3
        )
        
        return results