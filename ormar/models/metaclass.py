import copy
import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, cast

import pydantic
import sqlalchemy
from pydantic import field_serializer
from pydantic._internal._generics import PydanticGenericMetadata
from pydantic.fields import ComputedFieldInfo, FieldInfo
from pydantic_core.core_schema import SerializerFunctionWrapHandler
from sqlalchemy.sql.schema import ColumnCollectionConstraint

import ormar  # noqa I100
import ormar.fields.constraints
from ormar import ModelDefinitionError  # noqa I100
from ormar.exceptions import ModelError
from ormar.fields import BaseField
from ormar.fields.constraints import CheckColumns, IndexColumns, UniqueColumns
from ormar.fields.foreign_key import ForeignKeyField
from ormar.fields.many_to_many import ManyToManyField
from ormar.models.descriptors import (
    JsonDescriptor,
    PkDescriptor,
    PydanticDescriptor,
    RelationDescriptor,
)
from ormar.models.descriptors.descriptors import BytesDescriptor
from ormar.models.helpers import (
    check_required_config_parameters,
    config_field_not_set,
    expand_reverse_relationships,
    extract_annotations_and_default_vals,
    get_potential_fields,
    merge_or_generate_pydantic_config,
    modify_schema_example,
    populate_config_sqlalchemy_table_if_required,
    populate_config_tablename_columns_and_pk,
    populate_default_options_values,
    register_relation_in_alias_manager,
    sqlalchemy_columns_from_model_fields,
)
from ormar.models.ormar_config import OrmarConfig
from ormar.models.quick_access_views import quick_access_set
from ormar.queryset import FieldAccessor, QuerySet
from ormar.signals import Signal

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.models import T

CONFIG_KEY = "Config"
PARSED_FIELDS_KEY = "__parsed_fields__"


def add_cached_properties(new_model: type["Model"]) -> None:
    """
    Sets cached properties for both pydantic and ormar models.

    Quick access fields are fields grabbed in getattribute to skip all checks.

    Related fields and names are populated to None as they can change later.
    When children models are constructed they can modify parent to register itself.

    All properties here are used as "cache" to not recalculate them constantly.

    :param new_model: newly constructed Model
    :type new_model: Model class
    """
    pass


def add_property_fields(new_model: type["Model"], attrs: dict) -> None:  # noqa: CCR001
    """
    Checks class namespace for properties or functions with computed_field.
    If attribute have decorator_info it was decorated with @computed_field.

    Functions like this are exposed in dict() (therefore also fastapi result).
    Names of property fields are cached for quicker access / extraction.

    :param new_model: newly constructed model
    :type new_model: Model class
    :param attrs:
    :type attrs: dict[str, str]
    """
    pass


def register_signals(new_model: type["Model"]) -> None:  # noqa: CCR001
    """
    Registers on model's SignalEmmiter and sets pre-defined signals.
    Predefined signals are (pre/post) + (save/update/delete).

    Signals are emitted in both model own methods and in selected queryset ones.

    :param new_model: newly constructed model
    :type new_model: Model class
    """
    pass


def verify_constraint_names(
    base_class: "Model", model_fields: dict, parent_value: list
) -> None:
    """
    Verifies if redefined fields that are overwritten in subclasses did not remove
    any name of the column that is used in constraint as it will fail in sqlalchemy
    Table creation.

    :param base_class: one of the parent classes
    :type base_class: Model or model parent class
    :param model_fields: ormar fields in defined in current class
    :type model_fields: dict[str, BaseField]
    :param parent_value: list of base class constraints
    :type parent_value: list
    """
    pass


def get_constraint_copy(
    constraint: ColumnCollectionConstraint,
) -> Union[UniqueColumns, IndexColumns, CheckColumns]:
    """
    Copy the constraint and unpacking it's values

    :raises ValueError: if non subclass of ColumnCollectionConstraint
    :param value: an instance of the ColumnCollectionConstraint class
    :type value: Instance of ColumnCollectionConstraint child
    :return: copy ColumnCollectionConstraint ormar constraints
    :rtype: Union[UniqueColumns, IndexColumns, CheckColumns]
    """

    constraints = {
        sqlalchemy.UniqueConstraint: lambda x: UniqueColumns(*x._pending_colargs),
        sqlalchemy.Index: lambda x: IndexColumns(*x._pending_colargs),
        sqlalchemy.CheckConstraint: lambda x: CheckColumns(x.sqltext),
    }
    checks = (key if isinstance(constraint, key) else None for key in constraints)
    target_class = next((target for target in checks if target is not None), None)
    constructor: Optional[Callable] = (
        constraints.get(target_class) if target_class else None
    )
    if not constructor:
        raise ValueError(f"{constraint} must be a ColumnCollectionMixin!")

    return constructor(constraint)


