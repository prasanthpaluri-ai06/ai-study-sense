import pytest
from httpx import AsyncClient
from ai.academic.syllabus_parser import SyllabusParser, SyllabusDocumentExtractor


def test_syllabus_parser_and_dependencies():
    sample_text = """
    MODULE 1: Linear Structures
    - Arrays and Dynamic Sizing
    - Singly Linked Lists
    - Doubly Linked Lists
    - Stack Implementation
    - Queue and Deque

    MODULE 2: Trees and Balanced Hierarchies
    - Tree terminology
    - Binary tree
    - Inorder traversal
    - Preorder traversal
    - Postorder traversal
    - BST: Binary Search Tree
    - BST insertion
    - BST deletion
    - AVL Trees
    - AVL rotations
    - Binary Heap and Priority Queues
    """

    modules = SyllabusParser.parse_syllabus(sample_text)
    assert len(modules) == 2
    assert "Linear Structures" in modules[0].name
    assert "Trees" in modules[1].name

    mod2 = modules[1]
    topic_titles = [t.title for t in mod2.topics]
    assert "Tree terminology" in topic_titles
    assert "Binary tree" in topic_titles
    assert "AVL rotations" in topic_titles

    # Verify conceptual sequence
    assert len(mod2.conceptual_chain) >= 8
    # Later topics should list prior topics as dependencies
    avl_topic = next((t for t in mod2.topics if "AVL" in t.title), None)
    assert avl_topic is not None
    assert len(avl_topic.conceptual_dependencies) > 0


