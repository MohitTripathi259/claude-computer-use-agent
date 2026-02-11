#!/usr/bin/env python3
"""
Test: Using S3 Skills Directly
Demonstrates that skills loaded from S3 are immediately available to Claude
without needing a separate MCP server.
"""

import sys
import os
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent / "orchestrator"))

from skill_loader import get_skill_loader

def test_s3_skills_direct():
    """Test that skills can be loaded and used directly from S3"""

    print("\n" + "="*60)
    print("TEST: S3 Skills Direct Usage")
    print("="*60 + "\n")

    # 1. Get skill loader
    print("Step 1: Initialize S3 Skill Loader")
    loader = get_skill_loader(
        s3_bucket="cerebricks-studio-agent-skills",
        s3_prefix="skills_phase3/"
    )
    print(f"  - S3 Location: s3://{loader.s3_bucket}/{loader.s3_prefix}")
    print(f"  - Cache Directory: {loader.cache_dir}")

    # 2. List available skills
    print("\nStep 2: Discover Available Skills in S3")
    try:
        skill_names = loader.get_available_skills()
        print(f"  - Found {len(skill_names)} skills:")
        for skill in skill_names:
            print(f"    * {skill}")
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  (This is expected if AWS credentials are not configured)")
        skill_names = []

    # 3. Pre-load skills into memory
    print("\nStep 3: Pre-load Skills into Memory")
    try:
        skills = loader.preload_skills(force_refresh=False)
        print(f"  - Loaded {len(skills)} skills into memory")

        for skill_name, skill_data in skills.items():
            print(f"\n  Skill: {skill_name}")
            print(f"    - Description: {skill_data.get('description', 'N/A')[:100]}...")
            print(f"    - Scripts: {list(skill_data.get('scripts', {}).keys())}")
            print(f"    - Config Schema: {'Yes' if skill_data.get('config_schema') else 'No'}")
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  (This is expected if AWS credentials are not configured or S3 is unavailable)")
        skills = {}

    # 4. Generate system prompt section
    print("\nStep 4: Generate System Prompt Section")
    prompt_section = loader.get_skills_prompt_section()

    if prompt_section:
        print(f"  - Generated prompt section: {len(prompt_section)} characters")
        print(f"\n  Preview (first 500 chars):")
        print("  " + "-"*56)
        print("  " + prompt_section[:500].replace("\n", "\n  "))
        print("  ...")
        print("  " + "-"*56)
    else:
        print("  - No skills loaded (empty prompt section)")

    # 5. Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Skills can be used directly: {'YES' if skills else 'NO (check AWS credentials)'}")
    print(f"Skills in system prompt: {'YES' if prompt_section else 'NO'}")
    print(f"Claude has full context: {'YES' if prompt_section else 'NO'}")
    print("\nHow it works:")
    print("  1. Skills are downloaded from S3 to local cache")
    print("  2. Skill content (md, schema, scripts) loaded into memory")
    print("  3. Full skill documentation injected into system prompt")
    print("  4. Claude sees skills in EVERY request automatically")
    print("  5. Claude can use skills by calling appropriate MCP tools")
    print("\nNo separate MCP server needed for skill usage!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_s3_skills_direct()