def update_attrs_from_base_config(  # noqa: CCR001
    base_class: "Model", attrs: dict, model_fields: dict
) -> None:
    """
    Updates OrmarConfig parameters in child from parent if needed.

    :param base_class: one of the parent classes
    :type base_class: Model or model parent class
    :param attrs: new namespace for class being constructed
    :type attrs: dict
    :param model_fields: ormar fields in defined in current class
    :type model_fields: dict[str, BaseField]
    """
    pass


def copy_and_replace_m2m_through_model(  # noqa: CFQ002
    field: ManyToManyField,
    field_name: str,
    table_name: str,
    parent_fields: dict,
    attrs: dict,
    ormar_config: OrmarConfig,
    base_class: type["Model"],
) -> None:
    """
    Clones class with Through model for m2m relations, appends child name to the name
    of the cloned class.

    Clones non foreign keys fields from parent model, the same with database columns.

    Modifies related_name with appending child table name after '_'

    For table name, the table name of child is appended after '_'.

    Removes the original sqlalchemy table from metadata if it was not removed.

    :param base_class: base class model
    :type base_class: type["Model"]
    :param field: field with relations definition
    :type field: ManyToManyField
    :param field_name: name of the relation field
    :type field_name: str
    :param table_name: name of the table
    :type table_name: str
    :param parent_fields: dictionary of fields to copy to new models from parent
    :type parent_fields: dict
    :param attrs: new namespace for class being constructed
    :type attrs: dict
    :param ormar_config: metaclass of currently created model
    :type ormar_config: OrmarConfig
    """
    pass


def copy_data_from_parent_model(  # noqa: CCR001
    base_class: type["Model"],
    curr_class: type,
    attrs: dict,
    model_fields: dict[str, Union[BaseField, ForeignKeyField, ManyToManyField]],
) -> tuple[dict, dict]:
    """
    Copy the key parameters [database, metadata, property_fields and constraints]
    and fields from parent models. Overwrites them if needed.

    Only abstract classes can be subclassed.

    Since relation fields requires different related_name for different children


    :raises ModelDefinitionError: if non abstract model is subclassed
    :param base_class: one of the parent classes
    :type base_class: Model or model parent class
    :param curr_class: current constructed class
    :type curr_class: Model or model parent class
    :param attrs: new namespace for class being constructed
    :type attrs: dict
    :param model_fields: ormar fields in defined in current class
    :type model_fields: dict[str, BaseField]
    :return: updated attrs and model_fields
    :rtype: tuple[dict, dict]
    """
    pass


def extract_from_parents_definition(  # noqa: CCR001
    base_class: type,
    curr_class: type,
    attrs: dict,
    model_fields: dict[str, Union[BaseField, ForeignKeyField, ManyToManyField]],
) -> tuple[dict, dict]:
    """
    Extracts fields from base classes if they have valid ormar fields.

    If model was already parsed -> fields definitions need to be removed from class
    cause pydantic complains about field re-definition so after first child
    we need to extract from __parsed_fields__ not the class itself.

    If the class is parsed first time annotations and field definition is parsed
    from the class.__dict__.

    If the class is a ormar.Model it is skipped.

    :param base_class: one of the parent classes
    :type base_class: Model or model parent class
    :param curr_class: current constructed class
    :type curr_class: Model or model parent class
    :param attrs: new namespace for class being constructed
    :type attrs: dict
    :param model_fields: ormar fields in defined in current class
    :type model_fields: dict[str, BaseField]
    :return: updated attrs and model_fields
    :rtype: tuple[dict, dict]
    """
    pass


def update_attrs_and_fields(
    attrs: dict,
    new_attrs: dict,
    model_fields: dict,
    new_model_fields: dict,
    new_fields: set,
) -> dict:
    """
    Updates __annotations__, values of model fields (so pydantic FieldInfos)
    as well as model.ormar_config.model_fields definitions from parents.

    :param attrs: new namespace for class being constructed
    :type attrs: dict
    :param new_attrs: related of the namespace extracted from parent class
    :type new_attrs: dict
    :param model_fields: ormar fields in defined in current class
    :type model_fields: dict[str, BaseField]
    :param new_model_fields: ormar fields defined in parent classes
    :type new_model_fields: dict[str, BaseField]
    :param new_fields: set of new fields names
    :type new_fields: set[str]
    """
    pass


def add_field_descriptor(
    name: str, field: "BaseField", new_model: type["Model"]
) -> None:
    """
    Sets appropriate descriptor for each model field.
    There are 5 main types of descriptors, for bytes, json, pure pydantic fields,
    and 2 ormar ones - one for relation and one for pk shortcut

    :param name: name of the field
    :type name: str
    :param field: model field to add descriptor for
    :type field: BaseField
    :param new_model: model with fields
    :type new_model: type["Model]
    """
    pass


def get_serializer() -> Callable:
    pass


