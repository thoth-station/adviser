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

#include <algorithm>
#include <cassert>
#include <cstddef>
#include <map>
#include <set>
#include <stack>
#include <tuple>
#include <vector>

#include "stack_item.h"

/*
 * Dependency graph for generating application stacks.
 */
class DependencyGraph {
  public:
    DependencyGraph(
        package_t * direct_dependencies,
        std::size_t direct_dependencies_size,
        package_t ** dependencies_list,
        std::size_t dependencies_list_size,
        package_t * dependency_types,
        std::size_t size,
        int write_fd
    );
    ~DependencyGraph();
    bool walk();

    // Used to signalize there is no more stack to generate.
    static const package_t STREAM_STOP;
    // Delimiter used to delimit stacks in the stack stream written to write_fd.
    static const package_t STREAM_DELIMITER;

  private:
    bool is_final_state() const;
    void expand_state();
    void write_stack_item(const StackItem * stack_item) const;
    StackItem * traversal_stack_toppop();
    void expand_candidates(std::vector<std::vector<package_t> *> *, const package_t * dependencies, std::size_t packages_count);
    static void cartesian_product(std::vector<std::vector<package_t> *> *, const std::vector<std::vector<package_t>> &);

    // Mapping from a dependency to its direct dependencies allocated per dependency.
    std::vector<package_t> ** dependencies_mapping;

    // Types of direct dependencies.
    package_t * direct_dependencies;
    // Size of direct dependencies.
    std::size_t direct_dependencies_size;
    // Stating direct dependency for a dependency.
    package_t ** dependencies_list;
    // Size of dependencies_list as provided by callee.
    std::size_t dependencies_list_size;
    // Stating types of all the packages for resolution.
    package_type_t * dependency_types;
    // Number of all the packages for resolution (also stating size of dependency_types).
    std::size_t size;
    // Output file descriptor, e.g. pipe to write to.
    int write_fd;
    // Stack used during dependency graph traversal.
    traversal_stack_t traversal_stack;
};

/* Constructor for DependencyGraph.
 *
 * The very first argument is a list of integers representing package types of direct dependencies (see parameters
 * bellow). These package types state which packages (of what type) form direct dependencies.
 *
 * It accepts a list of dependencies as a seconds argument where each item is a tuple - (package, direct_dependency).
 * You can find this tuple being present for each package. For example given the list of dependencies:
 *   [
 *     [2, 3],
 *     [1, 6],
 *     ...
 *   ]
 *  means that package 2 (tuple on index 0) depends on package 3. Package 1 (tuple on index 1) depends on package 6.
 *
 * The third argument distinguishes package types - in Python ecosystem we can install one package with the
 * given name (there cannot occur two installations of numpy in one environment). As we work solely with numbers,
 * we need to somehow distinguish package types. The list accepted states on index i which type of package it
 * is - for example:
 *   [
 *     0,
 *     1,
 *     0,
 *     ...
 *   ]
 * Means package 0 and 2 (index 0 and 2) are of a same type (type 0 - e.g. numpy) so they cannot be installed at
 * the same time. Package 1 is of type 1, it can be installed with package 0 and 2 at the same time.
 *
 * Also note the dependency_types array states how many packages we are considering in total (equal to size).
 *
 * Stacks are written into write_fd file descriptor (can be any opened file descriptor, not just pipe) as
 * a stream of numbers. Each stack is delimited with STREAM_DELIMITER sign, the last stack generated
 * has a STREAM_STOP marker (after STREAM_DELIMITER).
 */
DependencyGraph::DependencyGraph(
        package_t * direct_dependencies,
        std::size_t direct_dependencies_size,
        package_t ** dependencies_list,
        std::size_t dependencies_list_size,
        package_type_t * dependency_types,
        std::size_t size,
        int write_fd
) {
    assert(write_fd > 0);
    this->direct_dependencies = direct_dependencies;
    this->direct_dependencies_size = direct_dependencies_size;
    this->dependencies_list = dependencies_list;
    this->dependencies_list_size = dependencies_list_size;
    this->dependency_types = dependency_types;
    this->size = size;
    this->write_fd = write_fd;

    // Mapping of a package to its dependencies.
    this->dependencies_mapping = new std::vector<package_t> * [this->size];
    for (std::size_t i = 0; i < this->size; i++)
        this->dependencies_mapping[i] = new std::vector<package_t>;
    for (std::size_t i = 0; i < this->dependencies_list_size; i++)
        this->dependencies_mapping[this->dependencies_list[i][0]]->push_back(this->dependencies_list[i][1]);

    // Expand the initial configuration and place all the initial nodes of the traversal graph onto stack.
    std::vector<std::vector<package_t> *> output_vector;
    this->expand_candidates(&output_vector, this->direct_dependencies, this->direct_dependencies_size);

    for (auto to_expand_item: output_vector) {
        StackItem * stack_item = new StackItem(to_expand_item);
        this->traversal_stack.push_front(stack_item);
    }
}

