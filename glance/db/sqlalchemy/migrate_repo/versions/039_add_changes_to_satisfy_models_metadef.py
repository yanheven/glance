#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import migrate
import sqlalchemy
from sqlalchemy import inspect
from sqlalchemy import (Table, Index, UniqueConstraint)
from sqlalchemy.schema import (AddConstraint, DropConstraint)


def upgrade(migrate_engine):
    meta = sqlalchemy.MetaData()
    meta.bind = migrate_engine
    inspector = inspect(migrate_engine)

    metadef_namespaces = Table('metadef_namespaces', meta, autoload=True)
    metadef_properties = Table('metadef_properties', meta, autoload=True)
    metadef_objects = Table('metadef_objects', meta, autoload=True)
    metadef_ns_res_types = Table('metadef_namespace_resource_types',
                                 meta, autoload=True)
    metadef_resource_types = Table('metadef_resource_types', meta,
                                   autoload=True)
    metadef_tags = Table('metadef_tags', meta, autoload=True)

    Index('ix_namespaces_namespace', metadef_namespaces.c.namespace).drop()

    Index('ix_objects_namespace_id_name', metadef_objects.c.namespace_id,
          metadef_objects.c.name).drop()

    Index('ix_metadef_properties_namespace_id_name',
          metadef_properties.c.namespace_id,
          metadef_properties.c.name).drop()

    fkc = migrate.ForeignKeyConstraint([metadef_tags.c.namespace_id],
                                       [metadef_namespaces.c.id])
    fkc.create()

    # `migrate` module removes unique constraint after adding
    # foreign key to the table in sqlite.
    # The reason of this issue is that it isn't possible to add fkc to
    # existing table in sqlite. Instead of this we should recreate the table
    # with needed fkc in the declaration. Migrate package provide us with such
    # possibility, but unfortunately it recreates the table without
    # constraints. Create unique constraint manually.
    if migrate_engine.name == 'sqlite' and len(
            inspector.get_unique_constraints('metadef_tags')) == 0:
        uc = migrate.UniqueConstraint(metadef_tags.c.namespace_id,
                                      metadef_tags.c.name)
        uc.create()

    Index('ix_tags_namespace_id_name', metadef_tags.c.namespace_id,
          metadef_tags.c.name).drop()

    Index('ix_metadef_tags_name', metadef_tags.c.name).create()

    Index('ix_metadef_tags_namespace_id', metadef_tags.c.namespace_id,
          metadef_tags.c.name).create()

    if migrate_engine.name == 'mysql':
        # We need to drop some foreign keys first  because unique constraints
        # that we want to delete depend on them. So drop the fk and recreate
        # it again after unique constraint deletion.
        fkc = migrate.ForeignKeyConstraint([metadef_properties.c.namespace_id],
                                           [metadef_namespaces.c.id],
                                           name='metadef_properties_ibfk_1')
        fkc.drop()
        constraint = UniqueConstraint(metadef_properties.c.namespace_id,
                                      metadef_properties.c.name,
                                      name='namespace_id')
        migrate_engine.execute(DropConstraint(constraint))
        fkc.create()

        fkc = migrate.ForeignKeyConstraint([metadef_objects.c.namespace_id],
                                           [metadef_namespaces.c.id],
                                           name='metadef_objects_ibfk_1')
        fkc.drop()
        constraint = UniqueConstraint(metadef_objects.c.namespace_id,
                                      metadef_objects.c.name,
                                      name='namespace_id')
        migrate_engine.execute(DropConstraint(constraint))
        fkc.create()

        constraint = UniqueConstraint(metadef_ns_res_types.c.resource_type_id,
                                      metadef_ns_res_types.c.namespace_id,
                                      name='resource_type_id')
        migrate_engine.execute(DropConstraint(constraint))

        constraint = UniqueConstraint(metadef_namespaces.c.namespace,
                                      name='namespace')
        migrate_engine.execute(DropConstraint(constraint))

        constraint = UniqueConstraint(metadef_resource_types.c.name,
                                      name='name')
        migrate_engine.execute(DropConstraint(constraint))

    if migrate_engine.name == 'postgresql':
        met_obj_index_name = (
            inspector.get_unique_constraints('metadef_objects')[0]['name'])
        constraint = UniqueConstraint(
            metadef_objects.c.namespace_id,
            metadef_objects.c.name,
            name=met_obj_index_name)
        migrate_engine.execute(DropConstraint(constraint))

        met_prop_index_name = (
            inspector.get_unique_constraints('metadef_properties')[0]['name'])
        constraint = UniqueConstraint(
            metadef_properties.c.namespace_id,
            metadef_properties.c.name,
            name=met_prop_index_name)
        migrate_engine.execute(DropConstraint(constraint))

        metadef_namespaces_name = (
            inspector.get_unique_constraints(
                'metadef_namespaces')[0]['name'])
        constraint = UniqueConstraint(
            metadef_namespaces.c.namespace,
            name=metadef_namespaces_name)
        migrate_engine.execute(DropConstraint(constraint))

        metadef_resource_types_name = (inspector.get_unique_constraints(
            'metadef_resource_types')[0]['name'])
        constraint = UniqueConstraint(
            metadef_resource_types.c.name,
            name=metadef_resource_types_name)
        migrate_engine.execute(DropConstraint(constraint))

        constraint = UniqueConstraint(
            metadef_tags.c.namespace_id,
            metadef_tags.c.name,
            name='metadef_tags_namespace_id_name_key')
        migrate_engine.execute(DropConstraint(constraint))

    Index('ix_metadef_ns_res_types_namespace_id',
          metadef_ns_res_types.c.namespace_id).create()

    Index('ix_metadef_namespaces_namespace',
          metadef_namespaces.c.namespace).create()

    Index('ix_metadef_namespaces_owner', metadef_namespaces.c.owner).create()

    Index('ix_metadef_objects_name', metadef_objects.c.name).create()

    Index('ix_metadef_objects_namespace_id',
          metadef_objects.c.namespace_id).create()

    Index('ix_metadef_properties_name', metadef_properties.c.name).create()

    Index('ix_metadef_properties_namespace_id',
          metadef_properties.c.namespace_id).create()


