/*
 * thoth-adviser - Dependency Graph implementation in C++
 * Copyright(C) 2018 Fridolin Pokorny
 *
 * This program is free software: you can redistribute it and / or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#pragma once

#include <cstddef>
#include <vector>
#include <stack>
#include <utility>
#include <limits>

/*
 * The traversal stack item stores a tuple - already expanded nodes in the graph and nodes that should
 * be expanded during the graph traversal. If the latter is empty, the traversal is done.
 */
typedef std::pair<std::vector<unsigned> *, std::vector<unsigned> *> traversal_stack_item_t;
typedef std::stack<traversal_stack_item_t *> traversal_stack_t;

/*
 * Dependency graph for generating application stacks.
 */
class DependencyGraph {
  public:
    bool walk(void);
    DependencyGraph(unsigned * direct_dependencies, unsigned ** dependencies_list, unsigned * dependency_types, std::size_t size, int write_pipe_fd);
    ~DependencyGraph();
    static const unsigned STREAM_STOP;
    static const unsigned STREAM_DELIMITER;

  private:
    bool is_valid_state();
    bool is_final_state();
    void expand_state();
    void delete_item(traversal_stack_item_t *);
    traversal_stack_item_t * traversal_stack_toppop();

    unsigned * direct_dependencies;
    unsigned ** dependencies_list;
    unsigned * dependency_types;
    std::size_t size;
    int write_pipe_fd;
    traversal_stack_t traversal_stack;
};

/* Constructor for DependencyGraph.
 * It accepts a list of dependencies where each item on position i states index of dependency i.
 * For example given the list of dependencies:
 *   [
 *     [2, 3],
 *     [1, 6],
 *     ...
 *   ]
 *  means that package 0 (index 0) depends on packages on indexes 2 and 3. Package 1 (index 1) depends
 *  on packages on indexes 1 and 6.
 *
 * The second argument distinguishes package types - in Python ecosystem we can install one package with the
 * given name (there cannot occur two installations of numpy in one environment). As we work solely with numbers,
 * we need to somehow distinguish package types. The list accepted states on index i which type of package is
 * it - for example:
 *   [
 *     0,
 *     1,
 *     0,
 *     ...
 *   ]
 * Means package 0 and 2 (index 0 and 2) are of a same type (type 0 - e.g. numpy) so they cannot be installed at
 * the same time. Package 1 is of type 1, it can be installed with package 0 and 2 at the same time.
 */
DependencyGraph::DependencyGraph(unsigned * direct_dependencies, unsigned ** dependencies_list, unsigned * dependency_types, std::size_t size, int write_pipe_fd) {
    this->direct_dependencies = direct_dependencies;
    this->dependencies_list = dependencies_list;
    this->dependency_types = dependency_types;
    this->size = size;
    this->write_pipe_fd = write_pipe_fd;

    // TODO: expand the initial configuration
    // [[1, 2, 3], [2, 3, 4], [5, 6, 7]]
}

/*
 * Sugar for top() and a subsequent pop() call.
 */
traversal_stack_item_t * DependencyGraph::traversal_stack_toppop() {
    traversal_stack_item_t * item = this->traversal_stack.top();
    this->traversal_stack.pop();
    return item;
}

/*
 * Destructor.
 *
 * As the library owns creation of the last stack that is propagated back to Python module, it is responsible for deleting it.
 */
DependencyGraph::~DependencyGraph() {
    while (this->traversal_stack.size() > 0)
        this->delete_item(this->traversal_stack_toppop());
}

/*
 * Delete a stack item - free memory allocated. Pointer usage after this call is invalid.
 */
void DependencyGraph::delete_item(traversal_stack_item_t * item) {
    delete item->first;
    delete item->second;
    delete item;
}

/*
 * Check if the generated state during dependency graph traversal is a valid state (no package name clashes).
 */
bool DependencyGraph::is_final_state() {
    return this->traversal_stack.top()->second->size() == 0;
}

/*
 * Check if the state on top of the stack is a valid state and can be expanded.
 */
bool DependencyGraph::is_valid_state() {
    // TODO: implement
    //this->delete_item(this->traversal_stack_toppop());
    return false;
}

/*
 * Pop the first element on stack and expand its state. This function has to be run after is_valid_state check.
 */
void DependencyGraph::expand_state() {
    // TODO: implement
    //traversal_stack_item_t * item = this->traversal_stack_toppop();
    return;
}