/*
 * Sugar for top() and a subsequent pop() call.
 */
StackItem * DependencyGraph::traversal_stack_toppop() {
    StackItem * stack_item = this->traversal_stack.front();
    this->traversal_stack.pop_front();
    return stack_item;
}

/*
 * Destructor.
 *
 * As the library owns creation of the stack which is propagated to Python module, it is responsible for deleting it.
 */
DependencyGraph::~DependencyGraph() {
    while (this->traversal_stack.size() > 0)
        delete this->traversal_stack_toppop();

    for (std::size_t i = 0; i < this->size; i++)
        delete this->dependencies_mapping[i];

    delete this->dependencies_mapping;
}

/*
 * Check if the generated state during dependency graph traversal is a final state (nothing to expand).
 */
bool DependencyGraph::is_final_state() const {
    return this->traversal_stack.front()->to_expand_count() == 0;
}

/*
 * Pop the first element on stack and expand its state. If the new state is not valid, the top item is discarded.
 */
void DependencyGraph::expand_state() {
    assert(! this->is_final_state());
    StackItem * stack_item = this->traversal_stack_toppop();

    auto to_expand = stack_item->next_to_expand();
    package_type_t to_expand_type = this->dependency_types[to_expand];
    auto expanded = stack_item->get_expanded();

    if (std::find(expanded->begin(), expanded->end(), to_expand) != expanded->end()) {
        // The given package was already introduced in the stack, continue without any additional changes.
        // The type has to be already present.:
        // Place it back for processing later on.
        this->traversal_stack.push_front(stack_item);
        return;
    }

    // We know the given package of the given type is not in the expanded, check seen types as we cannot
    // have packages of a same type.
    if (stack_item->type_seen(to_expand_type)) {
        // This is invalid state, give up.
        delete stack_item;
        return;
    }

    if (this->dependencies_mapping[to_expand]->size() == 0) {
        // There are no dependencies to process, mark the package as expanded and continue with the next one.
        stack_item->mark_package_expanded(to_expand, to_expand_type);
        this->traversal_stack.push_front(stack_item);
        return;
    }

    std::vector<std::vector<package_t> *> output_vector;
    this->expand_candidates(
        &output_vector,
        this->dependencies_mapping[to_expand]->data(),
        this->dependencies_mapping[to_expand]->size()
    );

    stack_item->mark_package_expanded(to_expand, to_expand_type);
    // We will reuse the structure of the last item not to perform delete and alloc twice unnecessarily.
    // This loop will be done at least once.
    for (auto it = output_vector.begin(); it != output_vector.end(); ++it) {
        StackItem * new_stack_item;
        if (it + 1 != output_vector.end())
            new_stack_item = new StackItem(stack_item);
        else
            // Reuse the existing stack item to avoid delete and alloc (see comment above).
            new_stack_item = stack_item;

        new_stack_item->add_to_expanded(*it);
        this->traversal_stack.push_front(new_stack_item);
    }
}

/*
 * Accept a list of packages (which are dependencies of a package - either direct or indirect) and get all the possible
 * expansions that will be placed onto stack.
 */
void DependencyGraph::expand_candidates(
        std::vector<std::vector<package_t> *> * output_vector,
        const package_t * dependencies,
        std::size_t packages_count
) {
    std::map<package_type_t, std::vector<package_t>> dependency_types_seen;
    for (std::size_t i = 0; i < packages_count; i++) {
        package_t dependency = dependencies[i];
        package_type_t dependency_type = this->dependency_types[dependency];
        dependency_types_seen[dependency_type].push_back(dependency);
    }

    std::vector<std::vector<package_t>> packages_vector;
    for (auto it: dependency_types_seen)
        packages_vector.push_back(it.second);

    this->cartesian_product(output_vector, packages_vector);
}

/*
 * Write the resulting stack into the output stack stream (file descriptor).
 */
void DependencyGraph::write_stack_item(const StackItem * stack_item) const {
    for (auto it = stack_item->get_expanded()->begin(); it != stack_item->get_expanded()->end(); ++it)
        write(this->write_fd, &(*it), sizeof(*it));

    // Add delimiter for the next stack produced or before stream end.
    write(this->write_fd, &(DependencyGraph::STREAM_DELIMITER), sizeof(DependencyGraph::STREAM_DELIMITER));
}
