# Publish and check the body

Use GitHub CLI when available and publication is authorized. Otherwise hand over the completed body file for the user's PR tool. Writing a description does not itself authorize opening a PR.

1. Save the filled template as a UTF-8 body file, for example `pr-body.md`, outside tracked project files. Use a file-writing tool or a quoted heredoc so backticks and shell substitutions remain literal. Copy the template contents without its outer fence.
2. Substitute the repository, base, branch, title, and body file in this command, then create a draft:

   ```bash
   gh pr create --draft --repo OWNER/REPO --base BASE --head BRANCH --title "TITLE" --body-file pr-body.md
   ```

   For an authorized update to an existing PR, use its number:

   ```bash
   gh pr edit N --repo OWNER/REPO --body-file pr-body.md
   ```

3. Fetch the stored body after creating or updating it:

   ```bash
   gh api repos/OWNER/REPO/pulls/N --jq .body
   ```

4. Compare it with the body file. Confirm the opener is first, `<details>` precedes `<summary>`, the summary names the actual writer's model and effort, a blank line follows `</summary>`, and another precedes `</details>`. Confirm all expanded sections survived. If the body differs, correct it with `gh pr edit` and fetch it again.
5. Hand over the PR link and verification result. Tell Will the opener is a draft for his approval or editing before merge; leave the PR's review state within the user's requested scope.