class ModelMetaclass(pydantic._internal._model_construction.ModelMetaclass):
    def __new__(  # type: ignore # noqa: CCR001
        mcs: "ModelMetaclass",
        name: str,
        bases: Any,
        attrs: dict,
        __pydantic_generic_metadata__: Union[PydanticGenericMetadata, None] = None,
        __pydantic_reset_parent_namespace__: bool = True,
        _create_model_module: Union[str, None] = None,
        **kwargs,
    ) -> type:
        """
        Metaclass used by ormar Models that performs configuration
        and build of ormar Models.


        Sets pydantic configuration.
        Extract model_fields and convert them to pydantic FieldInfo,
        updates class namespace.

        Extracts settings and fields from parent classes.
        Fetches methods decorated with @computed_field decorator
        to expose them later in dict().

        Construct parent pydantic Metaclass/ Model.

        If class has ormar_config declared (so actual ormar Models) it also:

        * populate sqlalchemy columns, pkname and tables from model_fields
        * register reverse relationships on related models
        * registers all relations in alias manager that populates table_prefixes
        * exposes alias manager on each Model
        * creates QuerySet for each model and exposes it on a class
        * sets custom serializers for relation models

        :param name: name of current class
        :type name: str
        :param bases: base classes
        :type bases: tuple
        :param attrs: class namespace
        :type attrs: dict
        """
        merge_or_generate_pydantic_config(attrs=attrs, name=name)
        attrs["__name__"] = name
        attrs, model_fields = extract_annotations_and_default_vals(attrs)
        for base in reversed(bases):
            mod = base.__module__
            if mod.startswith("ormar.models.") or mod.startswith("pydantic."):
                continue
            attrs, model_fields = extract_from_parents_definition(
                base_class=base, curr_class=mcs, attrs=attrs, model_fields=model_fields
            )
        if "ormar_config" in attrs:
            attrs["model_config"]["ignored_types"] = (OrmarConfig,)
            attrs["model_config"]["from_attributes"] = True
            for field_name, field in model_fields.items():
                if field.is_relation:
                    decorator = field_serializer(
                        field_name, mode="wrap", check_fields=False
                    )(get_serializer())
                    attrs[f"serialize_{field_name}"] = decorator

        new_model = super().__new__(
            mcs,  # type: ignore
            name,
            bases,
            attrs,
            __pydantic_generic_metadata__=__pydantic_generic_metadata__,
            __pydantic_reset_parent_namespace__=__pydantic_reset_parent_namespace__,
            _create_model_module=_create_model_module,
            **kwargs,
        )

        add_cached_properties(new_model)

        if hasattr(new_model, "ormar_config"):
            populate_default_options_values(new_model, model_fields)
            check_required_config_parameters(new_model)
            add_property_fields(new_model, attrs)
            register_signals(new_model=new_model)
            modify_schema_example(model=new_model)

            if not new_model.ormar_config.abstract:
                new_model = populate_config_tablename_columns_and_pk(name, new_model)
                populate_config_sqlalchemy_table_if_required(new_model.ormar_config)
                expand_reverse_relationships(new_model)
                for field_name, field in new_model.ormar_config.model_fields.items():
                    register_relation_in_alias_manager(field=field)
                    add_field_descriptor(
                        name=field_name, field=field, new_model=new_model
                    )

                if (
                    new_model.ormar_config.pkname
                    and new_model.ormar_config.pkname not in attrs["__annotations__"]
                    and new_model.ormar_config.pkname not in new_model.model_fields
                ):
                    field_name = new_model.ormar_config.pkname
                    new_model.model_fields[field_name] = (
                        FieldInfo.from_annotated_attribute(
                            Optional[int],  # type: ignore
                            None,
                        )
                    )
                    new_model.model_rebuild(force=True)

                new_model.pk = PkDescriptor(name=new_model.ormar_config.pkname)

        return new_model

    @property
    def objects(cls: type["T"]) -> "QuerySet[T]":  # type: ignore
        pass

    def __getattr__(self, item: str) -> Any:
        """
        Returns FieldAccessors on access to model fields from a class,
        that way it can be used in python style filters and order_by.

        :param item: name of the field
        :type item: str
        :return: FieldAccessor for given field
        :rtype: FieldAccessor
        """
        # Ugly workaround for name shadowing warnings in pydantic
        frame = sys._getframe(1)
        file_name = Path(frame.f_code.co_filename)
        if (
            frame.f_code.co_name == "collect_model_fields"
            and file_name.name == "_fields.py"
            and file_name.parent.parent.name == "pydantic"
        ):
            raise AttributeError()
        if item == "pk":
            item = self.ormar_config.pkname
        if item in object.__getattribute__(self, "ormar_config").model_fields:
            field = self.ormar_config.model_fields.get(item)
            if field.is_relation:
                return FieldAccessor(
                    source_model=cast(type["Model"], self),
                    model=field.to,
                    access_chain=item,
                )
            return FieldAccessor(
                source_model=cast(type["Model"], self), field=field, access_chain=item
            )
        return object.__getattribute__(self, item)
