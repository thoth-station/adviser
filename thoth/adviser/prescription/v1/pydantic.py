# thoth-adviser
# Copyright(C) 2023 Max Gautier
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Prescription pydantic models."""

from typing import List, Union, Optional, Dict, Type, Generic, TypeVar

from pydantic import BaseModel, Field, conint, constr, conlist, validator, create_model
from pydantic.generics import GenericModel
from packaging.specifiers import SpecifierSet, InvalidSpecifier
from thoth.adviser.enums import RecommendationType, DecisionType
from thoth.adviser.cpu_db import CPUDatabase

_string = constr(min_length=1)
ModelT = TypeVar('ModelT')


def _list(type: Type) -> Type:
    return conlist(type=type, min_items=1)

_optional_integers = conlist(type=Union[int, None], min_items=1)

class Not(GenericModel, Generic[ModelT]):
    _not: ModelT = Field(alias="not") # We need this because 'not' is a reserved python keyword


def _with_not_list(type: Type) -> Type:
    return Union[Not[_list(type)],_list(type)]

def _with_not(type: Type) -> Type:
    return Union[Not[type], type]


class Dependencies(BaseModel):
    boots: Optional[_list(_string)]
    pseudonyms: Optional[_list(_string)]
    sieves: Optional[_list(_string)]
    steps: Optional[_list(_string)]
    strides: Optional[_list(_string)]
    wraps: Optional[_list(_string)]



class OperatingSystem(BaseModel):
    name: _string
    version: _string

class Hardware(BaseModel):
    cpu_families: Optional[_with_not(_optional_integers)]
    cpu_models: Optional[_with_not(_optional_integers)]
    cpu_flags: Optional[_with_not(create_model("CpuFlags", __base__=BaseModel))] # needs some stuff to avoid runtime creation


    # WIP
    Optional("cpu_flags"): _with_not(All(CPUDatabase.get_known_flags(), Length(min=1))),
    gpu_models: _with_not(_NONEMPTY_LIST_OF_NONEMPTY_STRINGS_WITH_NONE),


class RuntimeEnvironments(BaseModel):
    operating_systems: Optional[List[OperatingSystem]]
    hardware: Optional[_list(Hardware)]
    python_version: Optional[str]
    cuda_version: Optional[str]
    openblas_version: Optional[str]
    openmpi_version: Optional[str]
    cudnn_version: Optional[str]
    mkl_version: Optional[str]

    @validator('python_version', 'cuda_version', 'openblas_version', 'openmpi_version', 'mkl_version')
    def valid_version(cls, v):
        try:
            SpecifierSet(v)
        except InvalidSpecifier as e:
            raise ValueError(str(e))
        return v


class ShouldInclude(BaseModel):
    adviser_pipeline: Optional[bool]
    dependency_monkey_pipeline: Optional[bool]
    times: Optional[conint(ge=0, le=1)] = 0
    labels: Dict
    dependencies: Optional[Dependencies]
    recommendation_types: Optional[_with_not_list(RecommendationType)]
    decision_types: Optional[_with_not_list(DecisionType)]
    runtime_environments: Optional[_with_not_list(RuntimeEnvironments)]
    decision_types: Optional[List[str]]
    authenticated: Optional[bool]


class Unit(BaseModel):
    name: str
    type: str
    should_include: ShouldInclude