def downgrade(migrate_engine):
    meta = sqlalchemy.MetaData()
    meta.bind = migrate_engine

    metadef_namespaces = Table('metadef_namespaces', meta, autoload=True)
    metadef_properties = Table('metadef_properties', meta, autoload=True)
    metadef_objects = Table('metadef_objects', meta, autoload=True)
    metadef_ns_res_types = Table('metadef_namespace_resource_types',
                                 meta, autoload=True)
    metadef_resource_types = Table('metadef_resource_types', meta,
                                   autoload=True)
    metadef_tags = Table('metadef_tags', meta, autoload=True)

    Index('ix_namespaces_namespace', metadef_namespaces.c.namespace).create()

    Index('ix_objects_namespace_id_name', metadef_objects.c.namespace_id,
          metadef_objects.c.name).create()

    Index('ix_metadef_properties_namespace_id_name',
          metadef_properties.c.namespace_id,
          metadef_properties.c.name).create()

    Index('ix_metadef_tags_name', metadef_tags.c.name).drop()

    Index('ix_metadef_tags_namespace_id', metadef_tags.c.namespace_id,
          metadef_tags.c.name).drop()

    if migrate_engine.name != 'sqlite':
        fkc = migrate.ForeignKeyConstraint([metadef_tags.c.namespace_id],
                                           [metadef_namespaces.c.id])
        fkc.drop()

        Index('ix_tags_namespace_id_name', metadef_tags.c.namespace_id,
              metadef_tags.c.name).create()
    else:
        # NOTE(ochuprykov): fkc can't be dropped via `migrate` in sqlite,so it
        # is necessary to recreate table manually and populate it with data
        temp = Table('temp_', meta, *(
            [c.copy() for c in metadef_tags.columns]))
        temp.create()
        migrate_engine.execute('insert into temp_ select * from metadef_tags')
        metadef_tags.drop()
        migrate_engine.execute('alter table temp_ rename to metadef_tags')

        # Refresh old metadata for this table
        meta = sqlalchemy.MetaData()
        meta.bind = migrate_engine
        metadef_tags = Table('metadef_tags', meta, autoload=True)

        Index('ix_tags_namespace_id_name', metadef_tags.c.namespace_id,
              metadef_tags.c.name).create()

        uc = migrate.UniqueConstraint(metadef_tags.c.namespace_id,
                                      metadef_tags.c.name)
        uc.create()

    if migrate_engine.name == 'mysql':
        constraint = UniqueConstraint(metadef_properties.c.namespace_id,
                                      metadef_properties.c.name,
                                      name='namespace_id')
        migrate_engine.execute(AddConstraint(constraint))

        constraint = UniqueConstraint(metadef_objects.c.namespace_id,
                                      metadef_objects.c.name,
                                      name='namespace_id')
        migrate_engine.execute(AddConstraint(constraint))

        constraint = UniqueConstraint(metadef_ns_res_types.c.resource_type_id,
                                      metadef_ns_res_types.c.namespace_id,
                                      name='resource_type_id')
        migrate_engine.execute(AddConstraint(constraint))

        constraint = UniqueConstraint(metadef_namespaces.c.namespace,
                                      name='namespace')
        migrate_engine.execute(AddConstraint(constraint))

        constraint = UniqueConstraint(metadef_resource_types.c.name,
                                      name='name')
        migrate_engine.execute(AddConstraint(constraint))

    if migrate_engine.name == 'postgresql':
        constraint = UniqueConstraint(
            metadef_objects.c.namespace_id,
            metadef_objects.c.name)
        migrate_engine.execute(AddConstraint(constraint))

        constraint = UniqueConstraint(
            metadef_properties.c.namespace_id,
            metadef_properties.c.name)
        migrate_engine.execute(AddConstraint(constraint))

        constraint = UniqueConstraint(
            metadef_namespaces.c.namespace)
        migrate_engine.execute(AddConstraint(constraint))

        constraint = UniqueConstraint(
            metadef_resource_types.c.name)
        migrate_engine.execute(AddConstraint(constraint))

        constraint = UniqueConstraint(
            metadef_tags.c.namespace_id,
            metadef_tags.c.name,
            name='metadef_tags_namespace_id_name_key')
        migrate_engine.execute(AddConstraint(constraint))

    if migrate_engine.name == 'mysql':
        fkc = migrate.ForeignKeyConstraint(
            [metadef_ns_res_types.c.resource_type_id],
            [metadef_namespaces.c.id],
            name='metadef_namespace_resource_types_ibfk_2')
        fkc.drop()

        Index('ix_metadef_ns_res_types_namespace_id',
              metadef_ns_res_types.c.namespace_id).drop()

        fkc.create()
    else:
        Index('ix_metadef_ns_res_types_namespace_id',
              metadef_ns_res_types.c.namespace_id).drop()

    Index('ix_metadef_namespaces_namespace',
          metadef_namespaces.c.namespace).drop()

    Index('ix_metadef_namespaces_owner', metadef_namespaces.c.owner).drop()

    Index('ix_metadef_objects_name', metadef_objects.c.name).drop()

    Index('ix_metadef_objects_namespace_id',
          metadef_objects.c.namespace_id).drop()

    Index('ix_metadef_properties_name', metadef_properties.c.name).drop()

    Index('ix_metadef_properties_namespace_id',
          metadef_properties.c.namespace_id).drop()
