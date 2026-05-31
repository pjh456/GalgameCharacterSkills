from __future__ import annotations

import pytest

from gal_chara_skill.llm.providers.openai import OpenAIProvider
from gal_chara_skill.llm.providers.registry import (
    ProviderNotFoundError,
    list_providers,
    register_provider,
    resolve_provider,
)


class TestRegisterProvider:
    def test_register_decorator_adds_to_registry(self) -> None:
        @register_provider("test-prov")  # type: ignore[arg-type]
        class TestProvider:
            pass

        assert "test-prov" in list_providers()

    def test_resolve_registered_provider(self) -> None:
        @register_provider("resolve-test")  # type: ignore[arg-type]
        class TestProvider:
            pass

        provider = resolve_provider("resolve-test")
        assert isinstance(provider, TestProvider)

    def test_resolve_unknown_raises_provider_not_found_error(self) -> None:
        with pytest.raises(ProviderNotFoundError, match="unknown-prov"):
            resolve_provider("unknown-prov")

    def test_list_providers_includes_openai(self) -> None:
        names = list_providers()
        assert "openai" in names

    def test_resolve_openai_via_registry(self) -> None:
        provider = resolve_provider("openai")
        assert isinstance(provider, OpenAIProvider)

    def test_lazy_instantiation_returns_new_instance_each_time(self) -> None:
        @register_provider("lazy-test")  # type: ignore[arg-type]
        class LazyProvider:
            pass

        a = resolve_provider("lazy-test")
        b = resolve_provider("lazy-test")
        assert a is not b

    def test_provider_not_found_error_stores_name(self) -> None:
        exc = ProviderNotFoundError("claude")
        assert exc.name == "claude"
        assert "claude" in str(exc)
