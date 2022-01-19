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


class ShIPMIError(Exception):
    message = None

    def __init__(self, message=None, **kwargs):
        if self.message and kwargs:
            self.message = self.message % kwargs
        else:
            self.message = message

        super(ShIPMIError, self).__init__(self.message)


class ProviderNotFound(ShIPMIError):
    message = 'No provider with matching name "%(name)s" was found'


class VirtualBMCCommandFailed(ShIPMIError):
    message = 'Command "%(command)s" failed with exit code %(exitcode)s'


class VirtualBMCAlreadyExists(ShIPMIError):
    message = 'Virtual BMC "%(name)s" already exists'


class VirtualBMCNotFound(ShIPMIError):
    message = 'No virtual BMC with matching name "%(name)s" was found'


class DetachProcessError(ShIPMIError):
    message = ('Error when forking (detaching) the ShIPMI process '
               'from its parent and session. Error: %(error)s')
