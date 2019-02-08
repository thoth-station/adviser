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

namespace Thoth {
    class DependencyGraph {
      public:
        int walk(void);
        //DependencyGraph(unsigned **dependencies_list, unsigned *dependency_types);

      private:
        unsigned **dependencies_list;
        unsigned *dependency_types;
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
     * we need to somehow distingush package types. The list accepted states on index i which type of package is
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
    //DependencyGraph::DependencyGraph(unsigned **dependencies_list, unsigned *dependency_types) {
    //    this->dependencies_list = dependencies_list;
    //    this->dependency_types = dependency_types;
    //}
}
