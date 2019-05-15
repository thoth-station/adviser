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

#include <list>
#include <set>
#include <vector>
#include <cstdint>

/*
 * Forward for typedef.
 */
class StackItem;

// Type of a package.
typedef uint16_t package_type_t;
// A package.
typedef uint16_t package_t;

// A traversal stack - a list of
typedef std::list<StackItem *> traversal_stack_t;

/*
 * An item on stack representing state during dependency graph traversal.
 */
class StackItem {
  public:
    StackItem(std::vector <package_t> * to_expand) {
        this->to_expand = to_expand;
    }

    StackItem(StackItem * other) {
        this->expanded = other->expanded;
        this->expanded_types = other->expanded_types;
        this->to_expand = new std::vector<package_t>(*other->to_expand);
    }

    ~StackItem() {
        // to_expand should always hold a valid pointer.
        delete this->to_expand;
    }

    /*
     * Get packages for the stack. If to_expand is empty, this will return a list of all packages for a stack.
     */
    const std::set<package_t> * get_expanded() const {
        return &this->expanded;
    }

    const std::vector<package_t> * get_to_expand() const {
        return this->to_expand;
    }

    /*
     * Get number of packages that are about to be expanded (this grows/decreases over time during traversal).
     * If the value returned is zero, the traversal is done and expanded holds a list of all packages in the stack.
     */
    std::size_t to_expand_count() const {
        return this->to_expand->size();
    }

    /*
     * Retrieve a next package (dependency) to be expanded, the dependency is removed from to_expand queue.
     */
    package_t next_to_expand() {
        package_t result = this->to_expand->back();
        this->to_expand->pop_back();
        return result;
    }

    /*
     * Check if the given type of package was seen during traversal.
     */
    bool type_seen(package_type_t package_type) const {
        return this->expanded_types.find(package_type) != this->expanded_types.end();
    }

    /*
     * Mark the given package as expanded, also mark the package type seen.
     */
    void mark_package_expanded(package_t package, package_type_t package_type) {
        this->expanded_types.insert(package_type);
        this->expanded.insert(package);
    }

    /*
     * Add each item from a list of packages (vector) to the queue for expansion.
     */
    void add_to_expanded(const std::vector<package_t> * packages) {
        for (auto package: *packages)
            this->to_expand->push_back(package);
    }

  private:
    // Already visited nodes during dependency stack traversal.
    std::set<package_t> expanded;
    // Types that were seen during traversal (for validity checks done during traversal).
    std::set<package_type_t> expanded_types;
    // Nodes to be expanded, if empty the traversal is done and expanded holds the generated stack.
    std::vector<package_t> * to_expand;
};
