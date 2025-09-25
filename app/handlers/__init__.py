from typing import Optional, Any, Dict
import logging
import inspect
import importlib
from aiogram import Router

log = logging.getLogger(__name__)

__all__ = ["register_handlers"]

def _try_import(name: str):
    try:
        module = importlib.import_module(f".{name}", package=__name__)
        log.info("Imported handlers.%s (relative)", name)
        return module
    except Exception as e_rel:
        log.debug("Relative import handlers.%s failed: %s", name, e_rel)

    try:
        module = importlib.import_module(f"app.handlers.{name}")
        log.info("Imported handlers.%s (absolute)", name)
        return module
    except Exception as e_abs:
        log.exception("Failed to import handlers.%s: %s", name, e_abs)
        return None

_user_mod = _try_import("user")
_admin_mod = _try_import("admin")
_callbacks_user_mod = _try_import("callbacks_user")
_catalog_mod = _try_import("catalog")


def _filter_kwargs_for_callable(callable_obj: Any, deps: Dict[str, Any]) -> Dict[str, Any]:
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
    if isinstance(obj, Router):
        return obj

    if isinstance(obj, type) and issubclass(obj, Router):
        return obj()

    if callable(obj):
        filtered_kwargs = _filter_kwargs_for_callable(obj, deps)
        try:
            router = obj(**filtered_kwargs)
            if isinstance(router, Router):
                return router
            raise TypeError("Router factory returned non-Router object: %r" % (router,))
        except TypeError as e_kw:
            log.debug("Keyword call failed for %r with filtered args %r: %s", obj, filtered_kwargs, e_kw)
            
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


def register_handlers(dp, ranks, async_session_maker, redis=None, admin_ids: Optional[list]=None, ranks_file=None, engine=None, catalog_file=None, catalog=None):
    if admin_ids is None:
        admin_ids = []

    deps = {
        "async_session_maker": async_session_maker,
        "ranks": ranks,
        "redis": redis,
        "admin_ids": admin_ids,
        "ranks_file": ranks_file,
        "engine": engine,
        "catalog": catalog,
        "catalog_file": catalog_file,
    }

    modules = [
        (_user_mod, ("get_user_router", "router", "UserRouter")),
        (_admin_mod, ("get_admin_router", "router", "AdminRouter")),
        (_callbacks_user_mod, ("get_callbacks_user_router", "router", "CallbacksUserRouter")),
        (_catalog_mod, ("get_catalog_router", "router", "CatalogRouter")),
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
