import asyncio

from jarvis_portal import IOContext, create_default_registry


def test_file_adapter_can_write_and_read_text(tmp_path):
    path = tmp_path / "note.txt"
    adapter = create_default_registry().get("File", "input")

    asyncio.run(adapter.write_input(IOContext(), {"path": str(path), "content": "hello"}, {}))

    result = asyncio.run(
        adapter.read_output(
            IOContext(),
            {"path": str(path), "name": "note", "read_content": True},
        )
    )
    assert result == {"note": "hello"}
