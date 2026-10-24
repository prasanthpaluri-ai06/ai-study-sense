import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QuickQuestion(BaseModel):
    question: str
    answer: str
    explanation: str


class RevisionPackage(BaseModel):
    topic_title: str
    category: str
    definition: str
    core_idea: str
    important_points: List[str]
    formulas_or_syntax: Optional[str] = None
    example: str
    common_mistakes: List[str]
    quick_questions: List[QuickQuestion]
    final_recap: str


class RevisionGenerator:
    """
    Generates structured, high-yield revision packages for any syllabus topic.
    Includes formal definitions, core mechanisms, formulas, pitfalls, quick questions, and recap.
    """

    @classmethod
    def generate_revision(cls, topic_title: str) -> RevisionPackage:
        clean_topic = topic_title.strip()
        t_low = clean_topic.lower()

        # Generate topic-specific tailored revision content based on topic patterns
        if "binary search" in t_low and "tree" not in t_low:
            return RevisionPackage(
                topic_title=clean_topic,
                category="Searching Algorithms / Divide & Conquer",
                definition="Binary Search is an efficient interval-halving search algorithm that locates the position of a target key within a monotonically ordered (sorted) sequence in logarithmic time.",
                core_idea="Compare the target value with the middle element of the array. If they match, return the index; otherwise, discard the half in which the target cannot possibly lie, repeating on the remaining subarray.",
                important_points=[
                    "Precondition Requirement: The input dataset MUST be sorted beforehand.",
                    "Time Invariant: The search window [low, high] strictly shrinks by at least half on every iteration.",
                    "Optimal Space: Iterative binary search achieves O(1) auxiliary space.",
                    "Applicable to Monotonic Functions: Can also be used to find roots or minimize cost functions over discrete domains.",
                ],
                formulas_or_syntax=(
                    "Midpoint Calculation: mid = low + (high - low) // 2 (prevents integer overflow)\n"
                    "Recurrence Relation: T(n) = T(n/2) + O(1) -> Master Theorem Case 2: O(log n)\n"
                    "Worst-case Comparisons: floor(log2(n)) + 1"
                ),
                example=(
                    "Array: [2, 5, 8, 12, 16, 23, 38, 56, 72, 91], Target: 23\n"
                    "Step 1: low=0, high=9 -> mid=4 (val=16). 23 > 16 -> search right (low=5, high=9)\n"
                    "Step 2: low=5, high=9 -> mid=7 (val=56). 23 < 56 -> search left (low=5, high=6)\n"
                    "Step 3: low=5, high=6 -> mid=5 (val=23). 23 == 23 -> Match found at index 5!"
                ),
                common_mistakes=[
                    "Using `(low + high) / 2` in typed languages (C++/Java) which causes integer overflow for large arrays.",
                    "Off-by-one errors in while loop condition (`while (low <= high)` vs `while (low < high)`).",
                    "Incorrect boundary update (using `low = mid` instead of `low = mid + 1`, causing an infinite loop).",
                    "Applying binary search to unsorted or dynamically mutating arrays without re-sorting.",
                ],
                quick_questions=[
                    QuickQuestion(
                        question="Why is `mid = low + (high - low) // 2` preferred over `(low + high) // 2`?",
                        answer="To prevent 32-bit signed integer overflow when low + high > 2^31 - 1.",
                        explanation="In languages with fixed integer sizes, adding two large positive indices can wrap into negative numbers, causing invalid memory indexing."
                    ),
                    QuickQuestion(
                        question="What is the worst-case number of comparisons for an array of 1,024 elements?",
                        answer="11 comparisons (log2(1024) + 1 = 10 + 1).",
                        explanation="Each iteration halves the remaining search range."
                    ),
                ],
                final_recap="Binary search achieves lightning-fast O(log n) searches on sorted data by continuously halving the candidate window. Always guard against integer overflow in midpoint calculation and ensure loop termination conditions."
            )

        elif "tree" in t_low or "bst" in t_low or "avl" in t_low:
            return RevisionPackage(
                topic_title=clean_topic,
                category="Hierarchical Data Structures",
                definition=f"{clean_topic} is a hierarchical node-based structure where each node contains a value and references to child subtrees, providing efficient sorted storage and associative queries.",
                core_idea="Organizes items in a non-linear hierarchy to balance quick sequential traversal with fast logarithmic insertion, deletion, and searching.",
                important_points=[
                    "BST Invariant: For any node X, all keys in left subtree < X.key < all keys in right subtree.",
                    "Inorder Traversal of a BST always yields keys in strictly ascending sorted order.",
                    "AVL Balance Factor: BF(node) = height(left) - height(right) must remain in {-1, 0, +1}.",
                    "Self-balancing rotations (LL, RR, LR, RL) restore O(log n) worst-case height guarantees.",
                ],
                formulas_or_syntax=(
                    "Balance Factor: BF(u) = Height(u.left) - Height(u.right)\n"
                    "Max nodes at depth d: 2^d\n"
                    "Max nodes in binary tree of height h: 2^(h+1) - 1\n"
                    "Height of balanced AVL tree: h < 1.44 * log2(n)"
                ),
                example=(
                    "Insert [10, 5, 15, 3, 7] into BST:\n"
                    "      10\n"
                    "     /  \\\n"
                    "    5    15\n"
                    "   / \\\n"
                    "  3   7\n"
                    "Inorder traversal: 3 -> 5 -> 7 -> 10 -> 15 (Sorted!)"
                ),
                common_mistakes=[
                    "Forgetting to update node heights during rotations in self-balancing trees.",
                    "Assuming standard BST guarantees O(log n) without self-balancing (can degenerate to O(n) linked list).",
                    "Off-by-one errors when deleting a node with two children (must replace with in-order successor or predecessor).",
                ],
                quick_questions=[
                    QuickQuestion(
                        question="Which tree traversal produces the elements of a BST in ascending order?",
                        answer="Inorder traversal (Left -> Root -> Right).",
                        explanation="Because left children are smaller and right children are greater than the current root."
                    ),
                    QuickQuestion(
                        question="When is a double rotation (e.g. Left-Right rotation) required in an AVL tree?",
                        answer="When an insertion is made into the right subtree of the left child (LR imbalance).",
                        explanation="A single rotation cannot fix a zigzag imbalance; we first rotate left on the child, then right on the node."
                    ),
                ],
                final_recap="Hierarchical tree structures provide O(log n) average performance when balanced. Memorize the BST property, tree traversals, and rotation rules for exams."
            )

        elif "graph" in t_low or "dijkstra" in t_low or "bfs" in t_low or "dfs" in t_low:
            return RevisionPackage(
                topic_title=clean_topic,
                category="Graph Theory & Network Traversal",
                definition=f"{clean_topic} is a foundational graph technique for exploring vertices and edges to solve connectivity, cycle detection, shortest path, and topological ordering problems.",
                core_idea="Systematically visits adjacent vertices using either frontier expansion (Queue in BFS) or deep branch exploration (Stack/Recursion in DFS).",
                important_points=[
                    "Graph Representation: Adjacency List (O(V+E) space, optimal for sparse graphs) vs Adjacency Matrix (O(V^2) space, optimal for dense graphs).",
                    "BFS finds the shortest path in unweighted graphs in O(V + E) time.",
                    "DFS is ideal for topological sorting, strongly connected components, and cycle detection.",
                    "Dijkstra's Algorithm finds single-source shortest paths on non-negative weighted graphs using a min-priority queue.",
                ],
                formulas_or_syntax=(
                    "BFS / DFS Time Complexity: O(V + E)\n"
                    "Dijkstra with Min-Heap: O((V + E) * log V)\n"
                    "Space Complexity: O(V) for visited tracking array and recursion/queue buffer"
                ),
                example=(
                    "BFS Traversal starting at Vertex A:\n"
                    "Queue: [A] -> Pop A, mark visited, Push neighbors [B, C]\n"
                    "Queue: [B, C] -> Pop B, Push [D]\n"
                    "Queue: [C, D] -> Pop C, Push [E]\n"
                    "Resulting Visit Order: A -> B -> C -> D -> E"
                ),
                common_mistakes=[
                    "Failing to track visited vertices, leading to infinite loops in cyclic graphs.",
                    "Applying Dijkstra's algorithm to graphs with negative edge weights (requires Bellman-Ford).",
                    "Using 1-based indexing on 0-based adjacency lists.",
                ],
                quick_questions=[
                    QuickQuestion(
                        question="Why can't Dijkstra's algorithm handle negative edge weights?",
                        answer="Because it greedily assumes once a vertex distance is finalized, no shorter path can be found later.",
                        explanation="A negative weight edge encountered later could invalidate previously finalized shortest distances."
                    ),
                    QuickQuestion(
                        question="Which data structure is used to implement Breadth-First Search (BFS)?",
                        answer="A FIFO Queue.",
                        explanation="A queue ensures level-by-level exploration outward from the starting vertex."
                    ),
                ],
                final_recap="Graphs model relationships between entities. Know when to use BFS (level-by-level / unweighted shortest path), DFS (backtracking / topological order), and Dijkstra (weighted shortest path)."
            )

        # General Academic Concept Generator
        return RevisionPackage(
            topic_title=clean_topic,
            category="Core Academic Curriculum",
            definition=f"{clean_topic} is a fundamental concept in the syllabus that establishes theoretical principles and practical analytical techniques for academic mastery.",
            core_idea=f"Deconstructs complex system interactions into structured components, governing laws, and repeatable procedures.",
            important_points=[
                f"Core Principle: Direct understanding of {clean_topic} is essential for prerequisite exam topics.",
                "Systematic Procedure: Follow step-by-step analytical verification rather than guessing.",
                "Boundary Conditions: Always evaluate asymptotic extremes and edge cases.",
                "Practical Application: Translates theoretical models into real-world solutions.",
            ],
            formulas_or_syntax=f"Key Analytical Metric: Efficiency / Accuracy = Output_Actual / Theoretical_Benchmark",
            example=f"Applying {clean_topic} to a standard textbook problem step-by-step: 1) Identify given parameters, 2) Apply governing equations, 3) Verify physical/mathematical consistency.",
            common_mistakes=[
                "Confusing foundational definitions with derived consequences.",
                "Overlooking prerequisite assumptions or boundary conditions.",
                "Failing to double-check units, signs, or boundary limits.",
            ],
            quick_questions=[
                QuickQuestion(
                    question=f"What is the primary governing principle of {clean_topic}?",
                    answer=f"To establish structural consistency, minimize error, and optimize system performance.",
                    explanation=f"Understanding the underlying mechanics of {clean_topic} enables robust problem solving across diverse scenarios."
                ),
                QuickQuestion(
                    question=f"What is the first step when analyzing a problem involving {clean_topic}?",
                    answer="Verify that all prerequisite conditions and boundary constraints are satisfied.",
                    explanation="Skipping constraint verification is the number one cause of calculation and reasoning errors."
                ),
            ],
            final_recap=f"Review the core definitions and invariants of {clean_topic}. Test yourself using the active recall questions and avoid common boundary mistakes."
        )
