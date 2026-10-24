"""
AI StudySense - Intelligent Topic-Aware Study Method Recommender
Synthesizes personalized execution protocols, practical exercises, expected outcomes,
and self-assessment questions specifically tailored to the user's input topic, learning objective,
and fatigue level across all five approved study methods:
1. Pomodoro Technique
2. 52/17 Deep Work
3. Active Recall
4. Spaced Repetition (SM-2)
5. Feynman Technique
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StudyMethodRecommendation(BaseModel):
    primary_method: str  # "Pomodoro", "52/17", "Active Recall", "Spaced Repetition", "Feynman Technique"
    secondary_method: Optional[str] = None
    topic_title: str
    learning_objective: str = "Deep Understanding"
    fatigue_level: str = "Normal"
    confidence_score: float  # 0 to 100
    why_recommended: str
    execution_protocol: List[str]
    estimated_duration_minutes: int
    scientific_rationale: str
    practical_exercises: List[str] = Field(default_factory=list)
    expected_outcomes: List[str] = Field(default_factory=list)
    self_assessment_questions: List[str] = Field(default_factory=list)


class StudyMethodRecommender:
    """
    Intelligently recommends the optimal study method among the five approved
    methods and constructs a rich, topic-specific step-by-step execution protocol.
    """

    METHODS = {
        "Pomodoro": {
            "name": "Pomodoro Technique",
            "default_time": 25,
            "description": "25-minute high-focus interval followed by a 5-minute restorative micro-break.",
            "rationale": "Prevents mental fatigue, defeats procrastination, and maintains cognitive stamina across structured focus intervals.",
        },
        "52/17": {
            "name": "52 / 17 Deep Work",
            "default_time": 52,
            "description": "52-minute immersive deep work block followed by 17 minutes of full cognitive disengagement.",
            "rationale": "Optimized for ultradian flow states in complex engineering, coding, proof derivations, and algorithmic problem solving.",
        },
        "Active Recall": {
            "name": "Active Recall",
            "default_time": 30,
            "description": "Direct memory retrieval practice using prompts, self-quizzing, and closed-book testing without passive notes.",
            "rationale": "Forces neural reconstruction during retrieval, boosting exam retention up to 50% compared to passive highlighting or re-reading.",
        },
        "Spaced Repetition": {
            "name": "Spaced Repetition (SM-2)",
            "default_time": 20,
            "description": "Mathematically scheduled interval reviews right before forgetting curves decay.",
            "rationale": "Applies the SuperMemo-2 (SM-2) decay curve to consolidate concepts into permanent long-term memory with minimal total time.",
        },
        "Feynman Technique": {
            "name": "Feynman Technique",
            "default_time": 35,
            "description": "4-stage guided simplification: Explain in simple terms, identify jargon/gaps, review sources, and craft intuitive analogies.",
            "rationale": "Uncovers hidden illusions of competence and builds foundational first-principles understanding.",
        },
    }

    @classmethod
    def _detect_topic_domain(cls, topic_clean: str) -> Dict[str, Any]:
        """Classifies topic into specific domain taxonomy and identifies key architectural sub-elements."""
        t_low = topic_clean.lower()

        # 1. Computer Science & Data Structures / Algorithms
        if any(kw in t_low for kw in ["tree", "bst", "avl", "red-black", "heap", "trie", "binary search"]):
            return {
                "domain": "cs_trees",
                "core_entity": "Hierarchical Data Structure / Tree Invariants",
                "sub_elements": ["node invariant (left < root <= right)", "pointer linking", "height balance", "in-order traversal"],
                "operations": ["lookup / search", "node insertion", "3-case deletion (leaf, 1 child, 2 children)", "balancing rotations"],
                "edge_cases": ["empty tree / null root", "degenerate / skewed linear chain", "duplicate keys", "single-node edge"],
            }
        elif any(kw in t_low for kw in ["graph", "bfs", "dfs", "dijkstra", "shortest path", "topological", "spanning tree", "kruskal", "prim", "bellman"]):
            return {
                "domain": "cs_graphs",
                "core_entity": "Graph Theory & Network Traversal",
                "sub_elements": ["adjacency list / matrix representation", "visited set / cycle detection", "edge weights", "priority queue state"],
                "operations": ["breadth-first / depth-first exploration", "relaxation step", "path reconstruction", "DAG ordering"],
                "edge_cases": ["disconnected components", "negative cycle", "isolated vertex", "dense vs sparse graphs"],
            }
        elif any(kw in t_low for kw in ["dynamic programming", "memoization", "knapsack", "lcs", "longest common", "fibonacci", "greedy", "backtrack", "divide and conquer"]):
            return {
                "domain": "cs_dp_algorithms",
                "core_entity": "Algorithmic Optimization & Recurrence Relations",
                "sub_elements": ["optimal substructure", "overlapping subproblems", "state definition DP[i][j]", "transition recurrence"],
                "operations": ["base case identification", "top-down memoized recursion", "bottom-up tabulation", "space optimization"],
                "edge_cases": ["zero capacity / empty base case", "negative values", "off-by-one indices", "boundary state"],
            }
        elif any(kw in t_low for kw in ["network", "tcp", "ip", "udp", "http", "socket", "osi", "routing", "congestion", "dns", "packet", "ethernet"]):
            return {
                "domain": "cs_networks",
                "core_entity": "Computer Networks & Protocol Architecture",
                "sub_elements": ["protocol headers / encapsulation", "3-way handshake", "sliding window / CWND", "acknowledgement flow"],
                "operations": ["slow start & AIMD congestion avoidance", "packet routing & forwarding", "error recovery (timeout vs 3 dup ACKs)", "socket binding"],
                "edge_cases": ["packet loss / jitter", "out-of-order delivery", "buffer overflow / dropped packets", "connection teardown FIN-ACK"],
            }
        elif any(kw in t_low for kw in ["os", "operating system", "process", "thread", "deadlock", "paging", "virtual memory", "semaphore", "mutex", "cpu scheduling"]):
            return {
                "domain": "cs_systems",
                "core_entity": "Operating Systems & Hardware-Software Interfaces",
                "sub_elements": ["context switching", "page tables / TLB", "critical section", "synchronization primitives"],
                "operations": ["virtual-to-physical address translation", "process state transitions", "deadlock Coffman condition verification", "page replacement (LRU/FIFO)"],
                "edge_cases": ["page faults & thrashing", "race conditions & deadlocks", "priority inversion", "starvation"],
            }
        elif any(kw in t_low for kw in ["sql", "database", "rdbms", "join", "normalization", "acid", "index", "b-tree", "transaction", "nosql"]):
            return {
                "domain": "cs_databases",
                "core_entity": "Relational & Distributed Database Systems",
                "sub_elements": ["relational schema", "primary / foreign keys", "B-tree indexing", "write-ahead logging"],
                "operations": ["INNER / LEFT / FULL OUTER join execution", "query optimization & EXPLAIN plan", "1NF to 3NF/BCNF normalization", "ACID transaction isolation"],
                "edge_cases": ["NULL handling in joins", "deadlocks in concurrent writes", "unindexed full-table scans", "dirty reads"],
            }

        # 2. Mathematics & Calculus & Statistics
        elif any(kw in t_low for kw in ["integration", "integral", "derivative", "calculus", "differential", "parts", "substitution", "taylor", "fourier", "limit"]):
            return {
                "domain": "math_calculus",
                "core_entity": "Mathematical Calculus & Analysis",
                "sub_elements": ["fundamental theorem of calculus", "LIATE selection hierarchy", "differentials du and dv", "antiderivative family + C"],
                "operations": ["integration by parts formula uv - int(v du)", "chain / product rule inversion", "cyclic equation algebraic solving", "definite limit evaluation"],
                "edge_cases": ["discontinuous bounds", "indeterminate forms 0/0", "divergent integrals", "sign alternation errors"],
            }
        elif any(kw in t_low for kw in ["matrix", "linear algebra", "eigen", "vector space", "determinant", "rank", "nullspace", "svd", "orthogonal"]):
            return {
                "domain": "math_linear_algebra",
                "core_entity": "Linear Algebra & Vector Transformations",
                "sub_elements": ["matrix linear transformation", "characteristic equation det(A - lambda I) = 0", "basis and dimension", "orthonormality"],
                "operations": ["Gaussian elimination / row echelon", "eigenvalue & eigenvector computation", "matrix diagonalization", "projection onto subspace"],
                "edge_cases": ["singular / non-invertible matrix (det=0)", "repeated eigenvalues with defective eigenspace", "zero vector trivial solutions", "dimension mismatch"],
            }
        elif any(kw in t_low for kw in ["probability", "bayes", "random variable", "distribution", "variance", "hypothesis", "regression", "p-value", "poisson"]):
            return {
                "domain": "math_probability",
                "core_entity": "Probability Theory & Statistical Inference",
                "sub_elements": ["sample space and events", "prior and posterior probability", "probability density function (PDF)", "expected value E[X]"],
                "operations": ["Bayes' theorem calculation", "conditional probability conditioning", "hypothesis test z/t-score calculation", "confidence interval estimation"],
                "edge_cases": ["independent vs mutually exclusive events", "zero prior probability", "type I vs type II errors", "skewed non-normal distributions"],
            }

        # 3. Physics & Physical Sciences
        elif any(kw in t_low for kw in ["physics", "thermodynamics", "entropy", "maxwell", "quantum", "electromagnetism", "newton", "mechanics", "optics", "relativity"]):
            return {
                "domain": "physics_science",
                "core_entity": "Physical Laws & Phenomenological Modeling",
                "sub_elements": ["conservation laws (energy, momentum)", "governing vector equations", "boundary & initial conditions", "state variables (P, V, T, E)"],
                "operations": ["free-body diagram formulation", "thermodynamic cycle / efficiency derivation", "differential field equation solving", "dimensional unit consistency check"],
                "edge_cases": ["frictionless ideal vs real dissipation", "relativistic velocity limits", "adiabatic vs isothermal limits", "singularity / boundary conditions"],
            }

        # 4. Life & Biological Sciences
        elif any(kw in t_low for kw in ["dna", "rna", "protein", "cell", "mitosis", "photosynthesis", "respiration", "enzyme", "genetics", "neuron", "immune", "biology"]):
            return {
                "domain": "bio_science",
                "core_entity": "Biological Systems & Molecular Pathways",
                "sub_elements": ["molecular substrates and enzymes", "cellular membrane & organelles", "chemical reaction pathways", "feedback loops"],
                "operations": ["phase-by-phase biochemical pathway tracing", "energy / ATP accounting", "transcription & translation mechanics", "regulatory inhibition & activation"],
                "edge_cases": ["mutation / replication errors", "denaturation under temperature/pH shifts", "competitive vs non-competitive inhibition", "pathway bottlenecks"],
            }

        # 5. Chemistry & Chemical Engineering
        elif any(kw in t_low for kw in ["chemistry", "organic", "reaction", "acid", "base", "kinetics", "equilibrium", "orbital", "covalent", "synthesis", "stoichiometry"]):
            return {
                "domain": "chemistry_science",
                "core_entity": "Chemical Structure & Reaction Dynamics",
                "sub_elements": ["electron configuration & hybridization", "reaction mechanism & intermediates", "activation energy (Ea)", "equilibrium constant (Keq)"],
                "operations": ["curly arrow electron pushing mechanism", "stoichiometric mole balancing", "Le Chatelier equilibrium shift prediction", "pH and buffer equation calculation"],
                "edge_cases": ["steric hindrance", "carbocation rearrangement", "limiting reactant depletion", "side product competition"],
            }

        # 6. Humanities, Business, History, Law
        elif any(kw in t_low for kw in ["history", "war", "revolution", "law", "contract", "economics", "market", "finance", "management", "constitution", "governance", "psychology"]):
            return {
                "domain": "humanities_social",
                "core_entity": "Socio-Historical & Analytical Systems",
                "sub_elements": ["historical context & stakeholder motivations", "structural causes and catalytic triggers", "legal precedents & doctrine", "economic incentives"],
                "operations": ["chronological timeline & causal chain mapping", "primary source / doctrine argument analysis", "comparative synthesis of perspectives", "long-term outcome & policy evaluation"],
                "edge_cases": ["conflicting historical testimonies", "statutory exceptions & caveats", "market externalities & unintended consequences", "counterfactual scenarios"],
            }

        # 7. General Academic Topic
        else:
            return {
                "domain": "general_academic",
                "core_entity": f"Core Concept & Theoretical Principles of {topic_clean}",
                "sub_elements": ["underlying definitions and fundamental axioms", "constituent components and relationships", "standard operational workflow", "practical application"],
                "operations": ["first-principles derivation", "structured process breakdown", "application to representative examples", "validation against criteria"],
                "edge_cases": ["boundary conditions", "common conceptual misconceptions", "exceptions to standard rules", "scalability / complexity constraints"],
            }

    @classmethod
    def _generate_topic_steps(
        cls,
        method: str,
        topic: str,
        domain_info: Dict[str, Any],
        objective: str,
        fatigue: str,
    ) -> List[str]:
        """Constructs detailed, numbered, topic-specific execution steps."""
        sub = domain_info["sub_elements"]
        ops = domain_info["operations"]
        edges = domain_info["edge_cases"]

        if method == "Pomodoro":
            # 25-minute structured sprints tailored specifically to the topic
            if fatigue.lower() in ["tired", "high", "fatigued"]:
                sprint1_time = "20m"
                break_time = "5m"
            else:
                sprint1_time = "25m"
                break_time = "5m"

            return [
                (
                    f"Sprint 1 ({sprint1_time} - {topic} Foundations & Architecture): "
                    f"Read and diagram the {domain_info['core_entity']}. Map out the key components: {sub[0]} and {sub[1]}. "
                    f"Write down the governing invariants and core definitions on paper without distractions."
                ),
                (
                    f"Sprint 2 ({sprint1_time} - Step-by-Step {topic} Mechanics & Operations): "
                    f"Trace the primary operations of {topic}: {ops[0]} and {ops[1]}. "
                    f"Manually step through a concrete numerical/code walkthrough line by line to observe how the internal state evolves."
                ),
                (
                    f"Sprint 3 ({sprint1_time} - Advanced Scenarios & Problem Solving): "
                    f"Solve at least 2 representative problems or implement the core algorithm for {topic}. "
                    f"Practice handling {ops[2] if len(ops) > 2 else ops[0]}, verifying time/space complexity and intermediate states."
                ),
                (
                    f"Sprint 4 ({sprint1_time} - Edge Cases & Synthesis): "
                    f"Stress-test your solution against critical edge cases: {edges[0]} and {edges[1]}. "
                    f"Complete a quick 5-minute closed-book recap summarizing the golden rules of {topic} before taking a 15-minute restorative rest."
                ),
            ]

        elif method == "52/17":
            # 52-minute uninterrupted deep flow session
            return [
                (
                    f"Phase 1 (10 Mins - Environment & Mental Framing for {topic}): "
                    f"Eliminate all notifications. Open your scratchpad or IDE and write down the central objective for {topic}. "
                    f"Outline the theoretical framework: {sub[0]} and {sub[1]} to establish a clean cognitive blueprint."
                ),
                (
                    f"Phase 2 (30 Mins - Uninterrupted Deep Flow & Execution): "
                    f"Immerse deeply into {topic}. Implement or rigorously derive the primary mechanisms: {ops[0]} and {ops[1]}. "
                    f"Solve complex, multi-step problem sets without switching context, ensuring your mental model accounts for {ops[2] if len(ops) > 2 else ops[0]}."
                ),
                (
                    f"Phase 3 (12 Mins - Verification, Edge Cases & Synthesis): "
                    f"Validate your work by testing boundary constraints: {edges[0]} and {edges[1]}. "
                    f"Document key performance characteristics and trade-offs of {topic} on your summary sheet."
                ),
                (
                    "Phase 4 (17 Mins - Restorative Cognitive Reset): "
                    "Step away completely from all screens. Hydrate, walk, and rest your eyes to allow hippocampal consolidation to solidify the neural pathways."
                ),
            ]

        elif method == "Active Recall":
            # Prompt retrieval & closed-book self-testing
            return [
                (
                    f"Step 1 (Closed-Book Knowledge Extraction for {topic}): "
                    f"Without opening notes or textbooks, write down everything you remember about {topic} on a blank canvas. "
                    f"Specifically attempt to reconstruct: 1) The definition of {sub[0]}, 2) The exact process of {ops[0]}, and 3) Governing equations/syntax."
                ),
                (
                    f"Step 2 (Targeted Problem Solving & Retrieval Drill): "
                    f"Select 3 unseen practice problems on {topic}. Attempt to solve them under strict exam conditions (no reference aids). "
                    f"Focus specifically on executing {ops[1]} and resolving {ops[2] if len(ops) > 2 else ops[0]} from pure memory."
                ),
                (
                    f"Step 3 (Gap Identification & Solution Reveal): "
                    f"Reveal the reference solution and use a red pen to circle any missing steps, sign mistakes, or logical gaps in your derivation of {topic}. "
                    f"Directly cross-examine where your understanding failed on {edges[0]}."
                ),
                (
                    f"Step 4 (Immediate Immediate Retest on Failed Prompts): "
                    f"Turn away from the reference material and re-derive the failed parts of {topic} from scratch until you achieve 100% fluent, error-free recall."
                ),
            ]

        elif method == "Spaced Repetition":
            # SM-2 Flashcard creation & scheduled recall intervals
            return [
                (
                    f"Step 1 (Deconstruct {topic} into Atomic Cue Cards): "
                    f"Break {topic} down into 5 to 8 focused question-and-answer flashcards. Create cards covering: "
                    f"Card 1: Core invariant/definition of {sub[0]}. Card 2: Step-by-step algorithm/formula for {ops[0]}. Card 3: How to handle {edges[0]}."
                ),
                (
                    f"Step 2 (Active Queue Review & Self-Rating): "
                    f"Review the flashcards for {topic}. Read the front prompt, mentally retrieve the full answer before flipping, and self-rate your recall from 0 (blackout) to 5 (perfect instant recall)."
                ),
                (
                    f"Step 3 (SM-2 Interval Scheduling): "
                    f"Apply the SM-2 algorithm: Successful cards (quality >= 4) progress to Day 1 -> Day 6 -> Day 15 review intervals. Failed cards (quality < 3) reset to the daily queue."
                ),
                (
                    f"Step 4 (Interleaved Cross-Topic Consolidation): "
                    f"Mix {topic} cards with previous syllabus flashcards to prevent block-practice illusions and train contextual discrimination."
                ),
            ]

        elif method == "Feynman Technique":
            # 4-stage simplification & analogy creation
            return [
                (
                    f"Stage 1 (Teach {topic} to a 10-Year-Old): "
                    f"Take a blank sheet of paper and write a clear, intuitive explanation of {topic} as if you were teaching it to a smart middle-schooler. "
                    f"Explain why {topic} exists and how {ops[0]} works without hiding behind complex jargon."
                ),
                (
                    f"Stage 2 (Pinpoint Technical Jargon & Cognitive Gaps): "
                    f"Review your explanation. Circle any hand-waving assumptions, buzzwords, or complicated formulas (e.g. {sub[0]}). "
                    f"Notice exactly where your explanation becomes vague when describing {ops[1]}."
                ),
                (
                    f"Stage 3 (Targeted Reference Repair): "
                    f"Return directly to reference textbooks, documentation, or lecture notes. Re-learn only the specific gap identified in Stage 2 until you can explain it in simple everyday vocabulary."
                ),
                (
                    f"Stage 4 (Craft a Concrete Real-World Analogy): "
                    f"Create a memorable, physical analogy for {topic}. Compare {domain_info['core_entity']} to a real-world system (e.g. library indexing, traffic routing, water plumbing, or a mail distribution center). "
                    f"Test your analogy by explaining how it handles {edges[0]}."
                ),
            ]

        else:
            return [
                f"Step 1: Set up dedicated study block for {topic} and eliminate notifications.",
                f"Step 2: Read and deconstruct the core mechanisms: {sub[0]}.",
                f"Step 3: Solve representative exercises practicing {ops[0]}.",
                f"Step 4: Verify understanding against edge cases: {edges[0]}.",
            ]

    @classmethod
    def _generate_practical_exercises(cls, topic: str, domain_info: Dict[str, Any]) -> List[str]:
        """Generates 3 concrete, topic-specific practice exercises."""
        ops = domain_info["operations"]
        edges = domain_info["edge_cases"]

        return [
            f"Trace Exercise: Perform a manual trace of {ops[0]} on a sample problem/dataset for {topic}, writing out all intermediate variables.",
            f"Implementation / Application Challenge: Solve or implement {ops[1]} for {topic}, verifying that time and space constraints are respected.",
            f"Edge Case Diagnostic: Construct a challenging scenario involving {edges[0]} and prove that your solution correctly handles the boundary condition.",
        ]

    @classmethod
    def _generate_expected_outcomes(cls, topic: str, domain_info: Dict[str, Any]) -> List[str]:
        """Generates 3 concrete, measurable learning outcomes for the topic."""
        sub = domain_info["sub_elements"]
        ops = domain_info["operations"]

        return [
            f"Mastery of {topic} Foundations: Clear first-principles understanding of {sub[0]} and {sub[1]}.",
            f"Operational Fluency: Ability to execute and derive {ops[0]} and {ops[1]} rapidly without referring to notes.",
            f"Analytical Rigor: Capability to identify and debug edge cases, performance bottlenecks, and common exam pitfalls.",
        ]

    @classmethod
    def _generate_self_assessment_questions(cls, topic: str, domain_info: Dict[str, Any]) -> List[str]:
        """Generates 3 diagnostic questions to self-test before completing the session."""
        sub = domain_info["sub_elements"]
        ops = domain_info["operations"]
        edges = domain_info["edge_cases"]

        return [
            f"Conceptual Invariant: In your own words, what is the core invariant rule governing {sub[0]} in {topic}?",
            f"Procedural Breakdown: Can you walk through the exact steps required to execute {ops[0]} without consulting external notes?",
            f"Edge Case Analysis: What specific failure or performance degradation occurs in {topic} when encountering {edges[0]}, and how is it resolved?",
        ]

    @classmethod
    def recommend_method(
        cls,
        topic_title: str,
        student_score: Optional[float] = None,
        learning_objective: str = "Deep Understanding",
        fatigue_level: str = "Normal",
        topic_type: Optional[str] = None,
    ) -> StudyMethodRecommendation:
        clean_topic = topic_title.strip() if topic_title else "Core Concept"
        t_low = clean_topic.lower()
        obj_low = learning_objective.lower()
        fat_low = fatigue_level.lower()

        domain_info = cls._detect_topic_domain(clean_topic)

        # Decision Matrix based on Objective, Fatigue, Score, and Domain
        # 1. Low Score / High Conceptual Difficulty -> Feynman Technique
        if student_score is not None and student_score < 60.0:
            primary = "Feynman Technique"
            secondary = "Active Recall"
            confidence = 94.0
            why = (
                f"Your recent score on '{clean_topic}' was {student_score:.1f}%. "
                f"The Feynman Technique will systematically uncover where your conceptual model breaks down by forcing plain-language explanations of {domain_info['core_entity']}."
            )
            duration = 35

        # 2. Exam Prep / Rapid Retrieval -> Active Recall
        elif any(kw in obj_low for kw in ["exam", "rapid", "test", "quiz", "assessment"]):
            primary = "Active Recall"
            secondary = "Spaced Repetition"
            confidence = 93.0
            why = (
                f"Exam preparation for '{clean_topic}' requires active neural retrieval. "
                f"Practicing closed-book problem solving on {domain_info['core_entity']} increases exam recall by up to 50% compared to passive reading."
            )
            duration = 30

        # 3. Long-Term Retention / Syllabus Mastery -> Spaced Repetition (SM-2)
        elif any(kw in obj_low for kw in ["long-term", "retention", "semester", "memory", "permanent"]):
            primary = "Spaced Repetition"
            secondary = "Active Recall"
            confidence = 91.0
            why = (
                f"To retain '{clean_topic}' long after the semester ends, Spaced Repetition (SM-2) schedules flashcard reviews at the exact threshold before memory decay occurs."
            )
            duration = 20

        # 4. Heavy Problem Solving / Coding / Mathematics -> 52/17 Deep Work (unless fatigued)
        elif any(kw in obj_low for kw in ["problem solving", "coding", "flow", "practice", "derivation", "proof"]) or domain_info["domain"].startswith("cs_") or domain_info["domain"].startswith("math_"):
            if fat_low in ["tired", "high", "fatigued", "low energy"]:
                primary = "Pomodoro"
                secondary = "52/17"
                confidence = 88.0
                why = (
                    f"Although '{clean_topic}' involves complex problem solving, your current fatigue level suggests 25-minute Pomodoro sprints to prevent mental burnout while mastering {domain_info['core_entity']}."
                )
                duration = 25
            else:
                primary = "52/17"
                secondary = "Pomodoro"
                confidence = 95.0
                why = (
                    f"'{clean_topic}' involves deep analytical reasoning. "
                    f"A 52-minute uninterrupted deep work block lets you enter full cognitive flow to trace and implement {domain_info['core_entity']}."
                )
                duration = 52

        # 5. First Time Learning / Deep Understanding -> Feynman Technique or Pomodoro
        elif any(kw in obj_low for kw in ["first time", "deep understanding", "concept", "beginner"]):
            primary = "Feynman Technique"
            secondary = "Pomodoro"
            confidence = 92.0
            why = (
                f"When approaching '{clean_topic}' for deep foundational comprehension, the Feynman Technique ensures you grasp the underlying mechanisms before moving to rote practice."
            )
            duration = 35

        # 6. Default -> Pomodoro Technique
        else:
            primary = "Pomodoro"
            secondary = "Active Recall"
            confidence = 89.0
            why = (
                f"The Pomodoro Technique provides structured pacing and continuous momentum to systematically work through '{clean_topic}' without fatigue."
            )
            duration = 25

        # Generate topic-specific components
        protocol = cls._generate_topic_steps(
            method=primary,
            topic=clean_topic,
            domain_info=domain_info,
            objective=learning_objective,
            fatigue=fatigue_level,
        )

        exercises = cls._generate_practical_exercises(clean_topic, domain_info)
        outcomes = cls._generate_expected_outcomes(clean_topic, domain_info)
        questions = cls._generate_self_assessment_questions(clean_topic, domain_info)

        return StudyMethodRecommendation(
            primary_method=primary,
            secondary_method=secondary,
            topic_title=clean_topic,
            learning_objective=learning_objective,
            fatigue_level=fatigue_level,
            confidence_score=confidence,
            why_recommended=why,
            execution_protocol=protocol,
            estimated_duration_minutes=duration,
            scientific_rationale=cls.METHODS[primary]["rationale"],
            practical_exercises=exercises,
            expected_outcomes=outcomes,
            self_assessment_questions=questions,
        )
