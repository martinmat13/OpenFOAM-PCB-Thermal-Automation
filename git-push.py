import subprocess
import sys
import datetime


def run_git(args, check=True):
    """Run a Git command and return its result."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True
    )

    if check and result.returncode != 0:
        print(f"❌ Git command failed: {' '.join(args)}")
        print(result.stderr.strip() or result.stdout.strip())
        sys.exit(result.returncode)

    return result


def main():
    # 1. Check whether the current directory is inside a Git repository
    root = run_git(["rev-parse", "--show-toplevel"], check=False)

    if root.returncode != 0:
        print("❌ This folder is not a Git repository.")
        print("Run 'git init -b main' first, then try again.")
        sys.exit(1)

    print(f"📁 Repository: {root.stdout.strip()}")

    # 2. Detect the current branch
    branch_result = run_git(
        ["symbolic-ref", "--short", "HEAD"],
        check=False
    )

    if branch_result.returncode != 0:
        print("❌ No active branch found. Create or switch to a branch first.")
        sys.exit(1)

    branch = branch_result.stdout.strip()
    print(f"🌿 Branch: {branch}")

    # 3. Check whether the GitHub remote exists
    remote_result = run_git(
        ["remote", "get-url", "origin"],
        check=False
    )

    if remote_result.returncode != 0:
        print("\n🔗 No GitHub repository is configured.")
        repo_url = input(
            "Paste your GitHub repository URL: "
        ).strip()

        if not repo_url:
            print("❌ Repository URL cannot be empty.")
            sys.exit(1)

        # Add the remote to this repository
        run_git(["remote", "add", "origin", repo_url])
        print("✅ GitHub repository saved!")
    else:
        print(f"☁️ Remote: {remote_result.stdout.strip()}")

    # 4. Get the commit message
    if len(sys.argv) > 1:
        commit_message = " ".join(sys.argv[1:])
    else:
        now = datetime.datetime.now().astimezone().strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        )
        commit_message = f"Auto-update: {now}"

    # 5. Stage changes
    print("\n🚀 Staging files...")
    run_git(["add", "-A"])

    # 6. Commit changes
    print(f"📝 Commit message: {commit_message}")

    commit = run_git(
        ["commit", "-m", commit_message],
        check=False
    )

    if commit.returncode != 0:
        output = (commit.stdout + commit.stderr).lower()

        if (
            "nothing to commit" in output
            or "nothing added to commit" in output
        ):
            print("ℹ️ No new changes to commit.")
        else:
            print("❌ Commit failed:")
            print(commit.stderr.strip() or commit.stdout.strip())
            sys.exit(commit.returncode)
    else:
        print(commit.stdout.strip() or "✅ Commit successful.")

    # 7. Push the current branch to GitHub
    print(f"\n☁️ Pushing branch '{branch}' to GitHub...")

    push = run_git(
        ["push", "-u", "origin", branch],
        check=False
    )

    if push.returncode != 0:
        print("❌ Push failed:")
        print(push.stderr.strip() or push.stdout.strip())
        print("\nCheck your repository URL, authentication, and permissions.")
        sys.exit(push.returncode)

    print(push.stdout.strip() or "✅ Push successful!")
    print("\n🎉 Git sync complete!")


if __name__ == "__main__":
    main()
