"""
Testes unitários para Memory Store
"""
import pytest
from core.memory_store import MemoryStore


def test_memory_store_set_get():
    """Testa set e get"""
    store = MemoryStore()

    store.set("key1", "value1")
    assert store.get("key1") == "value1"


def test_memory_store_get_nonexistent():
    """Testa get de chave inexistente"""
    store = MemoryStore()

    assert store.get("nonexistent") is None
    assert store.get("nonexistent", "default") == "default"


def test_memory_store_delete():
    """Testa delete"""
    store = MemoryStore()

    store.set("key", "value")
    store.delete("key")

    assert store.get("key") is None


def test_memory_store_exists():
    """Testa exists"""
    store = MemoryStore()

    store.set("key", "value")

    assert store.exists("key") is True
    assert store.exists("nonexistent") is False


def test_memory_store_keys():
    """Testa listagem de keys"""
    store = MemoryStore()

    store.set("key1", "value1")
    store.set("key2", "value2")
    store.set("key3", "value3")

    keys = store.keys()
    assert len(keys) == 3
    assert "key1" in keys
    assert "key2" in keys
    assert "key3" in keys


def test_memory_store_clear():
    """Testa clear"""
    store = MemoryStore()

    store.set("key1", "value1")
    store.set("key2", "value2")

    store.clear()

    assert len(store.keys()) == 0