@pytest.mark.asyncio
async def test_syllabus_roadmap_full_flow(client: AsyncClient):
    # 1. Register Student
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "syllabus_student",
            "email": "syl@university.edu",
            "full_name": "Syllabus Explorer",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Subject
    sub_res = await client.post(
        "/api/v1/academic/subjects",
        headers=headers,
        json={"name": "Data Structures & Algorithms", "code": "CS201", "color": "#5A6E52"},
    )
    assert sub_res.status_code == 201
    subject_id = sub_res.json()["id"]

    # 3. Upload Sample Syllabus
    sample_syllabus_text = """
    MODULE 1 — INTRODUCTION TO DATA STRUCTURES
    - Abstract Data Types
    - Space and Time Complexity Analysis
    - Asymptotic Notations: Big O, Big Omega, Big Theta

    MODULE 2 — TREES
    - Tree terminology
    - Binary tree
    - Inorder traversal
    - Preorder traversal
    - Postorder traversal
    - BST
    - BST insertion
    - BST deletion
    - AVL
    - AVL rotations
    - Heap
    """

    upload_res = await client.post(
        "/api/v1/syllabus/upload/text",
        headers=headers,
        json={
            "subject_id": subject_id,
            "title": "CS201 Spring Syllabus",
            "content_text": sample_syllabus_text,
        },
    )
    assert upload_res.status_code == 201
    roadmap = upload_res.json()
    assert roadmap["subject_id"] == subject_id
    assert len(roadmap["modules"]) == 2
    assert roadmap["total_topics"] >= 10
    assert roadmap["completed_topics"] == 0
    assert roadmap["overall_progress_percent"] == 0.0

    syllabus_id = roadmap["id"]

    # 4. Verify Module 2 contains the prompt's required topics
    mod2 = next((m for m in roadmap["modules"] if "TREES" in m["name"].upper()), None)
    assert mod2 is not None
    mod2_titles = [t["title"] for t in mod2["topics"]]
    assert "Tree terminology" in mod2_titles
    assert "BST" in mod2_titles or any("BST" in t for t in mod2_titles)
    assert "AVL" in mod2_titles or any("AVL" in t for t in mod2_titles)
    assert "Heap" in mod2_titles or any("Heap" in t for t in mod2_titles)

    # 5. Test Topic Status Transitions: Not Started -> In Progress -> Completed -> Needs Revision
    first_topic_id = mod2["topics"][0]["id"]

    # Status: In Progress
    p1_res = await client.patch(
        f"/api/v1/syllabus/topics/{first_topic_id}/status",
        headers=headers,
        json={"status": "In Progress", "notes": "Studying node degrees and leaf properties."},
    )
    assert p1_res.status_code == 200
    assert p1_res.json()["status"] == "In Progress"

    # Status: Completed
    p2_res = await client.patch(
        f"/api/v1/syllabus/topics/{first_topic_id}/status",
        headers=headers,
        json={"status": "Completed"},
    )
    assert p2_res.status_code == 200
    assert p2_res.json()["status"] == "Completed"
    assert p2_res.json()["is_completed"] is True

    # Status: Needs Revision
    p3_res = await client.patch(
        f"/api/v1/syllabus/topics/{first_topic_id}/status",
        headers=headers,
        json={"status": "Needs Revision", "notes": "Revisit edge cases before test."},
    )
    assert p3_res.status_code == 200
    assert p3_res.json()["status"] == "Needs Revision"

    # 6. Retrieve Updated Roadmap & Verify Progress Calculations
    get_res = await client.get(f"/api/v1/syllabus/{syllabus_id}", headers=headers)
    assert get_res.status_code == 200
    updated_roadmap = get_res.json()
    assert updated_roadmap["needs_revision_topics"] >= 1

    # 7. List All Roadmaps
    list_res = await client.get("/api/v1/syllabus/roadmaps", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


@pytest.mark.asyncio
async def test_syllabus_extract_preview_and_subject_registration(client: AsyncClient):
    # 1. Register Student
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "preview_student",
            "email": "preview@university.edu",
            "full_name": "Preview Tester",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test extract-preview with valid text
    valid_syllabus = """
    MODULE 1: Operating System Principles
    - Process Management
    - Process Scheduling Algorithms: FCFS, SJF, Round Robin
    - Inter-Process Communication
    
    MODULE 2: Memory Management
    - Paging and Segmentation
    - Virtual Memory and Page Replacement: FIFO, LRU, Optimal
    """

    prev_res = await client.post(
        "/api/v1/syllabus/extract-preview",
        headers=headers,
        data={"content_text": valid_syllabus},
    )
    assert prev_res.status_code == 200
    preview_data = prev_res.json()
    assert preview_data["modules_count"] == 2
    assert preview_data["topics_count"] >= 4
    assert preview_data["subtopics_count"] >= 5
    assert len(preview_data["modules"]) == 2

    # 3. Test extract-preview rejection on invalid/empty text
    bad_prev = await client.post(
        "/api/v1/syllabus/extract-preview",
        headers=headers,
        data={"content_text": "   "},
    )
    assert bad_prev.status_code == 400

    # 4. Register Subject with Syllabus using preview data
    create_payload = {
        "name": "Operating Systems",
        "code": "CS401",
        "semester": "Semester 4",
        "credits": 4.0,
        "color": "#4A6B82",
        "description": "Core systems course",
        "syllabus_title": "OS Spring Syllabus",
        "file_name": "os_syllabus.txt",
        "modules": preview_data["modules"],
    }

    sub_res = await client.post(
        "/api/v1/academic/subjects/with-syllabus",
        headers=headers,
        json=create_payload,
    )
    assert sub_res.status_code == 201
    created_sub = sub_res.json()
    assert created_sub["name"] == "Operating Systems"
    assert created_sub["has_syllabus"] is True
    assert created_sub["syllabus_id"] is not None
    assert created_sub["syllabus_total_topics"] == preview_data["topics_count"]
    assert created_sub["syllabus_completed_topics"] == 0
    assert created_sub["syllabus_progress_percent"] == 0.0

    # 5. Verify subject listing reflects syllabus info
    list_subs = await client.get("/api/v1/academic/subjects", headers=headers)
    assert list_subs.status_code == 200
    os_sub = next((s for s in list_subs.json() if s["id"] == created_sub["id"]), None)
    assert os_sub is not None
    assert os_sub["has_syllabus"] is True
    assert os_sub["syllabus_total_topics"] >= 4

    # 6. Mark a topic completed
    roadmaps_res = await client.get(f"/api/v1/syllabus/roadmaps?subject_id={created_sub['id']}", headers=headers)
    assert roadmaps_res.status_code == 200
    roadmap = roadmaps_res.json()[0]
    first_topic = roadmap["modules"][0]["topics"][0]

    patch_res = await client.patch(
        f"/api/v1/syllabus/topics/{first_topic['id']}/status",
        headers=headers,
        json={"status": "Completed"},
    )
    assert patch_res.status_code == 200

    # Verify updated subject listing reflects completed topic
    list_subs_after = await client.get("/api/v1/academic/subjects", headers=headers)
    os_sub_after = next((s for s in list_subs_after.json() if s["id"] == created_sub["id"]), None)
    assert os_sub_after["syllabus_completed_topics"] == 1
    assert os_sub_after["syllabus_progress_percent"] > 0

    # 7. Replace syllabus for this subject - verify matching topic progress is preserved!
    updated_syllabus_text = """
    MODULE 1: Operating System Principles (Revised)
    - Process Management
    - Multithreading and Concurrency
    - Deadlocks and Prevention
    
    MODULE 2: Memory Systems
    - Paging and Segmentation
    - Cache Memory Hierarchy
    """

    replace_res = await client.post(
        "/api/v1/syllabus/upload/text",
        headers=headers,
        json={
            "subject_id": created_sub["id"],
            "title": "OS Revised Syllabus",
            "content_text": updated_syllabus_text,
        },
    )
    assert replace_res.status_code == 201
    new_roadmap = replace_res.json()
    # Process Management was completed before, should remain completed!
    proc_topic = next(
        (t for m in new_roadmap["modules"] for t in m["topics"] if "Process Management" in t["title"]),
        None,
    )
    assert proc_topic is not None
    assert proc_topic["status"] == "Completed"
    assert proc_topic["is_completed"] is True
