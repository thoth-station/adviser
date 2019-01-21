import typing
import ctypes
lib = ctypes.cdll.LoadLibrary('./libdependency_graph.so')


class DependencyGraph:
    """Adapter for C implementation of dependency graph."""

    _C_CONSTRUCTOR = lib.DependencyGraph_new
    _C_CONSTRUCTOR.restype = ctypes.c_void_p
    _C_CONSTRUCTOR.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]

    _C_WALK = lib.DependencyGraph_walk
    _C_WALK.argtypes = [ctypes.c_void_p]
    _C_WALK.restype = ctypes.c_uint

    def __init__(
            self,
            direct_dependencies: typing.List[int],
            dependencies_list: typing.List[typing.List[int]],
            dependency_types: typing.List[int]
    ):
        """Construct dependency graph.

        Create a dependency graph by propagating arguments down to library. The arguments need to be first converted
        into C-type specific ones to have correct values in the C/C++ implementation..
        """
        size = len(dependency_types)
        c_dependency_types = (ctypes.c_uint * len(dependency_types))(*dependency_types)
        c_direct_dependencies = (ctypes.c_uint * len(direct_dependencies))(*direct_dependencies)

        # Convert list into ctype representation.
        c_rows = ctypes.c_uint * len(dependencies_list[1])
        c_matrix = ctypes.POINTER(ctypes.c_uint)*len(dependencies_list[0])

        c_dependency_list = c_matrix()
        for i, row in enumerate(dependencies_list):
            c_dependency_list[i] = c_rows()

            for j, val in enumerate(row):
                c_dependency_list[i][j] = val

        self.this = self._C_CONSTRUCTOR(c_direct_dependencies, c_dependency_list, c_dependency_types, size)

    def walk(self) -> typing.List[int]:
        """Generate a software stack by traversing the graph."""
        # TODO: convert to Python return value
        return self._C_WALK(self.this)


if __name__ == "__main__":
    f = DependencyGraph([1, 2], [[1, 2], [3, 2]], [1, 2, 5])
    f.walk()
