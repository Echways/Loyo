# app/handlers/__init__.py
"""Aggregate handlers package with robust router resolution."""

from typing import Optional, Any, Dict
import logging
import inspect
import importlib
from aiogram import Router

log = logging.getLogger(__name__)

__all__ = ["register_handlers"]

def _try_import(name: str):
    """
    Try import handler submodule robustly:
     - first try package-relative import (works when package is imported normally)
     - then try absolute import app.handlers.<name> (works when running from project root / IDE)
    Logs full exception on failure and returns None.
    """
    # try package-relative import: ".<name>" with package=__name__
    try:
        module = importlib.import_module(f".{name}", package=__name__)
        log.info("Imported handlers.%s (relative)", name)
        return module
    except Exception as e_rel:
        log.debug("Relative import handlers.%s failed: %s", name, e_rel)

    # try absolute import: "app.handlers.<name>"
    try:
        module = importlib.import_module(f"app.handlers.{name}")
        log.info("Imported handlers.%s (absolute)", name)
        return module
    except Exception as e_abs:
        log.exception("Failed to import handlers.%s: %s", name, e_abs)
        return None


# Try to import modular handler modules if present
_user_mod = _try_import("user")
_admin_mod = _try_import("admin")
_callbacks_user_mod = _try_import("callbacks_user")


def _filter_kwargs_for_callable(callable_obj: Any, deps: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a dict with keys from deps that match the callable's parameter names.
    """
    try:
        sig = inspect.signature(callable_obj)
    except (ValueError, TypeError):
        return {}
    params = sig.parameters
    names = [name for name, p in params.items()
             if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)]
    filtered = {k: v for k, v in deps.items() if k in names}
    return filtered


def _resolve_router(obj: Any, deps: Dict[str, Any]) -> Router:
    """
    Resolve various router exports into an actual Router instance.

    Accepts:
      - Router instance -> returns it
      - Router subclass/type -> instantiate it
      - callable factory -> try to call with deps filtered to the factory signature
         * first try keyword call with matching names
         * then try positional call using deps values in parameter order (if possible)
      - otherwise raise TypeError
    """
    if isinstance(obj, Router):
        return obj

    if isinstance(obj, type) and issubclass(obj, Router):
        return obj()

    if callable(obj):
        # 1) try calling with only matching keyword args
        filtered_kwargs = _filter_kwargs_for_callable(obj, deps)
        try:
            router = obj(**filtered_kwargs)
            if isinstance(router, Router):
                return router
            raise TypeError("Router factory returned non-Router object: %r" % (router,))
        except TypeError as e_kw:
            log.debug("Keyword call failed for %r with filtered args %r: %s", obj, filtered_kwargs, e_kw)

        # 2) try positional: build args tuple in order of parameters if we have values for them
        try:
            sig = inspect.signature(obj)
            positional_args = []
            missing = []
            for name, param in sig.parameters.items():
                if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                    if name in deps:
                        positional_args.append(deps[name])
                    elif param.default is inspect._empty:
                        missing.append(name)
            if missing:
                raise TypeError(f"Callable router factory missing required positional dependencies: {missing}")
            router = obj(*positional_args)
            if isinstance(router, Router):
                return router
            raise TypeError("Router factory returned non-Router object with positional args: %r" % (router,))
        except TypeError as e_pos:
            raise TypeError(f"Callable router factory is not compatible: {e_pos}") from e_pos

    raise TypeError("router should be instance of Router or a factory returning Router, got %r" % (obj,))


def register_handlers(dp, ranks, async_session_maker, redis=None, admin_ids: Optional[list]=None, ranks_file=None, catalog=None, purchase_service=None):
    """
    Register user/admin/callbacks routers.
    Supports modules that expose either:
      - get_user_router(...) factory function (recommended)
      - router variable (Router instance)
      - Router class (will be instantiated)
    """
    if admin_ids is None:
        admin_ids = []

    deps = {
        "async_session_maker": async_session_maker,
        "ranks": ranks,
        "redis": redis,
        "admin_ids": admin_ids,
        "ranks_file": ranks_file,
    }

    modules = [
        (_user_mod, ("get_user_router", "router", "UserRouter")),
        (_admin_mod, ("get_admin_router", "router", "AdminRouter")),
        (_callbacks_user_mod, ("get_callbacks_user_router", "router", "CallbacksUserRouter")),
    ]

    for module, names in modules:
        if module is None:
            continue
        resolved = False
        for name in names:
            if hasattr(module, name):
                candidate = getattr(module, name)
                try:
                    router = _resolve_router(candidate, deps)
                    dp.include_router(router)
                    log.info("Included router from %s: attribute=%s", module.__name__, name)
                    resolved = True
                    break
                except Exception as e:
                    log.exception("Failed to include router from %s.%s: %s", module.__name__, name, e)
        if not resolved:
            log.warning("No usable router found in module %s (checked %s)", module.__name__, names)
