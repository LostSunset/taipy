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
# -----------------------------------------------------------------------------------------
# To execute this script, make sure that the taipy-gui package is installed in your
# Python environment and run:
#     python <script>
# -----------------------------------------------------------------------------------------
import taipy.gui.builder as tgb
from taipy.gui import Gui

show_pane = False

with tgb.Page() as page:
    with tgb.part("d-flex"):
        with tgb.pane("{show_pane}", persistent=True, show_button=True, width="150px"):
            tgb.text("Here is the content of the pane.")
        with tgb.part():
            tgb.text("# Main page", mode="md")
            tgb.text("Here is the content of the page.")

if __name__ == "__main__":
    Gui(page).run(title="Pane - Persistent")
