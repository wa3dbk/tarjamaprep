from tarjamaprep.normalize.registry import get_rules, apply_rules

# Import rule modules so @register decorators fire
import tarjamaprep.normalize.arabic  # noqa: F401
import tarjamaprep.normalize.latin   # noqa: F401
import tarjamaprep.normalize.common  # noqa: F401
