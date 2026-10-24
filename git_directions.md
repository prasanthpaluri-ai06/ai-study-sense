# Complete Step-by-Step Guide: Pushing AI StudySense to a New Git Repository (`git_directions.md`)

Welcome! If this is your **first time using Git and GitHub**, do not worry. This guide is written specifically for beginners. It explains every single step clearly, why each command is needed, and how to avoid common first-timer mistakes.

---

## Table of Contents
1. [Key Concepts for Beginners: Git vs. GitHub](#1-key-concepts-for-beginners-git-vs-github)
2. [Prerequisites Checklist](#2-prerequisites-checklist)
3. [Important: Pre-Flight Check on `.gitignore`](#3-important-pre-flight-check-on-gitignore)
4. [Step 1: Create a New Repository on GitHub (Browser)](#step-1-create-a-new-repository-on-github-browser)
5. [Step 2: Open PowerShell in Your Project Folder](#step-2-open-powershell-in-your-project-folder)
6. [Step 3: Configure Your Git Identity (First-Time Setup)](#step-3-configure-your-git-identity-first-time-setup)
7. [Step 4: Initialize Git in Your Project (`git init`)](#step-4-initialize-git-in-your-project-git-init)
8. [Step 5: Set the Main Branch Name (`git branch -M main`)](#step-5-set-the-main-branch-name-git-branch--m-main)
9. [Step 6: Stage Your Project Files (`git add .`)](#step-6-stage-your-project-files-git-add-)
10. [Step 7: Create Your First Commit (`git commit`)](#step-7-create-your-first-commit-git-commit)
11. [Step 8: Link Local Project to GitHub (`git remote add origin`)](#step-8-link-local-project-to-github-git-remote-add-origin)
12. [Step 9: Push Your Code to GitHub (`git push -u origin main`)](#step-9-push-your-code-to-github-git-push--u-origin-main)
13. [Step 10: Verify on GitHub](#step-10-verify-on-github)
14. [Future Daily Workflow: How to Push Updates Later](#future-daily-workflow-how-to-push-updates-later)
15. [Troubleshooting & Common Beginner Errors](#troubleshooting--common-beginner-errors)

---

## 1. Key Concepts for Beginners: Git vs. GitHub

- **Git:** A program installed on your local computer that tracks changes to your files over time (like a time-machine for code).
- **GitHub:** A cloud-based website where you store a copy of your Git repository online so you can share it, back it up, or collaborate with others.
- **Repository (or "Repo"):** A folder tracked by Git containing all project files and their revision history.
- **Commit:** A snapshot/checkpoint of your project at a specific moment with a descriptive message.
- **Push:** Uploading your local commits from your laptop up to GitHub in the cloud.

---

## 2. Prerequisites Checklist

Before you start, make sure you have:
1. **GitHub Account:** If you don't have one, go to [https://github.com](https://github.com) and click **Sign Up** (it's completely free).
2. **Git Installed on Laptop:** Git is already installed on your system (`git version 2.55.0.windows.4`).

---

## 3. Important: Pre-Flight Check on `.gitignore`

When pushing a full-stack project, you should **never** upload:
- Virtual environments (`.venv/`, `venv/`) — these are huge folders with thousands of machine-specific binary files.
- `node_modules/` — the frontend dependencies folder (can be reinstalled anytime with `npm install`).
- Database files (`studysense.db`, `*.db`, `*.sqlite`) — these contain local test records.
- Secret files (`.env`) — these contain local passwords or secret keys.

Your project already has a `.gitignore` file configured in the root directory that automatically ignores these files. This ensures your repository remains fast, clean, and lightweight.

---

## Step 1: Create a New Repository on GitHub (Browser)

1. Open your web browser and log into [https://github.com](https://github.com).
2. In the top-right corner of the page, click the **`+`** icon (next to your profile picture) and select **New repository**.
   *(Alternatively, visit [https://github.com/new](https://github.com/new) directly).*
3. Fill in the repository details:
   - **Repository name:** `AI-StudySense` (or `Study_helper` or any name you prefer).
   - **Description:** *(Optional)* `AI StudySense — Intelligent Academic Companion & Ergonomic Focus Ecosystem`.
   - **Public or Private:** Choose **Public** (visible to everyone, great for college/portfolio) or **Private** (visible only to you).
   - > [!CRITICAL]
     > **DO NOT check any of these boxes:**
     > - [ ] **Add a README file** $\rightarrow$ Leave UNCHECKED!
     > - [ ] **Add .gitignore** $\rightarrow$ Leave UNCHECKED (None)!
     > - [ ] **Choose a license** $\rightarrow$ Leave UNCHECKED (None)!
     >
     > **Why?** You already have all these files locally on your laptop. If you let GitHub create an initial commit with a README, your local project and GitHub will have conflicting histories, causing a `rejected - non-fast-forward` error when pushing.
4. Click the green button: **Create repository**.
5. Keep this browser tab open! You will see a page showing your new repository's URL (e.g., `https://github.com/YOUR_USERNAME/AI-StudySense.git`).

---

## Step 2: Open PowerShell in Your Project Folder

1. Press `Win + X` on your keyboard and select **Terminal** or **Windows PowerShell**.
2. Make sure you are in your project folder. Type:
   ```powershell
   cd "C:\Users\palur\OneDrive\Desktop\Study_helper"
   ```
3. Verify that you are in the right folder by running:
   ```powershell
   Get-Location
   ```
   It should display: `C:\Users\palur\OneDrive\Desktop\Study_helper`.

---

## Step 3: Configure Your Git Identity (First-Time Setup)

If you have never used Git on your computer before, Git needs to know your name and email so it can label your commits.

Run these two commands in PowerShell (replace with your actual name and the email you used to sign up for GitHub):

```powershell
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

*Example:*
```powershell
git config --global user.name "Paluri"
git config --global user.email "paluri@example.com"
```

To verify that it was saved, run:
```powershell
git config --global --list
```
You should see your `user.name` and `user.email` listed.

---

## Step 4: Initialize Git in Your Project (`git init`)

Initialize Git in your project folder by running:

```powershell
git init
```

**Expected output:**
```text
Initialized empty Git repository in C:/Users/palur/OneDrive/Desktop/Study_helper/.git/
```

This creates a hidden `.git` folder in your project where Git keeps track of all file history.

---

## Step 5: Set the Main Branch Name (`git branch -M main`)

By default, older Git versions named the primary branch `master`. GitHub now uses `main` as the standard default branch.

Run this command to ensure your branch is named `main`:

```powershell
git branch -M main
```

---

## Step 6: Stage Your Project Files (`git add .`)

Now tell Git to prepare all files in the project for the initial commit:

```powershell
git add .
```

> **Note:** The period `.` means "add all files in the current folder, respecting `.gitignore`".
> This command takes about 5 to 10 seconds to process. It will not print anything if it succeeds.

You can verify what was staged by typing:
```powershell
git status
```
You will see a list of files highlighted in green (`new file: ...`), showing that your code, docs, and assets are staged and ready.

---

## Step 7: Create Your First Commit (`git commit`)

Now take the initial snapshot of your project with a descriptive commit message:

```powershell
git commit -m "Initial commit: AI StudySense full-stack project with hardware integration"
```

**Expected output:**
Git will print a list of files saved into this commit (e.g., `create mode 100644 backend/app/main.py`, etc.).

---

## Step 8: Link Local Project to GitHub (`git remote add origin`)

Now tell your local Git where your GitHub repository lives on the internet.

1. Go back to your browser tab on GitHub where you created the new repository.
2. Under the section **"…or push an existing repository from the command line"**, find the HTTPS URL. It looks like:
   `https://github.com/YOUR_USERNAME/REPO_NAME.git`
3. Copy that command or type it into PowerShell:
   ```powershell
   git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
   ```

*Real-World Example (replace `YOUR_USERNAME` and `AI-StudySense` with your actual GitHub username and repository name):*
```powershell
git remote add origin https://github.com/paluri/AI-StudySense.git
```

To verify the link was created successfully, run:
```powershell
git remote -v
```
**Expected output:**
```text
origin  https://github.com/YOUR_USERNAME/AI-StudySense.git (fetch)
origin  https://github.com/YOUR_USERNAME/AI-StudySense.git (push)
```

---

## Step 9: Push Your Code to GitHub (`git push -u origin main`)

Now upload your code to GitHub:

```powershell
git push -u origin main
```

> **What does `-u origin main` mean?**  
> `-u` sets the default upstream remote. After running this the first time, in the future you will only ever need to type `git push`!

### What happens when you run this command?
1. **GitHub Login Window:**  
   Windows will open a small pop-up window: **Git Credential Manager** asking you to authenticate.
   - Click **Sign in with your browser**.
   - Your browser will open GitHub asking to authorize Git Credential Manager. Click **Authorize**.
2. **Upload Progress:**  
   In your PowerShell window, you will see the upload progress:
   ```text
   Enumerating objects: 350, done.
   Counting objects: 100% (350/350), done.
   Delta compression using up to 8 threads
   Compressing objects: 100% (320/320), done.
   Writing objects: 100% (350/350), 12.50 MiB | 3.20 MiB/s, done.
   Total 350 (delta 45), reused 0 (delta 0), pack-reused 0
   To https://github.com/YOUR_USERNAME/AI-StudySense.git
    * [new branch]      main -> main
   branch 'main' set up to track 'origin/main'.
   ```

---

## Step 10: Verify on GitHub

1. Switch to your web browser and refresh your GitHub repository page.
2. You will now see your entire project uploaded with all files and folders cleanly structured:
   - `backend/`
   - `frontend/`
   - `hardware/`
   - `models/`
   - `working_study.md`
   - `abc_hrdwr.md`
   - `algo_use.md`
   - `README.md`
3. Congratulations! Your project is now safely backed up on GitHub!

---

## Summary of All Commands in One Place

For quick copy-pasting, here is the entire sequence from start to finish:

```powershell
# 1. Navigate to project directory
cd "C:\Users\palur\OneDrive\Desktop\Study_helper"

# 2. Configure Git identity (only needed once)
git config --global user.name "Your GitHub Name"
git config --global user.email "your_email@example.com"

# 3. Initialize Git repository
git init

# 4. Set branch name to main
git branch -M main

# 5. Stage all files
git add .

# 6. Commit staged files
git commit -m "Initial commit: AI StudySense full-stack project"

# 7. Add GitHub remote (replace with YOUR repo URL from GitHub)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git

# 8. Push files to GitHub
git push -u origin main
```

---

## Future Daily Workflow: How to Push Updates Later

Whenever you make changes, add features, or update documentation in the future, you do **NOT** repeat `git init` or `git remote add`.

Instead, just follow this simple 3-step routine:

```powershell
# Step 1: Check what has changed
git status

# Step 2: Stage all updated files
git add .

# Step 3: Commit with a brief note describing what you changed
git commit -m "Updated documentation and added new feature"

# Step 4: Push to GitHub!
git push
```

---

## Troubleshooting & Common Beginner Errors

### Issue 1: "fatal: remote origin already exists"
- **Cause:** You already ran `git remote add origin` previously.
- **Solution:** Check the existing URL:
  ```powershell
  git remote -v
  ```
  If you need to change it to a new URL, run:
  ```powershell
  git remote set-url origin https://github.com/YOUR_USERNAME/NEW_REPO.git
  ```

### Issue 2: "error: failed to push some refs to ... Updates were rejected"
- **Cause:** You checked the "Add a README" or "Add a license" checkbox on GitHub when creating the repository, so GitHub has commits that your computer does not have.
- **Solution:** Pull GitHub's initial commit and merge it before pushing:
  ```powershell
  git pull origin main --allow-unrelated-histories
  git push origin main
  ```

### Issue 3: Git prompts for a password in the terminal and rejects it
- **Cause:** GitHub stopped accepting account passwords in the terminal in 2021. You must use either the **browser login popup** (Git Credential Manager) or a **Personal Access Token (PAT)**.
- **Solution via Personal Access Token:**
  1. On GitHub, click your profile picture $\rightarrow$ **Settings** $\rightarrow$ **Developer settings** (bottom left) $\rightarrow$ **Personal access tokens** $\rightarrow$ **Tokens (classic)**.
  2. Click **Generate new token (classic)**.
  3. Give it a note (e.g., `Laptop-Git`), check the **`repo`** checkbox, and click **Generate token**.
  4. Copy the token (starts with `ghp_...`).
  5. When Git asks for your password in terminal, paste this token instead of your normal password.

### Issue 4: "fatal: not a git repository"
- **Cause:** You ran a git command in the wrong folder.
- **Solution:** Make sure PowerShell is inside `C:\Users\palur\OneDrive\Desktop\Study_helper` before running git commands.
