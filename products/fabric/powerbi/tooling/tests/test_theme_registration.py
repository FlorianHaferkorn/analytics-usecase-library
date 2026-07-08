from pathlib import Path

from products.fabric.powerbi.tooling.theme_registration import (
    custom_theme_collection_name,
    find_registered_custom_theme_item,
    prepare_registered_theme_bytes,
    registered_theme_filename,
    safe_theme_stem,
    write_registered_theme,
)


def test_safe_theme_stem_sanitizes_hash():
    assert safe_theme_stem("Aurora_Group__Monochromatic__Light__#2ECDE7") == (
        "Aurora_Group__Monochromatic__Light___2ECDE7"
    )


def test_prepare_registered_theme_bytes_aligns_internal_name(tmp_path: Path):
    source = tmp_path / "Aurora_Group__Monochromatic__Light__#2ECDE7.json"
    source.write_text(
        '{"name":"Aurora_Group__Monochromatic__Light__#2ECDE7","dataColors":["#249FB3"]}\n',
        encoding="utf-8",
    )

    filename, content = prepare_registered_theme_bytes(source)

    assert filename == "Aurora_Group__Monochromatic__Light___2ECDE7.json"
    assert b'"name": "Aurora_Group__Monochromatic__Light___2ECDE7.json"' in content


def test_write_registered_theme_uses_dest_stem(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_text('{"name":"Brand Rose__Monochromatic__Light__#DD2D4A"}\n', encoding="utf-8")
    dest = tmp_path / "Brand_Rose__Monochromatic__Lig8107013084034419.json"

    output_path = write_registered_theme(source, dest)

    assert output_path == dest
    written = dest.read_text(encoding="utf-8")
    assert '"name": "Brand_Rose__Monochromatic__Lig8107013084034419.json"' in written


def test_write_registered_theme_sanitizes_unsafe_dest_filename(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_text('{"name":"Aurora_Group__Monochromatic__Light__#2ECDE7"}\n', encoding="utf-8")
    unsafe_dest = tmp_path / "Aurora_Group__Monochromatic__Light__#2ECDE7.json"

    output_path = write_registered_theme(source, unsafe_dest)

    expected = tmp_path / "Aurora_Group__Monochromatic__Light___2ECDE7.json"
    assert output_path == expected
    assert expected.exists()
    assert not unsafe_dest.exists()
    written = expected.read_text(encoding="utf-8")
    assert '"name": "Aurora_Group__Monochromatic__Light___2ECDE7.json"' in written


def test_find_registered_custom_theme_item_matches_filename():
    package = {
        "items": [
            {
                "name": "Aurora_Group__Monochromatic__Light___2ECDE7.json",
                "path": "Aurora_Group__Monochromatic__Light___2ECDE7.json",
                "type": "CustomTheme",
            }
        ]
    }
    stem = "Aurora_Group__Monochromatic__Light___2ECDE7"
    item = find_registered_custom_theme_item(package, stem)
    assert item is not None
    assert item["name"].endswith(".json")


def test_custom_theme_collection_name_strips_json_suffix():
    assert custom_theme_collection_name("Theme__Light___2ECDE7.json") == "Theme__Light___2ECDE7"
    assert registered_theme_filename("Theme__Light___2ECDE7") == "Theme__Light___2ECDE7.json"
