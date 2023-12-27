# Cruiz workers API

import cruiz.globals as globals

from .common import endmessagethread

if globals.CONAN_MAJOR_VERSION == 1:
    from .v1 import (  # noqa: E402
        arbitrary,
        build,
        cmakebuildtool,
        configinstall,
        create,
        deletecmakecache,
        exportpackage,
        imports,
        install,
        lockcreate,
        meta,
        package,
        packagebinary,
        packagedetails,
        packagerevisions,
        reciperevisions,
        remotesearch,
        removeallpackages,
        removelocks,
        removepackage,
        source,
        testpackage,
    )
else:
    from .v2 import (  # type: ignore[no-redef] # noqa: E402
        arbitrary,
        build,
        configinstall,
        create,
        exportpackage,
        install,
        lockcreate,
        meta,
        packagebinary,
        packagedetails,
        packagerevisions,
        reciperevisions,
        remotesearch,
        removeallpackages,
        removepackage,
        source,
        testpackage,
    )
