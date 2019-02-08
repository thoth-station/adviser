import ctypes
lib = ctypes.cdll.LoadLibrary('./dependency_graph.so')


class DependencyGraph:
    def __init__(self, dependencies_list, dependency_types):
        dependency_types = (ctypes.c_uint * len(arr))(*arr)
        dependencies_list = 0
        #self.obj = lib.DependencyGraph_new(dependencies_list, dependency_types)
        self.obj = lib.DependencyGraph_new()
        print("%04x" % self.obj)

    def walk(self):
        return lib.DependencyGraph_walk(self.obj)


if __name__ == "__main__":
    print("="*10)
    arr = [1, 2, 3, 4]
    dependencies_list = [[3, 4, 5, 6], [1, 2, 4, 5]]
    dependency_types = [5, 2, 1, 7]
    graph = DependencyGraph(dependencies_list, dependency_types)
    print("walking...")
    print(graph.walk())
    print("="*10)
