# Copyright 2025 Juspay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0.txt

import glob
import os

package_dir = os.path.dirname(__file__)
modules = glob.glob(os.path.join(package_dir, "*.py"))

__all__ = []
for module in modules:
    module_name = os.path.basename(module)[:-3]
    if module_name != "__init__":
        __all__.append(module_name)
        __import__(f"{__name__}.{module_name}", globals(), locals(), [], 0)

