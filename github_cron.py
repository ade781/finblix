import os
import time
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("github_cron")

def run_git():
    try:
        # Add all files
        subprocess.run(["git", "add", "."], check=True)
        # Commit with timestamp
        commit_msg = f"Auto-commit Finblix AI System Updates - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        res = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
        
        # If there's nothing to commit, it returns a non-zero code or says "nothing to commit"
        if "nothing to commit" in res.stdout:
            logger.info("No changes to commit.")
        else:
            # Push
            subprocess.run(["git", "push"], check=True)
            logger.info(f"Successfully pushed to GitHub: {commit_msg}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in git sync: {e}")

if __name__ == "__main__":
    logger.info("Starting Github Auto-Sync Daemon...")
    while True:
        run_git()
        # Sleep for 1 hour
        time.sleep(3600)
