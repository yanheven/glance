# Copyright 2015 Red Hat, Inc.
# All Rights Reserved.
#
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

from oslo_log import log as logging
from taskflow import task

from glance import i18n


LOG = logging.getLogger(__name__)
_LW = i18n._LW


class OptionalTask(task.Task):

    def __init__(self, *args, **kwargs):
        super(OptionalTask, self).__init__(*args, **kwargs)
        self.execute = self._catch_all(self.execute)

    def _catch_all(self, func):
        # NOTE(flaper87): Read this comment before calling the MI6
        # Here's the thing, there's no nice way to define "optional"
        # tasks. That is, tasks whose failure shouldn't affect the execution
        # of the flow. The only current "sane" way to do this, is by catching
        # everything and logging. This seems harmless from a taskflow
        # perspective but it is not. There are some issues related to this
        # "workaround":
        #
        # - Task's states will shamelessly lie to us saying the task succeeded.
        #
        # - No revert procedure will be triggered, which means optional tasks,
        # for now, mustn't cause any side-effects because they won't be able to
        # clean them up. If these tasks depend on other task that do cause side
        # effects, a task that cleans those side effects most be registered as
        # well. For example, _ImportToFS, _MyDumbTask, _DeleteFromFS.
        #
        # - Ideally, optional tasks shouldn't `provide` new values unless they
        # are part of an optional flow. Due to the decoration of the execute
        # method, these tasks will need to define the provided methods at
        # class level using `default_provides`.
        #
        #
        # The taskflow team is working on improving this and on something that
        # will provide the ability of defining optional tasks. For now, to lie
        # ourselves we must.
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                msg = (_LW("An optional task has failed, "
                           "the failure was: %s") %
                       exc.message)
                LOG.warn(msg)
        return wrapper
