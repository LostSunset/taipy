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

import inspect
import re
import types
from abc import abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

from .._config import _Config
from ..common._template_handler import _TemplateHandler
from ..common._validate_id import _validate_id
from ..exceptions.exceptions import InvalidConfigurationType, LoadingError
from ..global_app.global_app_config import GlobalAppConfig
from ..section import Section
from ..unique_section import UniqueSection


class _BaseSerializer(object):
    """Base serializer class for taipy configuration."""

    _GLOBAL_NODE_NAME = "TAIPY"
    _SERIALIZABLE_TYPES = [
        "bool",
        "str",
        "int",
        "float",
        "datetime",
        "timedelta",
        "function",
        "class",
        "enum",
        "SECTION",
    ]
    _section_class = {_GLOBAL_NODE_NAME: GlobalAppConfig}
    _registered_types: Dict[str, type] = {}

    @classmethod
    def _register(cls, section):
        cls._section_class[section.name] = section.__class__
        for clazz in section._types_to_register():
            if not hasattr(clazz, "_type_identifier"):
                raise InvalidConfigurationType(f"Type {clazz.__name__} must have a `_type_identifier` method.")
            if not hasattr(clazz, "_stringify"):
                raise InvalidConfigurationType(f"Type {clazz.__name__} must have a `_stringify` method.")
            if not hasattr(clazz, "_pythonify"):
                raise InvalidConfigurationType(f"Type {clazz.__name__} must have a `_pythonify` method.")
            cls._registered_types[clazz._type_identifier()] = clazz

            if clazz._type_identifier() not in cls._SERIALIZABLE_TYPES:
                cls._SERIALIZABLE_TYPES.append(clazz._type_identifier())

    @classmethod
    @abstractmethod
    def _write(cls, configuration: _Config, filename: str):
        raise NotImplementedError

    @classmethod
    def _str(cls, configuration: _Config):
        config_as_dict = {cls._GLOBAL_NODE_NAME: configuration._global_config._to_dict()}
        for u_sect_name, u_sect in configuration._unique_sections.items():
            config_as_dict[u_sect_name] = u_sect._to_dict()
        for sect_name, sections in configuration._sections.items():
            config_as_dict[sect_name] = cls.__to_dict(sections)
        return cls._stringify(config_as_dict)

    @classmethod
    def __to_dict(cls, sections: Dict[str, Any]):
        return {section_id: section._to_dict() for section_id, section in sections.items()}

    @classmethod
    def _stringify(cls, as_dict):
        if as_dict is None:
            return None
        if hasattr(as_dict, "_stringify") and callable(as_dict._stringify):
            return as_dict._stringify()
        if isinstance(as_dict, bool):
            return f"{str(as_dict)}:bool"
        if isinstance(as_dict, int):
            return f"{str(as_dict)}:int"
        if isinstance(as_dict, float):
            return f"{str(as_dict)}:float"
        if isinstance(as_dict, datetime):
            return f"{as_dict.isoformat()}:datetime"
        if isinstance(as_dict, timedelta):
            return f"{cls._timedelta_to_str(as_dict)}:timedelta"
        if inspect.isfunction(as_dict) or isinstance(as_dict, types.BuiltinFunctionType):
            return f"{as_dict.__module__}.{as_dict.__name__}:function"
        if inspect.isclass(as_dict):
            return f"{as_dict.__module__}.{as_dict.__qualname__}:class"
        if isinstance(as_dict, Enum):
            return f"{as_dict.__module__}.{as_dict.__class__.__qualname__}.{as_dict.name}:enum"
        if isinstance(as_dict, dict):
            return {str(key): cls._stringify(val) for key, val in as_dict.items()}
        if isinstance(as_dict, list):
            return [cls._stringify(val) for val in as_dict]
        if isinstance(as_dict, tuple):
            return [cls._stringify(val) for val in as_dict]
        if isinstance(as_dict, set):
            return [cls._stringify(val) for val in as_dict]
        return as_dict

    @classmethod
    def _from_dict(cls, as_dict) -> _Config:
        config = _Config()
        config._global_config = GlobalAppConfig._from_dict(as_dict.get(cls._GLOBAL_NODE_NAME, {}))
        for section_name, sect_as_dict in as_dict.items():
            if section_class := cls._section_class.get(section_name, None):
                if issubclass(section_class, UniqueSection):
                    config._unique_sections[section_name] = section_class._from_dict(  # type: ignore
                        sect_as_dict, None, None
                    )
                elif issubclass(section_class, Section):
                    config._sections[section_name] = cls.__extract_node(as_dict, section_class, section_name, config)
        return config

    @staticmethod
    def __extract_node(config_as_dict, cls_config, node, config: Optional[Any]) -> Dict[str, Section]:
        res = {}
        for key, value in config_as_dict.get(node, {}).items():  # my_task, {input=[], output=[my_data_node], ...}
            key = _validate_id(key)
            res[key] = cls_config._from_dict(value, key, config)
        return res

    @classmethod
    def _pythonify(cls, val):
        match = re.fullmatch(_TemplateHandler._PATTERN, str(val))
        if not match:
            if isinstance(val, str):
                TYPE_PATTERN = r"^(.+):(\b" + r"\b|\b".join(cls._SERIALIZABLE_TYPES) + r"\b)?$"
                if match := re.fullmatch(TYPE_PATTERN, str(val)):
                    actual_val = match.group(1)
                    dynamic_type = match.group(2)
                    if dynamic_type == "SECTION":
                        return actual_val
                    if dynamic_type in cls._registered_types.keys():
                        return cls._registered_types[dynamic_type]._pythonify(actual_val)
                    if dynamic_type == "bool":
                        return _TemplateHandler._to_bool(actual_val)
                    elif dynamic_type == "int":
                        return _TemplateHandler._to_int(actual_val)
                    elif dynamic_type == "float":
                        return _TemplateHandler._to_float(actual_val)
                    elif dynamic_type == "datetime":
                        return _TemplateHandler._to_datetime(actual_val)
                    elif dynamic_type == "timedelta":
                        return _TemplateHandler._to_timedelta(actual_val)
                    elif dynamic_type == "function":
                        return _TemplateHandler._to_function(actual_val)
                    elif dynamic_type == "class":
                        return _TemplateHandler._to_class(actual_val)
                    elif dynamic_type == "enum":
                        return _TemplateHandler._to_enum(actual_val)
                    elif dynamic_type == "str":
                        return actual_val
                    else:
                        error_msg = f"Error loading toml configuration at {val}. {dynamic_type} type is not supported."
                        raise LoadingError(error_msg)
            if isinstance(val, dict):
                if len(val) == 1 and list(val.keys())[0] in cls._registered_types.keys():
                    return cls._registered_types[list(val.keys())[0]]._pythonify(list(val.values())[0])
                return {str(k): cls._pythonify(v) for k, v in val.items()}
            if isinstance(val, list):
                return [cls._pythonify(v) for v in val]
        return val

    @classmethod
    def _timedelta_to_str(cls, obj: timedelta) -> str:
        total_seconds = obj.total_seconds()
        return (
            f"{int(total_seconds // 86400)}d"
            f"{int(total_seconds % 86400 // 3600)}h"
            f"{int(total_seconds % 3600 // 60)}m"
            f"{int(total_seconds % 60)}s"
        )
