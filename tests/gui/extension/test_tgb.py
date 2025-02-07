# Copyright 2021-2025 Avaiga Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
import typing as t

from taipy.gui import Gui
from taipy.gui.extension import Element, ElementLibrary, ElementProperty, PropertyType


class TgbLibrary(ElementLibrary):
    elements = {
        "e1": Element(
            "s1",
            {
                "b1": ElementProperty(PropertyType.boolean, doc_string="e1.b1 doc"),
                "b2": ElementProperty(PropertyType.dynamic_boolean),
                "s1": ElementProperty(PropertyType.string),
                "s2": ElementProperty(PropertyType.dynamic_string),
                "d1": ElementProperty(PropertyType.dict),
                "d2": ElementProperty(PropertyType.dynamic_dict),
            },
            "E1", doc_string="e1 doc",
        ),
        "e2": Element(
            "x",
            {
                "p1": ElementProperty(PropertyType.any),
                "p2": ElementProperty(PropertyType.any),
            },
            "E2",
        ),
    }

    def get_name(self) -> str:
        return "test_ext_tgb"

    def get_elements(self) -> t.Dict[str, Element]:
        return TgbLibrary.elements


def test_tgb_generation(gui: Gui, test_client, helpers):
    from taipy.gui.extension.__main__ import generate_doc

    library = TgbLibrary()
    api = generate_doc(library)
    assert "def e1(" in api, "Missing element e1"
    assert "s1" in api, "Missing property s1"
    assert "s1: str" in api, "Incorrect property type for s1"
    assert "(s1: str, *" in api, "Property s1 should be the default property"
    assert "b1: bool" in api, "Missing or incorrect property type for b1"
    assert "b2: bool" in api, "Missing or incorrect property type for b2"
    assert "s2: str" in api, "Missing or incorrect property type for s2"
    assert "d1: dict" in api, "Missing or incorrect property type for d2"
    assert "d2: dict" in api, "Missing or incorrect property type for d2"
    assert "e1 doc" in api, "Missing doc for e1"
    assert "def e2(" in api, "Missing element e2"
    assert "e2(p1, p2)" in api, "Wrong default property in e2"
